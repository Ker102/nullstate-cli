from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__


BUNDLE_SCHEMA_VERSION = 1
BUNDLE_SCHEMA_ID = "https://schemas.nullstate.dev/run-bundle.schema.json"
BUNDLE_FILENAME = "run-bundle.json"


def write_run_bundle(run_dir: Path) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    if not (run_dir / "report.md").is_file():
        raise ValueError(f"Run directory does not contain report.md: {run_dir}")

    bundle = build_run_bundle(run_dir)
    errors = validate_run_bundle(bundle)
    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"Invalid run bundle: {joined}")
    bundle_path = run_dir / BUNDLE_FILENAME
    bundle_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return bundle


def build_run_bundle(run_dir: Path) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    events = _read_events(run_dir / "events.jsonl")
    findings = _read_json(run_dir / "findings.json", default=[])
    metrics = _read_json(run_dir / "metrics.json", default={})
    report = _read_text(run_dir / "report.md")
    manifest = _read_json(run_dir / "attack-manifest.json", default={})
    remediation = _read_json(run_dir / "remediation.json", default={})

    bundle = {
        "$schema": BUNDLE_SCHEMA_ID,
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "product": "nullstate",
        "product_version": __version__,
        "generated_at": datetime.now(UTC).isoformat(),
        "run": {
            "id": run_dir.name,
            "path": str(run_dir),
            "scenario": manifest.get("scenario") or _event_data(events, "start", "scenario"),
            "target": manifest.get("backend") or _event_data(events, "start", "target"),
            "offline": _event_data(events, "start", "offline"),
            "finding_count": len(findings) if isinstance(findings, list) else 0,
            "verdict": _verdict_from_report(report),
        },
        "evidence": {
            "findings": findings,
            "events": events,
            "metrics": metrics,
            "attack_manifest": manifest,
            "remediation": remediation,
            "report_excerpt": report[:4000],
        },
        "artifacts": _artifact_inventory(run_dir),
        "scrub": {
            "status": "not_performed",
            "workspace_included": False,
            "notes": "Bundle references local artifacts and excludes workspace/ and Terraform state by default.",
        },
        "cloud": {
            "upload_ready": True,
            "requires_token": True,
            "intended_endpoint": "Nullstate Cloud run ingestion API",
        },
    }
    return bundle


def validate_run_bundle(bundle: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(bundle, dict):
        return ["bundle must be an object"]

    if bundle.get("$schema") != BUNDLE_SCHEMA_ID:
        errors.append("$schema must reference the nullstate run-bundle schema")
    if bundle.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        errors.append(f"schema_version must be {BUNDLE_SCHEMA_VERSION}")
    if bundle.get("product") != "nullstate":
        errors.append("product must be nullstate")

    run = bundle.get("run")
    if not isinstance(run, dict):
        errors.append("run must be an object")
        errors.append("run.id is required")
    else:
        if not run.get("id"):
            errors.append("run.id is required")
        if "finding_count" in run and not isinstance(run.get("finding_count"), int):
            errors.append("run.finding_count must be an integer")
        if "verdict" in run and run.get("verdict") not in {"blocked", "failed", "unknown"}:
            errors.append("run.verdict must be blocked, failed, or unknown")

    evidence = bundle.get("evidence")
    if not isinstance(evidence, dict):
        errors.append("evidence must be an object")
        errors.append("evidence.findings must be a list")
    else:
        if not isinstance(evidence.get("findings"), list):
            errors.append("evidence.findings must be a list")
        if not isinstance(evidence.get("events"), list):
            errors.append("evidence.events must be a list")
        if not isinstance(evidence.get("metrics"), dict):
            errors.append("evidence.metrics must be an object")

    artifacts = bundle.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("artifacts must be a list")
    else:
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                errors.append(f"artifacts[{index}] must be an object")
                continue
            if not artifact.get("path"):
                errors.append(f"artifacts[{index}].path is required")
            if not artifact.get("sha256"):
                errors.append(f"artifacts[{index}].sha256 is required")
            if not isinstance(artifact.get("size_bytes"), int):
                errors.append(f"artifacts[{index}].size_bytes must be an integer")

    if not isinstance(bundle.get("scrub"), dict):
        errors.append("scrub must be an object")
    if not isinstance(bundle.get("cloud"), dict):
        errors.append("cloud must be an object")

    return errors


def _artifact_inventory(run_dir: Path) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    excluded_dirs = {"workspace", ".terraform", "__pycache__"}
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file():
            continue
        if any(part in excluded_dirs for part in path.relative_to(run_dir).parts):
            continue
        relative = path.relative_to(run_dir).as_posix()
        artifacts.append(
            {
                "path": relative,
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return artifacts


def _read_events(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        events.append(json.loads(line))
    return events


def _read_json(path: Path, *, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _event_data(events: list[dict[str, Any]], phase: str, key: str) -> Any:
    for event in events:
        if event.get("phase") == phase:
            data = event.get("data") or {}
            if isinstance(data, dict):
                return data.get(key)
    return None


def _verdict_from_report(report: str) -> str:
    if "Exploit blocked after remediation" in report:
        return "blocked"
    if "Exploit still succeeds" in report:
        return "failed"
    return "unknown"
