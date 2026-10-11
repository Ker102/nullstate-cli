from __future__ import annotations

import json
from pathlib import Path
from typing import Any


RUN_SUMMARY_SCHEMA_ID = "https://schemas.nullstate.dev/run-summary.schema.json"
RUN_SUMMARY_SCHEMA_VERSION = 1
SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def build_run_summary(run_dir: Path) -> dict[str, Any]:
    findings, finding_limitations = _read_findings(run_dir / "findings.json")
    event_statuses, scenario, event_limitations = _read_events_metadata(run_dir / "events.jsonl")
    tokens, token_limitations = _read_token_totals(run_dir / "metrics.json")
    artifacts, artifact_limitations = _artifact_paths(run_dir)
    highest_severity = _highest_severity(findings)
    status = _summary_status(findings, event_statuses)
    limitations = finding_limitations + event_limitations + token_limitations + artifact_limitations
    return {
        "$schema": RUN_SUMMARY_SCHEMA_ID,
        "schema_version": RUN_SUMMARY_SCHEMA_VERSION,
        "run": {
            "id": run_dir.name,
            "path": str(run_dir),
        },
        "scenario": scenario,
        "status": status,
        "finding_count": len(findings),
        "highest_severity": highest_severity,
        "attack": {
            "before": event_statuses.get("before"),
            "after": event_statuses.get("after"),
        },
        "remediation_available": (run_dir / "remediation.patch").is_file(),
        "artifacts": artifacts,
        "tokens": tokens,
        "limitations": limitations,
    }


def validate_run_summary(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["run summary must be an object"]
    if payload.get("$schema") != RUN_SUMMARY_SCHEMA_ID:
        errors.append("$schema must reference the nullstate run-summary schema")
    if payload.get("schema_version") != RUN_SUMMARY_SCHEMA_VERSION:
        errors.append(f"schema_version must be {RUN_SUMMARY_SCHEMA_VERSION}")
    run = payload.get("run")
    if not isinstance(run, dict):
        errors.append("run must be an object")
        errors.append("run.id is required")
    elif not isinstance(run.get("id"), str) or not run.get("id"):
        errors.append("run.id is required")
    if not isinstance(payload.get("status"), str) or not payload.get("status"):
        errors.append("status is required")
    scenario = payload.get("scenario")
    if not isinstance(scenario, dict):
        errors.append("scenario must be an object")
    elif scenario.get("name") is not None and not isinstance(scenario.get("name"), str):
        errors.append("scenario.name must be a string or null")
    if not isinstance(payload.get("finding_count"), int):
        errors.append("finding_count must be an integer")
    if not isinstance(payload.get("artifacts"), dict):
        errors.append("artifacts must be an object")
    tokens = payload.get("tokens")
    if tokens is not None and not isinstance(tokens, dict):
        errors.append("tokens must be an object")
    limitations = payload.get("limitations")
    if limitations is not None and not isinstance(limitations, list):
        errors.append("limitations must be a list")
    return errors


def _read_findings(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.is_file():
        return [], ["findings.json missing"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [], ["findings.json malformed"]
    if not isinstance(payload, list):
        return [], ["findings.json is not a list"]
    findings = [finding for finding in payload if isinstance(finding, dict)]
    if len(findings) != len(payload):
        return findings, ["findings.json contains non-object entries"]
    return findings, []


def _read_events_metadata(path: Path) -> tuple[dict[str, str | None], dict[str, str | None], list[str]]:
    statuses: dict[str, str | None] = {"before": None, "after": None}
    scenario: dict[str, str | None] = {
        "name": None,
        "evidence_level": None,
        "evidence_summary": None,
    }
    if not path.is_file():
        return statuses, scenario, ["events.jsonl missing"]
    limitations = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            limitations.append("events.jsonl contains malformed JSON")
            continue
        phase = event.get("phase")
        data = event.get("data") or {}
        if phase == "start" and isinstance(data, dict):
            if isinstance(data.get("scenario"), str):
                scenario["name"] = data["scenario"]
            if isinstance(data.get("scenario_evidence_level"), str):
                scenario["evidence_level"] = data["scenario_evidence_level"]
            if isinstance(data.get("scenario_evidence_summary"), str):
                scenario["evidence_summary"] = data["scenario_evidence_summary"]
        result = ((event.get("data") or {}).get("result") or {}) if isinstance(event.get("data"), dict) else {}
        status = result.get("status") if isinstance(result, dict) else None
        if isinstance(status, str) and phase == "red-team":
            statuses["before"] = status
        elif isinstance(status, str) and phase == "validation":
            statuses["after"] = status
    return statuses, scenario, limitations


def _read_token_totals(path: Path) -> tuple[dict[str, int], list[str]]:
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    if not path.is_file():
        return totals, ["metrics.json missing"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return totals, ["metrics.json malformed"]
    for call in payload.get("model_calls") or []:
        if not isinstance(call, dict):
            continue
        for key in totals:
            value = call.get(key)
            if isinstance(value, int):
                totals[key] += value
    return totals, []


def _artifact_paths(run_dir: Path) -> tuple[dict[str, str], list[str]]:
    known_artifacts = {
        "report": "report.md",
        "findings": "findings.json",
        "events": "events.jsonl",
        "metrics": "metrics.json",
        "remediation_patch": "remediation.patch",
        "bundle": "run-bundle.json",
        "sarif": "nullstate.sarif",
        "dashboard": "dashboard.html",
    }
    artifacts = {}
    limitations = []
    for name, filename in known_artifacts.items():
        path = run_dir / filename
        if path.is_file():
            artifacts[name] = str(path)
        elif filename in {"report.md", "events.jsonl", "metrics.json"}:
            limitations.append(f"{filename} missing")
    return artifacts, limitations


def _highest_severity(findings: list[dict[str, Any]]) -> str | None:
    severities = [str(finding.get("severity", "")).lower() for finding in findings]
    known = [severity for severity in severities if severity in SEVERITY_ORDER]
    if not known:
        return None
    return max(known, key=lambda severity: SEVERITY_ORDER[severity])


def _summary_status(findings: list[dict[str, Any]], event_statuses: dict[str, str | None]) -> str:
    if findings:
        return "failed"
    if event_statuses.get("before") in {"success", "inconclusive"} and event_statuses.get("after") is None:
        return "needs-review"
    return "passed"
