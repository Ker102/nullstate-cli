from __future__ import annotations

from pathlib import Path
from typing import Any

from .policy import write_default_policy
from .scenarios import get_scenario


GITHUB_TEMPLATE_PATH = Path("docs/templates/github-actions/nullstate-enforcing.yml")


def render_github_workflow(
    *,
    scenario: str,
    iac_path: str,
    policy_file: str,
    baseline_file: str,
    fail_on_severity: str,
) -> str:
    template = GITHUB_TEMPLATE_PATH.read_text(encoding="utf-8")
    replacements = {
        "NULLSTATE_SCENARIO: aws-public-s3": f"NULLSTATE_SCENARIO: {scenario}",
        "NULLSTATE_IAC_PATH: examples/aws-public-s3": f"NULLSTATE_IAC_PATH: {iac_path}",
        "NULLSTATE_POLICY_FILE: nullstate-policy.json": f"NULLSTATE_POLICY_FILE: {policy_file}",
        "NULLSTATE_BASELINE_FILE: nullstate-baseline.json": f"NULLSTATE_BASELINE_FILE: {baseline_file}",
        "NULLSTATE_FAIL_ON_SEVERITY: high": f"NULLSTATE_FAIL_ON_SEVERITY: {fail_on_severity}",
    }
    rendered = template
    for old, new in replacements.items():
        rendered = rendered.replace(old, new)
    return rendered


def write_github_ci_files(
    *,
    workflow_path: Path,
    policy_path: Path,
    scenario: str,
    iac_path: str,
    fail_on_severity: str,
    baseline_file: str = "nullstate-baseline.json",
    force: bool = False,
) -> dict[str, Any]:
    if workflow_path.exists() and not force:
        raise FileExistsError(f"Workflow file already exists: {workflow_path}")
    if policy_path.exists() and not force:
        raise FileExistsError(f"Policy file already exists: {policy_path}")
    scenario_spec = get_scenario(scenario)
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(
        render_github_workflow(
            scenario=scenario,
            iac_path=iac_path,
            policy_file=str(policy_path),
            baseline_file=baseline_file,
            fail_on_severity=fail_on_severity,
        ),
        encoding="utf-8",
    )
    policy = write_default_policy(policy_path, scenario_name=scenario_spec.name, backend_name=scenario_spec.backend)
    return {
        "workflow_path": str(workflow_path),
        "policy_path": str(policy_path),
        "scenario": scenario,
        "iac_path": iac_path,
        "fail_on_severity": fail_on_severity,
        "policy_preset": policy["preset"],
    }
