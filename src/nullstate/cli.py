from __future__ import annotations

import os
import shutil
import subprocess
import time
import webbrowser
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .agents import LlmAgent
from .artifacts import EventLog, new_run_id, write_json
from .artifact_scrubber import scrub_run_artifacts
from .attack import simulate_attack, write_attack_script
from .attack_manifest import write_attack_manifest
from .attack_runner import run_attack_script
from .baseline import DEFAULT_BASELINE_FILENAME, load_baseline_identities, split_known_and_new_findings, write_baseline
from .bundle import BUNDLE_FILENAME, write_run_bundle
from .ci import CI_SUMMARY_FILENAME, build_ci_summary, normalize_fail_on_severity
from .dashboard import write_run_dashboard
from .demo import create_demo
from .evidence_manifest import EVIDENCE_MANIFEST_FILENAME, write_evidence_manifest
from .findings import find_scenario_findings
from .llm_providers import LlmEndpointConfig, normalize_provider, resolve_base_url
from .metrics import collect_run_metrics
from .policy import DEFAULT_POLICY_FILENAME, load_attack_policy, write_default_policy
from .policy_result import POLICY_RESULT_FILENAME, write_policy_result
from .remediation import remediate_scenario_files
from .report import render_report
from .sarif import SARIF_FILENAME, write_sarif
from .sandbox import get_backend, list_backends, probe_backend, render_commands, run_commands
from .scenario_detection import infer_scenario
from .scenarios import get_scenario, list_scenarios
from .terraform import apply_saved_plan, load_plan_json
from .upload import DEFAULT_UPLOAD_ENDPOINT, DEFAULT_UPLOAD_TOKEN_ENV, UPLOAD_PLAN_FILENAME, write_upload_plan


app = typer.Typer(
    invoke_without_command=True,
    no_args_is_help=False,
    help="Autonomous purple-teaming CLI for infrastructure-as-code sandboxes.",
)
sandbox_app = typer.Typer(no_args_is_help=True, help="Manage local sandbox backends.")
scenarios_app = typer.Typer(no_args_is_help=True, help="Inspect supported attack scenarios.")
policy_app = typer.Typer(no_args_is_help=True, help="Manage red-tool execution policies.")
app.add_typer(sandbox_app, name="sandbox")
app.add_typer(scenarios_app, name="scenarios")
app.add_typer(policy_app, name="policy")
console = Console()

BANNER = r"""
 _   _       _ _     _        _
| \ | |_   _| | |___| |_ __ _| |_ ___
|  \| | | | | | / __| __/ _` | __/ _ \
| |\  | |_| | | \__ \ || (_| | ||  __/
|_| \_|\__,_|_|_|___/\__\__,_|\__\___|
Nullstate
Autonomous Purple-Team Sandbox
"""


@app.callback()
def main(ctx: typer.Context) -> None:
    """Show the nullstate launch screen when no command is provided."""
    if ctx.invoked_subcommand is not None:
        return
    _print_banner()
    console.print(
        Panel(
            "\n".join(
                [
                    "Autonomous purple-team validation for IaC sandboxes.",
                    "",
                    "Workflow: start a sandbox, run a scenario, review the report, then clean up.",
                ]
            ),
            title="nullstate",
            border_style="cyan",
        )
    )
    _print_next_steps(
        [
            "nullstate status",
            "nullstate sandbox list",
            "nullstate sandbox up localstack-aws",
            "nullstate run examples/aws-public-s3 --target localstack-aws",
            "nullstate report",
        ]
    )


@app.command()
def doctor(offline: bool = typer.Option(False, "--offline", help="Skip network and external service checks.")) -> None:
    """Check local dependencies and configured model endpoint."""
    _print_banner()
    table = Table(title="nullstate doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")

    if offline:
        table.add_row("Offline mode", "ok", "External dependency checks skipped.")
    else:
        for binary in ["docker", "terraform", "az"]:
            found = shutil.which(binary)
            table.add_row(binary, "ok" if found else "missing", found or "not on PATH")
        table.add_row(
            "LLM endpoint",
            "configured" if _llm_configured() else "missing",
            "NULLSTATE_LLM_BASE_URL or role-specific red/blue endpoint variables",
        )

    console.print(table)


@app.command("init-demo")
def init_demo(
    name: str = typer.Argument(..., help="Demo name. Run `nullstate scenarios list` to see options."),
    output: Path = typer.Option(Path("examples/azure-public-blob"), "--output", "-o", help="Directory to create."),
) -> None:
    """Create an intentionally vulnerable IaC demo."""
    create_demo(name, output)
    console.print(f"Created demo at {output}")
    _print_next_steps(
        [
            f"nullstate run {output} --offline",
            "nullstate sandbox status localstack-azure",
        ]
    )


@app.command()
def status(
    sandbox: str = typer.Option("localstack-azure", "--sandbox", help="Sandbox backend to inspect."),
    runs_dir: Path = typer.Option(Path("runs"), "--runs-dir", help="Directory containing run artifacts."),
) -> None:
    """Show current workflow state and next useful commands."""
    _print_banner()
    try:
        backend = get_backend(sandbox)
    except KeyError as error:
        raise typer.BadParameter(str(error)) from error

    latest_run = _latest_report_path(runs_dir)
    env_file = _resolve_sandbox_env_file(None)
    table = Table(title="nullstate status")
    table.add_column("Check")
    table.add_column("State")
    table.add_column("Detail")
    table.add_row(
        "LLM endpoints",
        "configured" if _llm_configured() else "missing",
        _endpoint_status_detail(),
    )
    table.add_row(
        "LocalStack env",
        "file" if env_file else ("shell" if os.getenv("LOCALSTACK_AUTH_TOKEN") else "missing"),
        str(env_file) if env_file else "LOCALSTACK_AUTH_TOKEN from shell or .env/.env.local",
    )
    table.add_row("Sandbox", backend.name, backend.status)
    for probe in probe_backend(backend):
        table.add_row(probe.name, probe.status, probe.detail)
    table.add_row(
        "Latest run",
        latest_run.parent.name if latest_run else "none",
        str(latest_run.parent if latest_run else runs_dir),
    )
    console.print(table)
    _print_next_steps(
        [
            f"nullstate sandbox status {backend.name}",
            f"nullstate sandbox up {backend.name}",
            _example_run_command(backend.name),
            "nullstate report",
        ]
    )


