from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .summary import build_run_summary


EVAL_SUITE_SCHEMA_ID = "https://schemas.nullstate.dev/eval-suite.schema.json"
EVAL_RESULTS_SCHEMA_ID = "https://schemas.nullstate.dev/eval-results.schema.json"
EVAL_SUITE_SCHEMA_VERSION = 1


def load_eval_suite(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid eval suite JSON in {path}: {error.msg} at line {error.lineno}, column {error.colno}.") from error
    except OSError as error:
        raise ValueError(f"Unable to read eval suite {path}: {error}") from error
    errors = validate_eval_suite(payload)
    if errors:
        raise ValueError("Invalid eval suite: " + "; ".join(errors))
    return payload


def validate_eval_suite(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["eval suite must be an object"]
    if payload.get("$schema") != EVAL_SUITE_SCHEMA_ID:
        errors.append("$schema must reference the nullstate eval-suite schema")
    if payload.get("schema_version") != EVAL_SUITE_SCHEMA_VERSION:
        errors.append(f"schema_version must be {EVAL_SUITE_SCHEMA_VERSION}")
    suite = payload.get("suite")
    if not isinstance(suite, dict):
        errors.append("suite must be an object")
        errors.append("suite.id is required")
    elif not isinstance(suite.get("id"), str) or not suite.get("id"):
        errors.append("suite.id is required")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("cases must include at least one case")
    elif case_errors := _validate_cases(cases):
        errors.extend(case_errors)
    return errors


def run_eval_suite(suite_path: Path, output_dir: Path) -> dict[str, Any]:
    suite = load_eval_suite(suite_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    cases = []
    suite_root = suite_path.resolve().parent.parent.parent if suite_path.resolve().parent.name == "eval" else Path.cwd()
    for case in suite["cases"]:
        cases.append(_run_eval_case(case, output_dir=output_dir, suite_root=suite_root))
    passed_count = sum(1 for case in cases if case["status"] == "passed")
    failed_count = len(cases) - passed_count
    results = {
        "$schema": EVAL_RESULTS_SCHEMA_ID,
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "suite": suite["suite"],
        "case_count": len(cases),
        "passed_count": passed_count,
        "failed_count": failed_count,
        "cases": cases,
        "totals": _totals(cases),
    }
    (output_dir / "eval-results.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_eval_report(results, output_dir)
    return results


def write_eval_report(results: dict[str, Any], output_dir: Path) -> Path:
    lines = [
        "# Nullstate Evaluation Report",
        "",
        f"Suite: `{results['suite']['id']}`",
        f"Cases: {results['case_count']}",
        f"Passed: {results['passed_count']}",
        f"Failed: {results['failed_count']}",
        "",
        "## Totals",
        "",
        f"- Duration seconds: {results['totals']['duration_seconds']}",
        f"- Findings: {results['totals']['finding_count']}",
        f"- Prompt tokens: {results['totals']['prompt_tokens']}",
        f"- Completion tokens: {results['totals']['completion_tokens']}",
        f"- Total tokens: {results['totals']['total_tokens']}",
        f"- Artifacts: {results['totals']['artifact_count']}",
        "",
        "## Baseline Comparison",
        "",
        f"- Cases with attack replay evidence: {results['totals']['comparison']['cases_with_runtime_attack_evidence']}",
        f"- Cases with remediation validation: {results['totals']['comparison']['cases_with_remediation_validation']}",
        f"- Artifact delta: {results['totals']['comparison']['artifact_delta']}",
        "",
        "## Cases",
        "",
    ]
    for case in results["cases"]:
        comparison = case["comparison"]
        lines.extend(
            [
                f"### {case['id']}",
                "",
                f"- Status: {case['status']}",
                f"- Baseline: {comparison['baseline_id']}",
                f"- Duration seconds: {case['duration_seconds']}",
                f"- Findings: {case['summary']['finding_count']}",
                f"- Highest severity: {case['summary']['highest_severity']}",
                f"- Attack before: {case['summary']['attack']['before']}",
                f"- Attack after: {case['summary']['attack']['after']}",
                f"- Artifacts: {case['metrics']['artifact_count']}",
                f"- Adds attack replay evidence: {comparison['adds_runtime_attack_evidence']}",
                f"- Adds remediation validation: {comparison['adds_remediation_validation']}",
                f"- Artifact delta: {comparison['artifact_delta']}",
                "",
            ]
        )
    report_path = output_dir / "eval-report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def _validate_cases(cases: list[Any]) -> list[str]:
    errors = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"cases[{index}] must be an object")
            continue
        for field_name in ("id", "terraform_dir"):
            if not isinstance(case.get(field_name), str) or not case.get(field_name):
                errors.append(f"cases[{index}].{field_name} is required")
        if not isinstance(case.get("expected"), dict):
            errors.append(f"cases[{index}].expected must be an object")
    return errors


def _run_eval_case(case: dict[str, Any], *, output_dir: Path, suite_root: Path) -> dict[str, Any]:
    case_dir = output_dir / str(case["id"])
    case_runs_dir = case_dir / "runs"
    case_dir.mkdir(parents=True, exist_ok=True)
    terraform_dir = Path(str(case["terraform_dir"]))
    if not terraform_dir.is_absolute():
        terraform_dir = suite_root / terraform_dir
    command = [
        sys.executable,
        "-m",
        "nullstate",
        "run",
        str(terraform_dir),
        "--runs-dir",
        str(case_runs_dir),
    ]
    if case.get("offline", True):
        command.append("--offline")
    if case.get("mock_agents", True):
        command.append("--mock-agents")
    if scenario := case.get("scenario"):
        command.extend(["--scenario", str(scenario)])
    if target := case.get("target"):
        command.extend(["--target", str(target)])
    started = time.perf_counter()
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    duration_seconds = round(time.perf_counter() - started, 3)
    run_dir = _latest_run_dir(case_runs_dir)
    summary = build_run_summary(run_dir) if run_dir is not None else _empty_summary(case_runs_dir)
    status = "passed" if completed.returncode == 0 and _matches_expectations(summary, case.get("expected") or {}) else "failed"
    metrics = {
        "artifact_count": len(summary.get("artifacts") or {}),
        "prompt_tokens": summary["tokens"]["prompt_tokens"],
        "completion_tokens": summary["tokens"]["completion_tokens"],
        "total_tokens": summary["tokens"]["total_tokens"],
    }
    return {
        "id": case["id"],
        "status": status,
        "duration_seconds": duration_seconds,
        "command": command,
        "returncode": completed.returncode,
        "stdout_path": _write_text(case_dir / "stdout.txt", completed.stdout),
        "stderr_path": _write_text(case_dir / "stderr.txt", completed.stderr),
        "run_dir": str(run_dir) if run_dir is not None else None,
        "summary": summary,
        "metrics": metrics,
        "comparison": _build_comparison(case.get("baseline") or {}, summary=summary, metrics=metrics),
        "expectations": case.get("expected") or {},
    }


def _latest_run_dir(runs_dir: Path) -> Path | None:
    if not runs_dir.is_dir():
        return None
    candidates = [path for path in runs_dir.iterdir() if path.is_dir()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _matches_expectations(summary: dict[str, Any], expected: dict[str, Any]) -> bool:
    if summary["finding_count"] < int(expected.get("min_findings", 0)):
        return False
    if expected.get("highest_severity") and summary.get("highest_severity") != expected["highest_severity"]:
        return False
    if expected.get("attack_before") and summary["attack"].get("before") != expected["attack_before"]:
        return False
    if expected.get("attack_after") and summary["attack"].get("after") != expected["attack_after"]:
        return False
    return True


def _empty_summary(path: Path) -> dict[str, Any]:
    return {
        "run": {"id": "missing", "path": str(path)},
        "status": "failed",
        "finding_count": 0,
        "highest_severity": None,
        "attack": {"before": None, "after": None},
        "tokens": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "artifacts": {},
        "limitations": ["run directory missing"],
    }


def _write_text(path: Path, value: str) -> str:
    path.write_text(value, encoding="utf-8")
    return str(path)


def _totals(cases: list[dict[str, Any]]) -> dict[str, Any]:
    comparison = {
        "cases_with_runtime_attack_evidence": sum(
            1 for case in cases if case["comparison"]["adds_runtime_attack_evidence"]
        ),
        "cases_with_remediation_validation": sum(
            1 for case in cases if case["comparison"]["adds_remediation_validation"]
        ),
        "cases_with_token_metrics": sum(1 for case in cases if case["comparison"]["adds_token_metrics"]),
        "artifact_delta": sum(int(case["comparison"]["artifact_delta"]) for case in cases),
    }
    return {
        "duration_seconds": round(sum(float(case["duration_seconds"]) for case in cases), 3),
        "finding_count": sum(int(case["summary"]["finding_count"]) for case in cases),
        "prompt_tokens": sum(int(case["metrics"]["prompt_tokens"]) for case in cases),
        "completion_tokens": sum(int(case["metrics"]["completion_tokens"]) for case in cases),
        "total_tokens": sum(int(case["metrics"]["total_tokens"]) for case in cases),
        "artifact_count": sum(int(case["metrics"]["artifact_count"]) for case in cases),
        "comparison": comparison,
    }


def _build_comparison(
    baseline: dict[str, Any],
    *,
    summary: dict[str, Any],
    metrics: dict[str, int],
) -> dict[str, Any]:
    baseline_id = str(baseline.get("id") or "unspecified-baseline")
    baseline_artifact_count = int(baseline.get("artifact_count") or 0)
    baseline_runtime_evidence = bool(baseline.get("runtime_attack_evidence"))
    baseline_remediation_validation = bool(baseline.get("remediation_validation"))
    baseline_token_metrics = bool(baseline.get("token_metrics"))
    has_attack_evidence = bool(summary.get("attack", {}).get("before"))
    has_remediation_validation = bool(summary.get("attack", {}).get("after"))
    has_token_metrics = int(metrics.get("total_tokens") or 0) > 0
    advantages = []
    if has_attack_evidence and not baseline_runtime_evidence:
        advantages.append("attack replay evidence")
    if has_remediation_validation and not baseline_remediation_validation:
        advantages.append("post-remediation validation")
    if has_token_metrics and not baseline_token_metrics:
        advantages.append("model token metrics")
    if int(metrics["artifact_count"]) > baseline_artifact_count:
        advantages.append("structured artifact coverage")
    return {
        "baseline_id": baseline_id,
        "baseline_description": baseline.get("description"),
        "baseline_finding_count": int(baseline.get("finding_count") or 0),
        "baseline_highest_severity": baseline.get("highest_severity"),
        "baseline_artifact_count": baseline_artifact_count,
        "nullstate_finding_count": int(summary.get("finding_count") or 0),
        "nullstate_highest_severity": summary.get("highest_severity"),
        "nullstate_artifact_count": int(metrics["artifact_count"]),
        "artifact_delta": int(metrics["artifact_count"]) - baseline_artifact_count,
        "adds_runtime_attack_evidence": has_attack_evidence and not baseline_runtime_evidence,
        "adds_remediation_validation": has_remediation_validation and not baseline_remediation_validation,
        "adds_token_metrics": has_token_metrics and not baseline_token_metrics,
        "advantages": advantages,
    }
