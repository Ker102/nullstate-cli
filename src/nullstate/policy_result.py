from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .baseline import load_baseline_identities, split_known_and_new_findings
from .ci import CI_FAILURE_EXIT_CODE, SEVERITY_RANKS, max_finding_severity, normalize_fail_on_severity
from .findings import Finding


POLICY_RESULT_FILENAME = "policy-result.json"


def write_policy_result(
    run_dir: Path,
    *,
    fail_on_severity: str,
    baseline_file: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    findings = _read_findings(run_dir / "findings.json")
    baseline_identities = load_baseline_identities(baseline_file)
    known_findings, new_findings = split_known_and_new_findings(findings, baseline_identities)
    evaluated_findings = new_findings if baseline_file is not None else findings
    threshold = normalize_fail_on_severity(fail_on_severity)
    max_severity = max_finding_severity(evaluated_findings)
    failed = threshold != "none" and SEVERITY_RANKS[max_severity] >= SEVERITY_RANKS[threshold]
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "run_id": run_dir.name,
        "failed": failed,
        "exit_code": CI_FAILURE_EXIT_CODE if failed else 0,
        "fail_on_severity": threshold,
        "max_severity": max_severity,
        "finding_count": len(findings),
        "evaluated_finding_count": len(evaluated_findings),
        "baseline": {
            "path": str(baseline_file) if baseline_file is not None else None,
            "known_finding_count": len(known_findings),
            "new_finding_count": len(evaluated_findings),
            "new_findings": [finding.to_dict() for finding in evaluated_findings],
        },
        "findings": [finding.to_dict() for finding in findings],
    }
    target = output_path or run_dir / POLICY_RESULT_FILENAME
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _read_findings(path: Path) -> list[Finding]:
    if not path.is_file():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return []
    findings = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        findings.append(
            Finding(
                rule_id=str(item.get("rule_id") or ""),
                severity=str(item.get("severity") or "low"),
                resource_address=str(item.get("resource_address") or ""),
                summary=str(item.get("summary") or ""),
                evidence=str(item.get("evidence") or ""),
                remediation=str(item.get("remediation") or ""),
            )
        )
    return findings