@app.command()
def run(
    terraform_dir: Path = typer.Argument(..., exists=True, file_okay=False, help="Terraform directory to test."),
    target: str = typer.Option("auto", "--target", help="Execution target. Use auto to infer from the scenario."),
    scenario: str = typer.Option("auto", "--scenario", help="Attack scenario. Use auto to infer from IaC."),
    offline: bool = typer.Option(False, "--offline", help="Use static IaC parsing and skip Terraform/cloud runtime calls."),
    mock_agents: bool = typer.Option(False, "--mock-agents", help="Use deterministic mock red/blue agents even when an endpoint is configured."),
    runs_dir: Path = typer.Option(Path("runs"), "--runs-dir", help="Directory for run artifacts."),
    blue_model: str = typer.Option("gemma-4-31b-it", "--blue-model", help="Blue-team model name."),
    red_model: str = typer.Option("qwen3-coder-next", "--red-model", help="Red-team model name."),
    red_base_url: str | None = typer.Option(None, "--red-base-url", help="OpenAI-compatible endpoint for red-team agent."),
    blue_base_url: str | None = typer.Option(None, "--blue-base-url", help="OpenAI-compatible endpoint for blue-team agent."),
    llm_provider: str | None = typer.Option(
        None,
        "--llm-provider",
        help="Shared LLM provider preset: openai-compatible, google, claude, or custom.",
    ),
    red_provider: str | None = typer.Option(None, "--red-provider", help="Provider preset for the red-team agent."),
    blue_provider: str | None = typer.Option(None, "--blue-provider", help="Provider preset for the blue-team agent."),
    ci: bool = typer.Option(False, "--ci", help="Write CI summary and use severity-based exit codes."),
    fail_on_severity: str = typer.Option(
        "high",
        "--fail-on-severity",
        help="CI failure threshold: none, low, medium, high, or critical.",
    ),
    baseline_file: Path | None = typer.Option(None, "--baseline-file", help="Optional baseline JSON file for known findings."),
    policy_file: Path | None = typer.Option(None, "--policy-file", help="Optional red-tool execution policy JSON file."),
) -> None:
    """Run detection, attack, remediation, and validation."""
    try:
        normalized_fail_on_severity = normalize_fail_on_severity(fail_on_severity)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    scenario_spec = _resolve_scenario(terraform_dir, scenario)
    backend = _resolve_backend(target, scenario_spec.backend)
    if not offline and not _scenario_supports_live_terraform(scenario_spec.name):
        raise typer.BadParameter(
            f"Scenario {scenario_spec.name!r} supports offline demo execution only for now. "
            "Use --offline until its live sandbox adapter is implemented."
        )
    if backend.mode == "plan-only":
        offline = True
    for key, value in _localstack_azure_auth_env(backend.name, offline=offline).items():
        os.environ.setdefault(key, value)
    try:
        attack_policy = load_attack_policy(policy_file)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    try:
        red_config = _resolve_agent_config("red", explicit_provider=red_provider, shared_provider=llm_provider, explicit_base_url=red_base_url)
        blue_config = _resolve_agent_config("blue", explicit_provider=blue_provider, shared_provider=llm_provider, explicit_base_url=blue_base_url)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    use_red_mock = mock_agents or not bool(red_config.base_url)
    use_blue_mock = mock_agents or not bool(blue_config.base_url)
    use_mock_agents = use_red_mock and use_blue_mock
    shared_endpoint = red_config == blue_config

    run_id = new_run_id()
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    workspace_dir = run_dir / "workspace"
    _copy_terraform_workspace(terraform_dir, workspace_dir)
    events = EventLog(run_dir / "events.jsonl")

    _print_banner()
    console.print(
        Panel(
            f"Run ID: {run_id}\nScenario: {scenario_spec.name}\nTarget: {backend.name}",
            title="nullstate run",
            border_style="cyan",
        )
    )
    events.write(
        "start",
        "Run started",
        terraform_dir=terraform_dir,
        workspace_dir=workspace_dir,
        target=backend.name,
        target_mode=backend.mode,
        scenario=scenario_spec.name,
        offline=offline,
        mock_agents=use_mock_agents,
        red_mock_agent=use_red_mock,
        blue_mock_agent=use_blue_mock,
        role_specific_endpoints=not shared_endpoint,
    )

    plan, commands = load_plan_json(workspace_dir, offline=offline)
    for result in commands:
        events.write("terraform", "Command completed", command=result.command, returncode=result.returncode)
    if not offline:
        for result in apply_saved_plan(workspace_dir):
            events.write("terraform", "Command completed", command=result.command, returncode=result.returncode)

    findings = find_scenario_findings(scenario_spec.name, workspace_dir, plan)
    events.write("analysis", "IaC input analyzed", finding_count=len(findings))
    write_json(run_dir / "findings.json", [finding.to_dict() for finding in findings])
    if shared_endpoint:
        before_metrics = collect_run_metrics(
            run_dir=run_dir,
            base_url=red_config.base_url,
            offline=not bool(red_config.base_url),
            stage="before",
        )
        endpoint_metrics: dict[str, dict[str, Any]] = {
            "red": {"before": before_metrics},
            "blue": {"before": before_metrics},
        }
    else:
        red_before_metrics = collect_run_metrics(
            run_dir=run_dir,
            base_url=red_config.base_url,
            offline=not bool(red_config.base_url),
            stage="red-before",
        )
        endpoint_metrics = {"red": {"before": red_before_metrics}}
        before_metrics = {
            "mode": "role-specific",
            "message": "See endpoints.red and endpoints.blue for role-specific endpoint metrics.",
        }

    attack_script_path = run_dir / "attack.py"
    attack_manifest_path = run_dir / "attack-manifest.json"
    attack_target_url = _attack_target_url(backend.name, scenario_spec.name, offline=offline)
    write_attack_script(attack_script_path, scenario_spec.name)
    write_attack_manifest(
        attack_manifest_path,
        scenario_name=scenario_spec.name,
        backend_name=backend.name,
        target_url=attack_target_url,
        workspace_dir=workspace_dir,
    )
    red_agent = LlmAgent("red", red_model, base_url=red_config.base_url, api_key=red_config.api_key, provider=red_config.provider)
    red_result = red_agent.complete(
        "You are a red-team IaC security agent constrained to the generated local sandbox and run evidence.",
        f"Find an exploit for these findings: {[finding.to_dict() for finding in findings]}",
        offline=use_red_mock,
    )
    if not shared_endpoint:
        endpoint_metrics["red"]["after"] = collect_run_metrics(
            run_dir=run_dir,
            base_url=red_config.base_url,
            offline=not bool(red_config.base_url),
            stage="red-after",
        )
    before_tool = run_attack_script(
        attack_script_path,
        run_dir=run_dir,
        target_url=attack_target_url,
        stage="before",
        manifest_path=attack_manifest_path,
        policy=attack_policy,
    )
    events.write("red-tool", "Allowlisted attack command completed", **before_tool.to_dict())
    before_attack = simulate_attack(findings, "before")
    before_attack = _with_tool_evidence(before_attack, before_tool)
    events.write("red-team", "Attack attempted before remediation", result=before_attack, agent=red_result)

    if not shared_endpoint:
        endpoint_metrics["blue"] = {
            "before": collect_run_metrics(
                run_dir=run_dir,
                base_url=blue_config.base_url,
                offline=not bool(blue_config.base_url),
                stage="blue-before",
            )
        }

    blue_agent = LlmAgent("blue", blue_model, base_url=blue_config.base_url, api_key=blue_config.api_key, provider=blue_config.provider)
    blue_result = blue_agent.complete(
        "You are a blue-team IaC remediation agent.",
        f"Diagnose and patch these findings: {[finding.to_dict() for finding in findings]}",
        offline=use_blue_mock,
    )
    if not shared_endpoint:
        endpoint_metrics["blue"]["after"] = collect_run_metrics(
            run_dir=run_dir,
            base_url=blue_config.base_url,
            offline=not bool(blue_config.base_url),
            stage="blue-after",
        )

    patch_result = remediate_scenario_files(scenario_spec.name, workspace_dir)
    (run_dir / "remediation.patch").write_text(patch_result.diff, encoding="utf-8")
    if shared_endpoint:
        after_metrics = collect_run_metrics(
            run_dir=run_dir,
            base_url=red_config.base_url,
            offline=not bool(red_config.base_url),
            stage="after",
        )
        endpoint_metrics["red"]["after"] = after_metrics
        endpoint_metrics["blue"]["after"] = after_metrics
    else:
        after_metrics = {
            "mode": "role-specific",
            "message": "See endpoints.red and endpoints.blue for role-specific endpoint metrics.",
        }
    write_json(
        run_dir / "metrics.json",
        {
            "model_calls": [red_result.metrics.to_dict(), blue_result.metrics.to_dict()],
            "endpoint": {
                "before": before_metrics,
                "after": after_metrics,
            },
            "endpoints": endpoint_metrics,
            "notes": (
                "Token metrics come from OpenAI-compatible response usage when available. "
                "Offline mock mode records zero token counts. User-authored prompts are not required; "
                "nullstate sends internal agent instructions plus scenario evidence."
            ),
            "providers": {
                "red": red_config.provider,
                "blue": blue_config.provider,
            },
        },
    )
    events.write("blue-team", "IaC remediation generated", changed=patch_result.changed, agent=blue_result)

    if offline:
        remediated_plan, remediation_commands = load_plan_json(workspace_dir, offline=True)
    else:
        remediated_plan, remediation_commands = load_plan_json(workspace_dir, offline=False)
    for result in remediation_commands:
        events.write("terraform", "Command completed", command=result.command, returncode=result.returncode)
    if not offline:
        for result in apply_saved_plan(workspace_dir):
            events.write("terraform", "Command completed", command=result.command, returncode=result.returncode)
    remaining_findings = find_scenario_findings(scenario_spec.name, workspace_dir, remediated_plan)
    after_tool = run_attack_script(
        attack_script_path,
        run_dir=run_dir,
        target_url=attack_target_url,
        stage="after",
        manifest_path=attack_manifest_path,
        policy=attack_policy,
    )
    events.write("red-tool", "Allowlisted attack command completed", **after_tool.to_dict())
    after_attack = simulate_attack(remaining_findings, "after")
    after_attack = _with_tool_evidence(after_attack, after_tool)
    events.write("validation", "Attack attempted after remediation", result=after_attack, remaining_findings=len(remaining_findings))

    report = render_report(
        run_id=run_id,
        terraform_dir=str(terraform_dir),
        findings=findings,
        before_attack=before_attack,
        after_attack=after_attack,
        patch_diff=patch_result.diff,
        model_notes=f"Red: {red_result.model}. Blue: {blue_result.model}. {blue_result.content}",
        runtime_evidence={
            "before": before_tool.to_dict(),
            "after": after_tool.to_dict(),
        },
    )
    (run_dir / "report.md").write_text(report, encoding="utf-8")

    ci_summary = None
    if ci:
        known_findings = None
        new_findings = None
        if baseline_file is not None:
            baseline_identities = load_baseline_identities(baseline_file)
            known_findings, new_findings = split_known_and_new_findings(findings, baseline_identities)
        ci_summary = build_ci_summary(
            run_id=run_id,
            findings=findings,
            remaining_findings=remaining_findings,
            fail_on_severity=normalized_fail_on_severity,
            before_attack=before_attack,
            after_attack=after_attack,
            baseline_path=str(baseline_file) if baseline_file is not None else None,
            known_findings=known_findings,
            new_findings=new_findings,
        )
        write_json(run_dir / CI_SUMMARY_FILENAME, ci_summary)

    _print_run_summary(run_dir, findings, before_attack, after_attack)
    if ci_summary is not None:
        console.print(
            f"CI summary: {run_dir / CI_SUMMARY_FILENAME} · "
            f"failed={ci_summary['failed']} · exit_code={ci_summary['exit_code']}"
        )
    _print_next_steps(
        [
            f"nullstate report {run_id} --runs-dir {runs_dir}",
            f"nullstate bundle {run_id} --runs-dir {runs_dir}",
            f"nullstate dashboard {run_id} --runs-dir {runs_dir}",
            f"nullstate report --runs-dir {runs_dir}",
            f"nullstate status --runs-dir {runs_dir} --sandbox {backend.name}",
        ]
    )
    if ci_summary is not None and ci_summary["failed"]:
        raise typer.Exit(code=int(ci_summary["exit_code"]))


