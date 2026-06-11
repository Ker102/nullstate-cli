from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__


SARIF_FILENAME = "nullstate.sarif"
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"


def write_sarif(run_dir: Path, output_path: Path | None = None) -> dict[str, Any]:
    payload = build_sarif(run_dir)
    target = output_path or run_dir / SARIF_FILENAME
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def build_sarif(run_dir: Path) -> dict[str, Any]:
    findings = _read_findings(run_dir / "findings.json")
    rules = _rules_from_findings(findings)
    results = [_result_from_finding(finding) for finding in findings]
    return {
        "$schema": SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "nullstate",
                        "informationUri": "https://github.com/Ker102/nullstate-cli",
                        "semanticVersion": __version__,
                        "rules": rules,
                    }
                },
                "results": results,
                "properties": {
                    "generated_at": datetime.now(UTC).isoformat(),
                    "run_id": run_dir.name,
                },
            }
        ],
    }


def _read_findings(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return []
    return [finding for finding in raw if isinstance(finding, dict)]


def _rules_from_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    rules: list[dict[str, Any]] = []
    for finding in findings:
        rule_id = str(finding.get("rule_id") or "NULLSTATE_FINDING")
        if rule_id in seen:
            continue
        seen.add(rule_id)
        rules.append(
            {
                "id": rule_id,
                "name": rule_id,
                "shortDescription": {"text": str(finding.get("summary") or rule_id)},
                "fullDescription": {"text": str(finding.get("evidence") or finding.get("summary") or rule_id)},
                "help": {"text": str(finding.get("remediation") or "Review and remediate this finding.")},
                "properties": {
                    "severity": str(finding.get("severity") or "warning").lower(),
                    "precision": "high",
                },
            }
        )
    return rules


def _result_from_finding(finding: dict[str, Any]) -> dict[str, Any]:
    rule_id = str(finding.get("rule_id") or "NULLSTATE_FINDING")
    resource_address = str(finding.get("resource_address") or "unknown")
    summary = str(finding.get("summary") or rule_id)
    evidence = str(finding.get("evidence") or "")
    text = summary if not evidence else f"{summary} Evidence: {evidence}"
    return {
        "ruleId": rule_id,
        "level": _level_for_severity(str(finding.get("severity") or "")),
        "message": {"text": text},
        "logicalLocations": [
            {
                "name": resource_address,
                "fullyQualifiedName": resource_address,
                "kind": "resource",
            }
        ],
        "properties": {
            "severity": str(finding.get("severity") or "warning").lower(),
            "evidence": evidence,
            "remediation": str(finding.get("remediation") or ""),
        },
    }


def _level_for_severity(severity: str) -> str:
    normalized = severity.lower()
    if normalized in {"critical", "high"}:
        return "error"
    if normalized == "medium":
        return "warning"
    if normalized == "low":
        return "note"
    return "warning"
