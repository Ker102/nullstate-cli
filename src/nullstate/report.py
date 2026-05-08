from __future__ import annotations

from .findings import Finding


def render_report(
    *,
    run_id: str,
    terraform_dir: str,
    findings: list[Finding],
    before_attack: dict[str, str],
    after_attack: dict[str, str],
    patch_diff: str,
    model_notes: str,
) -> str:
    verdict = "Exploit blocked after remediation" if after_attack.get("status") == "blocked" else "Exploit still succeeds"
    finding_rows = "\n".join(_render_finding(finding) for finding in findings) or "No findings."
    diff = patch_diff.strip() or "No Terraform changes were required."

    return f"""# nullstate Run Report

Run ID: `{run_id}`

IaC input: `{terraform_dir}`

## Verdict

{verdict}

## Findings

{finding_rows}

## Red Team Before Remediation

- Status: `{before_attack.get("status", "unknown")}`
- Evidence: {before_attack.get("detail", "No detail recorded.")}

## Blue Team Remediation

{model_notes}

```diff
{diff}
```

## Red Team After Remediation

- Status: `{after_attack.get("status", "unknown")}`
- Evidence: {after_attack.get("detail", "No detail recorded.")}

## Case Study Notes

nullstate used deterministic IaC analysis for reliability, then layered red-team and blue-team agents over the evidence trail so the demo remains reproducible under hackathon time pressure.
"""


def _render_finding(finding: Finding) -> str:
    return (
        f"- `{finding.severity.upper()}` `{finding.rule_id}` on `{finding.resource_address}`: "
        f"{finding.summary} Evidence: {finding.evidence} Remediation: {finding.remediation}"
    )