@sandbox_app.command("list")
def sandbox_list() -> None:
    """List supported sandbox backends."""
    backends = list_backends()
    console.print("Backends: " + ", ".join(backend.name for backend in backends))
    table = Table(title="nullstate sandbox backends")
    table.add_column("Backend")
    table.add_column("Mode")
    table.add_column("IaC target")
    table.add_column("Status")
    table.add_column("Requirements")
    for backend in backends:
        table.add_row(backend.name, backend.mode, backend.target_iac, backend.status, ", ".join(backend.requirements) or "none")
    console.print(table)


@scenarios_app.command("list")
def scenarios_list() -> None:
    """List supported and scaffolded scenarios."""
    scenarios = list_scenarios()
    console.print("Scenarios: " + ", ".join(scenario.name for scenario in scenarios))
    table = Table(title="nullstate scenarios")
    table.add_column("Scenario")
    table.add_column("Backend")
    table.add_column("Mode")
    table.add_column("Status")
    table.add_column("Risk")
    for scenario in scenarios:
        table.add_row(scenario.name, scenario.backend, scenario.mode, scenario.status, scenario.risk)
    console.print(table)


@scenarios_app.command("status")
def scenarios_status(name: str = typer.Argument(..., help="Scenario name.")) -> None:
    """Show scenario details."""
    try:
        scenario = get_scenario(name)
    except KeyError as error:
        raise typer.BadParameter(str(error)) from error
    table = Table(title=f"{scenario.name} scenario")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Backend", scenario.backend)
    table.add_row("Mode", scenario.mode)
    table.add_row("IaC targets", ", ".join(scenario.iac_targets))
    table.add_row("Status", scenario.status)
    table.add_row("Risk", scenario.risk)
    table.add_row("Description", scenario.description)
    console.print(table)


