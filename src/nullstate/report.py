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
    runtime_evidence: dict[str, dict[str, object]] | None = None,
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

{_render_runtime_evidence(runtime_evidence)}

## Case Study Notes

nullstate used deterministic IaC analysis for reliability, then layered red-team and blue-team agents over the evidence trail so the demo remains reproducible under hackathon time pressure.
"""


def _render_finding(finding: Finding) -> str:
    return (
        f"- `{finding.severity.upper()}` `{finding.rule_id}` on `{finding.resource_address}`: "
        f"{finding.summary} Evidence: {finding.evidence} Remediation: {finding.remediation}"
    )


def _render_runtime_evidence(runtime_evidence: dict[str, dict[str, object]] | None) -> str:
    if not runtime_evidence:
        return ""
    before = runtime_evidence.get("before", {})
    after = runtime_evidence.get("after", {})
    return f"""## Runtime Command Evidence

### Before remediation

- Command: `{_command(before)}`
- Return code: `{before.get("returncode", "unknown")}`
- Target: `{before.get("target_url", "unknown")}`
- Classification: `{_runtime_classification(before)}`
- Stdout excerpt:

```text
{_excerpt(str(before.get("stdout", "")))}
```

### After remediation

- Command: `{_command(after)}`
- Return code: `{after.get("returncode", "unknown")}`
- Target: `{after.get("target_url", "unknown")}`
- Classification: `{_runtime_classification(after)}`
- Stdout excerpt:

```text
{_excerpt(str(after.get("stdout", "")))}
```
"""


def _command(payload: dict[str, object]) -> str:
    command = payload.get("command")
    if not isinstance(command, list):
        return "unknown"
    return " ".join(str(part) for part in command)


def _runtime_classification(payload: dict[str, object]) -> str:
    target_url = str(payload.get("target_url", ""))
    stdout = str(payload.get("stdout", "")).lower()
    if target_url.startswith("offline://") or "offline target selected" in stdout:
        return "offline deterministic simulation"
    if "runtime_exploit_observed=true" in stdout:
        return "runtime exploit observed"
    if "runtime_exploit_observed=false" in stdout:
        return "runtime probe did not observe exploit"
    if "runtime_probe_inconclusive=true" in stdout:
        return "runtime probe inconclusive"
    return "runtime evidence unavailable"


def _excerpt(value: str, limit: int = 1200) -> str:
    if len(value) <= limit:
        return value.strip() or "(empty)"
    return value[:limit].rstrip() + "\n... truncated ..."
