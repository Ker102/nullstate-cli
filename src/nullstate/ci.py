from __future__ import annotations

from typing import Any

from .findings import Finding


CI_SUMMARY_FILENAME = "ci-summary.json"
CI_SUMMARY_SCHEMA_ID = "https://schemas.nullstate.dev/ci-summary.schema.json"
CI_SUMMARY_SCHEMA_VERSION = 1
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
    baseline_path: str | None = None,
    known_findings: list[Finding] | None = None,
    new_findings: list[Finding] | None = None,
) -> dict[str, Any]:
    threshold = normalize_fail_on_severity(fail_on_severity)
    evaluated_findings = new_findings if new_findings is not None else findings
    max_severity = max_finding_severity(evaluated_findings)
    failed = threshold != "none" and SEVERITY_RANKS[max_severity] >= SEVERITY_RANKS[threshold]
    summary: dict[str, Any] = {
        "$schema": CI_SUMMARY_SCHEMA_ID,
        "schema_version": CI_SUMMARY_SCHEMA_VERSION,
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
        "baseline": {
            "path": baseline_path,
            "known_finding_count": len(known_findings or []),
            "new_finding_count": len(evaluated_findings),
            "new_findings": [finding.to_dict() for finding in evaluated_findings],
        },
    }
    errors = validate_ci_summary(summary)
    if errors:
        raise ValueError("Invalid CI summary: " + "; ".join(errors))
    return summary


def validate_ci_summary(summary: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(summary, dict):
        return ["ci summary must be an object"]

    if summary.get("$schema") != CI_SUMMARY_SCHEMA_ID:
        errors.append("$schema must reference the nullstate ci-summary schema")
    if summary.get("schema_version") != CI_SUMMARY_SCHEMA_VERSION:
        errors.append(f"schema_version must be {CI_SUMMARY_SCHEMA_VERSION}")

    run_id = summary.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        errors.append("run_id is required")

    if not isinstance(summary.get("failed"), bool):
        errors.append("failed must be a boolean")
    if not isinstance(summary.get("exit_code"), int):
        errors.append("exit_code must be an integer")

    fail_on_severity = summary.get("fail_on_severity")
    if not isinstance(fail_on_severity, str) or fail_on_severity not in SEVERITY_RANKS:
        errors.append("fail_on_severity must be a supported severity")

    max_severity = summary.get("max_severity")
    if not isinstance(max_severity, str) or max_severity not in SEVERITY_RANKS:
        errors.append("max_severity must be a supported severity")

    for field in ("finding_count", "remaining_finding_count"):
        value = summary.get(field)
        if not isinstance(value, int) or value < 0:
            errors.append(f"{field} must be a nonnegative integer")

    verdict = summary.get("verdict")
    if not isinstance(verdict, str) or not verdict.strip():
        errors.append("verdict is required")

    for field in ("before_attack_status", "after_attack_status"):
        value = summary.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} is required")

    if not isinstance(summary.get("findings"), list):
        errors.append("findings must be a list")

    baseline = summary.get("baseline")
    if not isinstance(baseline, dict):
        errors.append("baseline must be an object")
    else:
        for field in ("known_finding_count", "new_finding_count"):
            value = baseline.get(field)
            if not isinstance(value, int) or value < 0:
                errors.append(f"baseline.{field} must be a nonnegative integer")
        if not isinstance(baseline.get("new_findings"), list):
            errors.append("baseline.new_findings must be a list")

    return errors


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