@policy_app.command("init")
def policy_init(
    output: Path = typer.Option(Path(DEFAULT_POLICY_FILENAME), "--output", "-o", help="Policy JSON output path."),
) -> None:
    """Create a starter red-tool execution policy."""
    payload = write_default_policy(output)
    console.print(f"Policy: {output}")
    console.print(
        "Allowed targets="
        + ", ".join(payload["allowed_target_classifications"])
        + " · command policies="
        + ", ".join(payload["allowed_command_policy_ids"])
    )
    _print_next_steps([f"nullstate run examples/aws-public-s3 --offline --policy-file {output}"])


@sandbox_app.command("status")
def sandbox_status(name: str = typer.Argument("plan-only", help="Sandbox backend name.")) -> None:
    """Show backend status and setup requirements."""
    try:
        backend = get_backend(name)
    except KeyError as error:
        raise typer.BadParameter(str(error)) from error

    table = Table(title=f"{backend.name} status")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Mode", backend.mode)
    table.add_row("IaC target", backend.target_iac)
    table.add_row("Description", backend.description)
    table.add_row("Requirements", ", ".join(backend.requirements) or "none")
    table.add_row("Status", backend.status)
    for probe in probe_backend(backend):
        table.add_row(probe.name, f"{probe.status}: {probe.detail}")
    console.print(table)
    _print_next_steps(
        [
            f"nullstate sandbox up {backend.name}",
            _example_run_command(backend.name),
            "nullstate status",
        ]
    )


