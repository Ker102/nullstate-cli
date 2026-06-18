from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .findings import Finding


BASELINE_SCHEMA_VERSION = 1
DEFAULT_BASELINE_FILENAME = "nullstate-baseline.json"


def write_baseline(run_dir: Path, output_path: Path) -> dict[str, Any]:
    findings = _read_findings(run_dir / "findings.json")
    payload = build_baseline(run_id=run_dir.name, findings=findings)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def build_baseline(*, run_id: str, findings: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_findings = []
    for finding in findings:
        rule_id = str(finding.get("rule_id") or "")
        resource_address = str(finding.get("resource_address") or "")
        baseline_findings.append(
            {
                "identity": finding_identity(rule_id=rule_id, resource_address=resource_address),
                "rule_id": rule_id,
                "resource_address": resource_address,
                "severity": str(finding.get("severity") or ""),
                "summary": str(finding.get("summary") or ""),
            }
        )
    return {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "run_id": run_id,
        "finding_count": len(baseline_findings),
        "findings": baseline_findings,
    }


def load_baseline_identities(path: Path | None) -> set[str]:
    if path is None:
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    findings = payload.get("findings") if isinstance(payload, dict) else []
    if not isinstance(findings, list):
        return set()
    identities = set()
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        identity = finding.get("identity")
        if identity:
            identities.add(str(identity))
            continue
        identities.add(
            finding_identity(
                rule_id=str(finding.get("rule_id") or ""),
                resource_address=str(finding.get("resource_address") or ""),
            )
        )
    return identities


def split_known_and_new_findings(
    findings: list[Finding],
    baseline_identities: set[str],
) -> tuple[list[Finding], list[Finding]]:
    if not baseline_identities:
        return [], findings
    known: list[Finding] = []
    new: list[Finding] = []
    for finding in findings:
        identity = finding_identity(rule_id=finding.rule_id, resource_address=finding.resource_address)
        if identity in baseline_identities:
            known.append(finding)
        else:
            new.append(finding)
    return known, new


def finding_identity(*, rule_id: str, resource_address: str) -> str:
    return f"{rule_id}|{resource_address}"


def _read_findings(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return []
    return [finding for finding in raw if isinstance(finding, dict)]
