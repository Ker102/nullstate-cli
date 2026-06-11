from __future__ import annotations

from typing import Any

from .findings import Finding


CI_SUMMARY_FILENAME = "ci-summary.json"
CI_FAILURE_EXIT_CODE = 2
SEVERITY_RANKS = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def build_ci_summary(
    *,
    run_id: str,
    findings: list[Finding],
    remaining_findings: list[Finding],
    fail_on_severity: str,
    before_attack: dict[str, str],
    after_attack: dict[str, str],
) -> dict[str, Any]:
    threshold = normalize_fail_on_severity(fail_on_severity)
    max_severity = max_finding_severity(findings)
    failed = threshold != "none" and SEVERITY_RANKS[max_severity] >= SEVERITY_RANKS[threshold]
    return {
        "schema_version": 1,
        "run_id": run_id,
        "failed": failed,
        "exit_code": CI_FAILURE_EXIT_CODE if failed else 0,
        "fail_on_severity": threshold,
        "max_severity": max_severity,
        "finding_count": len(findings),
        "remaining_finding_count": len(remaining_findings),
        "verdict": "blocked" if after_attack.get("status") == "blocked" else "unresolved",
        "before_attack_status": before_attack.get("status", "unknown"),
        "after_attack_status": after_attack.get("status", "unknown"),
        "findings": [finding.to_dict() for finding in findings],
    }


def normalize_fail_on_severity(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in SEVERITY_RANKS:
        known = ", ".join(SEVERITY_RANKS)
        raise ValueError(f"Unsupported fail-on severity {value!r}. Supported values: {known}")
    return normalized


def max_finding_severity(findings: list[Finding]) -> str:
    if not findings:
        return "none"
    severities = [normalize_finding_severity(finding.severity) for finding in findings]
    return max(severities, key=lambda severity: SEVERITY_RANKS[severity])


def normalize_finding_severity(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in SEVERITY_RANKS and normalized != "none":
        return normalized
    return "low"