@sandbox_app.command("up")
def sandbox_up(
    name: str = typer.Argument("localstack-azure", help="Sandbox backend name."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print commands without running them."),
    env_file: Path | None = typer.Option(None, "--env-file", help="Docker env file for sandbox secrets such as LOCALSTACK_AUTH_TOKEN."),
) -> None:
    """Start a sandbox backend."""
    try:
        backend = get_backend(name)
    except KeyError as error:
        raise typer.BadParameter(str(error)) from error

    resolved_env_file = _resolve_sandbox_env_file(env_file)
    container_name, renamed_container = _resolve_sandbox_container_name(backend)
    commands = backend.up_commands(env_file=resolved_env_file, container_name=container_name)
    if dry_run or not commands:
        console.print(render_commands(commands))
        if renamed_container and container_name:
            console.print(
                f"Default container name already exists; planned new container name: {container_name}",
                style="yellow",
            )
        if resolved_env_file:
            console.print(f"Using env file: {resolved_env_file}")
        _print_next_steps(
            [
                f"nullstate sandbox status {backend.name}",
                _example_run_command(backend.name),
            ]
        )
        return
    results = run_commands(commands)
    failed = [result for result in results if result.returncode != 0]
    if failed:
        console.print("Sandbox start failed. Re-run with --dry-run to inspect commands.", style="bold red")
        _print_sandbox_start_failure_hints(backend)
        raise typer.Exit(code=1)
    verified, detail = _verify_sandbox_container_started(container_name)
    if not verified:
        console.print(f"Sandbox container did not stay running: {detail}", style="bold red")
        _print_sandbox_start_failure_hints(backend)
        raise typer.Exit(code=1)
    console.print("Sandbox start commands completed.", style="bold green")
    if renamed_container and container_name:
        console.print(
            f"Default container name already existed; started new container: {container_name}",
            style="yellow",
        )
    if resolved_env_file:
        console.print(f"Used env file: {resolved_env_file}")
    _print_next_steps(
        [
            f"nullstate sandbox status {backend.name}",
            _example_run_command(backend.name),
        ]
    )


@sandbox_app.command("down")
def sandbox_down(
    name: str = typer.Argument("localstack-azure", help="Sandbox backend name."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print commands without running them."),
) -> None:
    """Stop a sandbox backend."""
    try:
        backend = get_backend(name)
    except KeyError as error:
        commands = _resolve_explicit_sandbox_container_down_commands(name)
        if not commands:
            raise typer.BadParameter(str(error)) from error
        if dry_run:
            console.print(render_commands(commands))
            return
        results = run_commands(commands)
        failed = [result for result in results if result.returncode != 0]
        if failed:
            console.print("Sandbox stop failed. Re-run with --dry-run to inspect commands.", style="bold red")
            raise typer.Exit(code=1)
        console.print(f"Sandbox container stopped: {name}", style="bold green")
        return

    commands, target_detail = _resolve_sandbox_down_commands(backend)
    if dry_run or not commands:
        console.print(render_commands(commands))
        if target_detail:
            console.print(target_detail)
        return
    results = run_commands(commands)
    failed = [result for result in results if result.returncode != 0]
    if failed:
        console.print("Sandbox stop failed. Re-run with --dry-run to inspect commands.", style="bold red")
        raise typer.Exit(code=1)
    console.print("Sandbox stop commands completed.", style="bold green")
    if target_detail:
        console.print(target_detail)
    _print_next_steps(["nullstate sandbox status " + backend.name])


@app.command()
def report(
    run_id: str | None = typer.Argument(None, help="Run ID to open. Defaults to the latest run report."),
    runs_dir: Path = typer.Option(Path("runs"), "--runs-dir", help="Directory containing runs."),
) -> None:
    """Print a previous run report."""
    report_path = _resolve_report_path(run_id, runs_dir)
    console.print(f"Report: {report_path}")
    console.print(_console_safe_text(report_path.read_text(encoding="utf-8")), markup=False, highlight=False)


@app.command()
def bundle(
    run_id: str | None = typer.Argument(None, help="Run ID to bundle. Defaults to the latest run."),
    runs_dir: Path = typer.Option(Path("runs"), "--runs-dir", help="Directory containing runs."),
) -> None:
    """Create a portable run bundle for dashboards, CI, support, or future cloud upload."""
    run_dir = _resolve_run_dir(run_id, runs_dir)
    payload = write_run_bundle(run_dir)
    bundle_path = run_dir / BUNDLE_FILENAME
    console.print(f"Bundle: {bundle_path}")
    console.print(
        f"Run {payload['run']['id']} · scenario={payload['run'].get('scenario')} · "
        f"verdict={payload['run'].get('verdict')} · findings={payload['run'].get('finding_count')}"
    )
    _print_next_steps(
        [
            f"nullstate dashboard {payload['run']['id']} --runs-dir {runs_dir}",
            f"nullstate report {payload['run']['id']} --runs-dir {runs_dir}",
        ]
    )


@app.command()
def sarif(
    run_id: str | None = typer.Argument(None, help="Run ID to export. Defaults to the latest run."),
    runs_dir: Path = typer.Option(Path("runs"), "--runs-dir", help="Directory containing runs."),
    output: Path | None = typer.Option(None, "--output", "-o", help=f"Output SARIF path. Defaults to {SARIF_FILENAME} in the run directory."),
) -> None:
    """Export run findings as SARIF for CI and code-scanning tools."""
    run_dir = _resolve_run_dir(run_id, runs_dir)
    sarif_path = output or run_dir / SARIF_FILENAME
    payload = write_sarif(run_dir, sarif_path)
    result_count = len(payload["runs"][0]["results"])
    console.print(f"SARIF: {sarif_path}")
    console.print(f"Run {run_dir.name} · results={result_count}")
    _print_next_steps(
        [
            f"nullstate report {run_dir.name} --runs-dir {runs_dir}",
            f"nullstate bundle {run_dir.name} --runs-dir {runs_dir}",
        ]
    )


@app.command("evidence-manifest")
def evidence_manifest(
    run_id: str | None = typer.Argument(None, help="Run ID to inventory. Defaults to the latest run."),
    runs_dir: Path = typer.Option(Path("runs"), "--runs-dir", help="Directory containing runs."),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help=f"Output JSON path. Defaults to {EVIDENCE_MANIFEST_FILENAME} in the run directory.",
    ),
) -> None:
    """Write an integrity manifest for shareable run evidence artifacts."""
    run_dir = _resolve_run_dir(run_id, runs_dir)
    try:
        payload = write_evidence_manifest(run_dir, output_path=output)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    manifest_path = output or run_dir / EVIDENCE_MANIFEST_FILENAME
    console.print(f"Evidence manifest: {manifest_path}")
    console.print(
        f"Run {payload['run']['id']} - artifacts={payload['artifact_count']} - "
        f"signing={payload['signing']['status']}"
    )
    _print_next_steps(
        [
            f"nullstate bundle {run_dir.name} --runs-dir {runs_dir}",
            f"nullstate scrub {run_dir.name} --runs-dir {runs_dir}",
        ]
    )


@app.command()
def dashboard(
    run_id: str | None = typer.Argument(None, help="Run ID to render. Defaults to the latest run."),
    runs_dir: Path = typer.Option(Path("runs"), "--runs-dir", help="Directory containing runs."),
    open_browser: bool = typer.Option(False, "--open", help="Open the generated dashboard in the default browser."),
) -> None:
    """Generate a free local single-run HTML dashboard."""
    run_dir = _resolve_run_dir(run_id, runs_dir)
    dashboard_path = write_run_dashboard(run_dir)
    console.print(f"Dashboard: {dashboard_path}")
    if open_browser:
        webbrowser.open(dashboard_path.resolve().as_uri())
    _print_next_steps(
        [
            f"nullstate bundle {run_dir.name} --runs-dir {runs_dir}",
            f"nullstate report {run_dir.name} --runs-dir {runs_dir}",
        ]
    )


@app.command()
def scrub(
    run_id: str | None = typer.Argument(None, help="Run ID to scrub. Defaults to the latest run."),
    runs_dir: Path = typer.Option(Path("runs"), "--runs-dir", help="Directory containing runs."),
    output_dir: Path = typer.Option(Path("scrubbed-runs"), "--output-dir", help="Directory for scrubbed run copies."),
) -> None:
    """Create a scrubbed copy of a run for publishing, support, or review."""
    run_dir = _resolve_run_dir(run_id, runs_dir)
    try:
        report_payload = scrub_run_artifacts(run_dir, output_dir)
    except FileExistsError as error:
        raise typer.BadParameter(str(error)) from error
    scrubbed_dir = Path(str(report_payload["scrubbed_run_dir"]))
    console.print(f"Scrubbed run: {scrubbed_dir}")
    console.print(f"Scrub report: {scrubbed_dir / 'scrub-report.json'}")
    console.print(
        f"Files scanned={report_payload['files_scanned']} "
        f"changed={len(report_payload['files_changed'])}"
    )
    _print_next_steps(
        [
            f"nullstate report {scrubbed_dir.name} --runs-dir {scrubbed_dir.parent}",
            f"nullstate bundle {scrubbed_dir.name} --runs-dir {scrubbed_dir.parent}",
        ]
    )


@app.command()
def upload(
    run_id: str | None = typer.Argument(None, help="Run ID to prepare for upload. Defaults to the latest run."),
    runs_dir: Path = typer.Option(Path("runs"), "--runs-dir", help="Directory containing runs."),
    endpoint: str = typer.Option(DEFAULT_UPLOAD_ENDPOINT, "--endpoint", help="Future Nullstate Cloud ingestion endpoint."),
    token_env: str = typer.Option(DEFAULT_UPLOAD_TOKEN_ENV, "--token-env", help="Environment variable that will hold the cloud token."),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Only write an upload plan; live upload is not implemented yet."),
) -> None:
    """Prepare a dry-run upload plan for future Nullstate Cloud ingestion."""
    if not dry_run:
        raise typer.BadParameter("Live upload is not implemented yet. Use --dry-run.")
    run_dir = _resolve_run_dir(run_id, runs_dir)
    plan = write_upload_plan(run_dir, endpoint=endpoint, token_env=token_env)
    plan_path = run_dir / UPLOAD_PLAN_FILENAME
    console.print(f"Upload plan: {plan_path}")
    console.print(
        f"Run {plan['run']['id']} · dry_run={plan['dry_run']} · "
        f"token_present={plan['auth']['token_present']}"
    )
    _print_next_steps(
        [
            f"nullstate bundle {run_dir.name} --runs-dir {runs_dir}",
            f"nullstate scrub {run_dir.name} --runs-dir {runs_dir}",
        ]
    )


@app.command()
def baseline(
    run_id: str | None = typer.Argument(None, help="Run ID to baseline. Defaults to the latest run."),
    runs_dir: Path = typer.Option(Path("runs"), "--runs-dir", help="Directory containing runs."),
    output: Path = typer.Option(Path(DEFAULT_BASELINE_FILENAME), "--output", "-o", help="Baseline JSON output path."),
) -> None:
    """Export current run findings as a CI baseline."""
    run_dir = _resolve_run_dir(run_id, runs_dir)
    payload = write_baseline(run_dir, output)
    console.print(f"Baseline: {output}")
    console.print(f"Run {payload['run_id']} · findings={payload['finding_count']}")
    _print_next_steps(
        [
            f"nullstate run examples/aws-public-s3 --offline --ci --baseline-file {output}",
            f"nullstate report {run_dir.name} --runs-dir {runs_dir}",
        ]
    )


@app.command("policy-result")
def policy_result(
    run_id: str | None = typer.Argument(None, help="Run ID to evaluate. Defaults to the latest run."),
    runs_dir: Path = typer.Option(Path("runs"), "--runs-dir", help="Directory containing runs."),
    output: Path | None = typer.Option(None, "--output", "-o", help=f"Output JSON path. Defaults to {POLICY_RESULT_FILENAME} in the run directory."),
    fail_on_severity: str = typer.Option("high", "--fail-on-severity", help="Failure threshold: none, low, medium, high, or critical."),
    baseline_file: Path | None = typer.Option(None, "--baseline-file", help="Optional baseline JSON file for known findings."),
) -> None:
    """Export a JSON policy decision from an existing run."""
    run_dir = _resolve_run_dir(run_id, runs_dir)
    try:
        payload = write_policy_result(
            run_dir,
            fail_on_severity=fail_on_severity,
            baseline_file=baseline_file,
            output_path=output,
        )
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    result_path = output or run_dir / POLICY_RESULT_FILENAME
    console.print(f"Policy result: {result_path}")
    console.print(
        f"Run {payload['run_id']} · failed={payload['failed']} · "
        f"evaluated_findings={payload['evaluated_finding_count']}"
    )
    _print_next_steps(
        [
            f"nullstate sarif {run_dir.name} --runs-dir {runs_dir}",
            f"nullstate report {run_dir.name} --runs-dir {runs_dir}",
        ]
    )


def _print_run_summary(run_dir: Path, findings, before_attack: dict[str, str], after_attack: dict[str, str]) -> None:
    table = Table(title="Run Summary")
    table.add_column("Stage")
    table.add_column("Result")
    table.add_column("Detail")
    table.add_row("Analysis", f"{len(findings)} finding(s)", "Scenario-specific IaC exposure scan")
    table.add_row("Red before", before_attack["status"], before_attack["detail"])
    table.add_row("Red after", after_attack["status"], after_attack["detail"])
    table.add_row("Artifacts", "written", str(run_dir))
    console.print(table)


def _llm_configured() -> bool:
    return bool(
        os.getenv("NULLSTATE_LLM_BASE_URL")
        or os.getenv("NULLSTATE_RED_LLM_BASE_URL")
        or os.getenv("NULLSTATE_BLUE_LLM_BASE_URL")
        or os.getenv("NULLSTATE_LLM_PROVIDER")
        or os.getenv("NULLSTATE_RED_LLM_PROVIDER")
        or os.getenv("NULLSTATE_BLUE_LLM_PROVIDER")
    )


def _endpoint_status_detail() -> str:
    red = os.getenv("NULLSTATE_RED_LLM_BASE_URL")
    blue = os.getenv("NULLSTATE_BLUE_LLM_BASE_URL")
    shared = os.getenv("NULLSTATE_LLM_BASE_URL")
    if red or blue:
        return f"red={_redact_url(red)}, blue={_redact_url(blue)}"
    if shared:
        return f"shared={_redact_url(shared)}"
    provider = os.getenv("NULLSTATE_LLM_PROVIDER")
    if provider:
        return f"provider={provider}"
    return "Set NULLSTATE_LLM_BASE_URL, role-specific endpoints, or NULLSTATE_LLM_PROVIDER=google or claude."


def _redact_url(value: str | None) -> str:
    if not value:
        return "missing"
    return value.split("//", 1)[-1].split("/", 1)[0]


def _console_safe_text(value: str, *, encoding: str | None = None) -> str:
    target_encoding = encoding or getattr(console.file, "encoding", None) or "utf-8"
    try:
        value.encode(target_encoding)
    except (LookupError, UnicodeError):
        return value.encode(target_encoding, errors="replace").decode(target_encoding, errors="replace")
    return value


def _print_banner() -> None:
    console.print(BANNER, style="bold cyan")


def _print_next_steps(commands: list[str]) -> None:
    if not commands:
        return
    table = Table(title="Next")
    table.add_column("Command")
    for command in commands:
        table.add_row(command)
    console.print(table)


def _example_run_command(backend_name: str) -> str:
    examples = {
        "localstack-azure": "examples/azure-public-blob",
        "localstack-aws": "examples/aws-public-s3",
        "kind-kubernetes": "examples/k8s-privileged-pod",
        "docker-compose": "examples/compose-exposed-admin",
        "microvm-onprem": "examples/onprem-ssh-password",
        "plan-only": "examples/generic-plan-review",
    }
    return f"nullstate run {examples.get(backend_name, 'examples/azure-public-blob')}"


def _attack_target_url(backend_name: str, scenario_name: str, *, offline: bool) -> str:
    if offline:
        return f"offline://{scenario_name}"
    if backend_name in {"localstack-aws", "localstack-azure"}:
        return "http://localhost.localstack.cloud:4566"
    return f"local://{backend_name}/{scenario_name}"


def _with_tool_evidence(attack: dict[str, str], tool_result) -> dict[str, str]:
    detail = attack.get("detail", "No detail recorded.")
    enriched = dict(attack)
    enriched["detail"] = (
        f"{detail} Allowlisted tool command returned {tool_result.returncode}: "
        f"`{_summarize_tool_command(tool_result.command)}` target={tool_result.target_url}."
    )
    return enriched


def _summarize_tool_command(command: list[str]) -> str:
    if len(command) >= 2 and Path(command[1]).name == "attack.py":
        return "python attack.py " + " ".join(command[2:])
    return " ".join(command)


def _resolve_scenario(terraform_dir: Path, scenario: str):
    if scenario == "auto":
        inferred = infer_scenario(terraform_dir)
        if inferred is None:
            raise typer.BadParameter(
                "Could not infer a scenario from the IaC directory. "
                "Pass --scenario explicitly or run `nullstate scenarios list`."
            )
        return inferred
    try:
        return get_scenario(scenario)
    except KeyError as error:
        raise typer.BadParameter(str(error)) from error


def _resolve_backend(target: str, scenario_backend: str):
    backend_name = scenario_backend if target == "auto" else target
    try:
        return get_backend(backend_name)
    except KeyError as error:
        raise typer.BadParameter(str(error)) from error


def _scenario_supports_live_terraform(scenario_name: str) -> bool:
    return scenario_name in {"azure-public-blob", "aws-public-s3"}


def _resolve_sandbox_env_file(
    explicit: Path | None,
    candidates: list[str] | None = None,
    *,
    cwd: Path | None = None,
) -> Path | None:
    if explicit is not None:
        return explicit
    search_root = cwd or Path.cwd()
    for candidate in candidates or [".env.local", ".env"]:
        path = search_root / candidate
        if path.is_file():
            return path
    return None


def _resolve_sandbox_container_name(
    backend,
    *,
    container_exists=None,
    suffix: str | None = None,
) -> tuple[str | None, bool]:
    base_name = backend.default_container_name()
    if base_name is None:
        return None, False
    exists = container_exists or _docker_container_exists
    if not exists(base_name):
        return base_name, False
    resolved_suffix = suffix or datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"{base_name}-{resolved_suffix}", True


def _docker_container_exists(container_name: str) -> bool:
    result = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name=^/{container_name}$", "--format", "{{.Names}}"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0 and container_name in {line.strip() for line in result.stdout.splitlines()}


def _verify_sandbox_container_started(
    container_name: str | None,
    *,
    runner=None,
    sleep_seconds: float = 2.0,
) -> tuple[bool, str]:
    if not container_name:
        return True, "No container runtime to verify."
    if sleep_seconds > 0:
        time.sleep(sleep_seconds)
    run = runner or subprocess.run
    result = run(
        [
            "docker",
            "inspect",
            "--format",
            "{{.State.Running}} {{.State.Status}} {{.State.ExitCode}}",
            container_name,
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return False, (result.stderr or result.stdout or f"Could not inspect container {container_name}.").strip()
    raw = result.stdout.strip()
    parts = raw.split()
    if parts and parts[0].lower() == "true":
        return True, f"{container_name} is running."
    status = parts[1] if len(parts) > 1 else "unknown"
    exit_code = parts[2] if len(parts) > 2 else "unknown"
    return False, f"{container_name} status={status} exit_code={exit_code}"


def _resolve_sandbox_down_commands(backend, *, container_lister=None) -> tuple[list[list[str]], str]:
    lister = container_lister or _list_sandbox_containers
    container_names = lister(backend)
    if container_names:
        return backend.down_commands(container_names=container_names), "Target containers: " + ", ".join(container_names)
    return backend.down_commands(), ""


def _resolve_explicit_sandbox_container_down_commands(container_name: str) -> list[list[str]]:
    if _is_localstack_container_name(container_name):
        return [["docker", "rm", "-f", container_name]]
    return []


def _list_sandbox_containers(backend) -> list[str]:
    base_name = backend.default_container_name()
    image = backend.container_image()
    if not base_name or not image:
        return []
    result = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name={base_name}", "--filter", f"ancestor={image}", "--format", "{{.Names}}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    names = sorted({line.strip() for line in result.stdout.splitlines() if line.strip()})
    return [
        name
        for name in names
        if name == base_name
        or name.startswith(f"{base_name}-")
        or (name.startswith("nullstate-cli-localstack-") and base_name in name)
    ]


def _print_sandbox_start_failure_hints(backend) -> None:
    if backend.name not in {"localstack-aws", "localstack-azure"}:
        return
    console.print(
        Panel(
            "\n".join(
                [
                    "If Docker reported `Bind for 127.0.0.1:4566 failed` or `port is already allocated`,",
                    "a leftover LocalStack container is probably still reserving the shared edge port.",
                    "",
                    f"Try: nullstate sandbox down {backend.name}",
                    "Then retry: nullstate sandbox up " + backend.name,
                    "",
                    "To inspect manually: docker ps -a --filter name=localstack",
                ]
            ),
            title="Port 4566 Hint",
            border_style="yellow",
        )
    )


def _is_localstack_container_name(container_name: str) -> bool:
    return (
        container_name == "localstack"
        or container_name.startswith("localstack-")
        or container_name == "localstack-azure"
        or container_name.startswith("localstack-azure-")
        or container_name.startswith("nullstate-cli-localstack-")
    )


def _localstack_azure_auth_env(backend_name: str, *, offline: bool) -> dict[str, str]:
    if offline or backend_name != "localstack-azure":
        return {}
    null_uuid = "00000000-0000-0000-0000-000000000000"
    return {
        "ARM_CLIENT_ID": null_uuid,
        "ARM_CLIENT_SECRET": "nullstate-localstack",
        "ARM_TENANT_ID": null_uuid,
        "ARM_SUBSCRIPTION_ID": null_uuid,
    }


def _resolve_agent_api_key(role: str) -> str:
    role_env = f"NULLSTATE_{role.upper()}_LLM_API_KEY"
    return os.getenv(role_env) or os.getenv("NULLSTATE_LLM_API_KEY") or ""


def _resolve_agent_config(
    role: str,
    *,
    explicit_provider: str | None,
    shared_provider: str | None,
    explicit_base_url: str | None,
) -> LlmEndpointConfig:
    provider = normalize_provider(
        explicit_provider
        or os.getenv(f"NULLSTATE_{role.upper()}_LLM_PROVIDER")
        or shared_provider
        or os.getenv("NULLSTATE_LLM_PROVIDER")
    )
    role_env = f"NULLSTATE_{role.upper()}_LLM_BASE_URL"
    base_url = resolve_base_url(
        provider=provider,
        explicit_base_url=explicit_base_url,
        role_base_url=os.getenv(role_env),
        shared_base_url=os.getenv("NULLSTATE_LLM_BASE_URL"),
    )
    return LlmEndpointConfig(provider=provider, base_url=base_url, api_key=_resolve_agent_api_key(role))


def _copy_terraform_workspace(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(
            ".terraform",
            "terraform.tfstate",
            "terraform.tfstate.*",
            "tfplan",
            "runs",
            "__pycache__",
        ),
    )


def _resolve_report_path(run_id: str | None, runs_dir: Path) -> Path:
    if run_id:
        direct = runs_dir / run_id / "report.md"
        if direct.exists():
            return direct
        matches = sorted(path for path in runs_dir.rglob("report.md") if path.parent.name == run_id)
        if matches:
            return matches[-1]
        raise typer.BadParameter(f"Report not found for run {run_id!r} under {runs_dir}")
    latest = _latest_report_path(runs_dir)
    if latest is None:
        raise typer.BadParameter(f"No reports found under {runs_dir}")
    return latest


def _resolve_run_dir(run_id: str | None, runs_dir: Path) -> Path:
    return _resolve_report_path(run_id, runs_dir).parent


def _latest_report_path(runs_dir: Path) -> Path | None:
    reports = [path for path in runs_dir.rglob("report.md") if path.is_file()]
    if not reports:
        return None
    return max(reports, key=lambda path: (path.parent.name, path.stat().st_mtime))
