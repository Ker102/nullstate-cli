from __future__ import annotations

import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .agents import LlmAgent
from .artifacts import EventLog, new_run_id, write_json
from .attack import simulate_attack, write_attack_script
from .attack_runner import run_attack_script
from .demo import create_demo
from .findings import find_scenario_findings
from .metrics import collect_run_metrics
from .remediation import remediate_scenario_files
from .report import render_report
from .sandbox import get_backend, list_backends, probe_backend, render_commands, run_commands
from .scenario_detection import infer_scenario
from .scenarios import get_scenario, list_scenarios
from .terraform import apply_saved_plan, load_plan_json


app = typer.Typer(no_args_is_help=True, help="Autonomous purple-teaming CLI for infrastructure-as-code sandboxes.")
sandbox_app = typer.Typer(no_args_is_help=True, help="Manage local sandbox backends.")
scenarios_app = typer.Typer(no_args_is_help=True, help="Inspect supported attack scenarios.")
app.add_typer(sandbox_app, name="sandbox")
app.add_typer(scenarios_app, name="scenarios")
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
) -> None:
    """Run detection, attack, remediation, and validation."""
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
    red_endpoint = _resolve_agent_base_url("red", red_base_url)
    blue_endpoint = _resolve_agent_base_url("blue", blue_base_url)
    red_api_key = _resolve_agent_api_key("red")
    blue_api_key = _resolve_agent_api_key("blue")
    use_red_mock = mock_agents or not bool(red_endpoint)
    use_blue_mock = mock_agents or not bool(blue_endpoint)
    use_mock_agents = use_red_mock and use_blue_mock
    shared_endpoint = red_endpoint == blue_endpoint

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
            base_url=red_endpoint,
            offline=not bool(red_endpoint),
            stage="before",
        )
        endpoint_metrics: dict[str, dict[str, Any]] = {
            "red": {"before": before_metrics},
            "blue": {"before": before_metrics},
        }
    else:
        red_before_metrics = collect_run_metrics(
            run_dir=run_dir,
            base_url=red_endpoint,
            offline=not bool(red_endpoint),
            stage="red-before",
        )
        endpoint_metrics = {"red": {"before": red_before_metrics}}
        before_metrics = {
            "mode": "role-specific",
            "message": "See endpoints.red and endpoints.blue for role-specific endpoint metrics.",
        }

    attack_script_path = run_dir / "attack.py"
    attack_target_url = _attack_target_url(backend.name, scenario_spec.name, offline=offline)
    write_attack_script(attack_script_path, scenario_spec.name)
    red_agent = LlmAgent("red", red_model, base_url=red_endpoint, api_key=red_api_key)
    red_result = red_agent.complete(
        "You are a red-team IaC security agent constrained to the generated local sandbox and run evidence.",
        f"Find an exploit for these findings: {[finding.to_dict() for finding in findings]}",
        offline=use_red_mock,
    )
    if not shared_endpoint:
        endpoint_metrics["red"]["after"] = collect_run_metrics(
            run_dir=run_dir,
            base_url=red_endpoint,
            offline=not bool(red_endpoint),
            stage="red-after",
        )
    before_tool = run_attack_script(
        attack_script_path,
        run_dir=run_dir,
        target_url=attack_target_url,
        stage="before",
    )
    events.write("red-tool", "Allowlisted attack command completed", **before_tool.to_dict())
    before_attack = simulate_attack(findings, "before")
    before_attack = _with_tool_evidence(before_attack, before_tool)
    events.write("red-team", "Attack attempted before remediation", result=before_attack, agent=red_result)

    if not shared_endpoint:
        endpoint_metrics["blue"] = {
            "before": collect_run_metrics(
                run_dir=run_dir,
                base_url=blue_endpoint,
                offline=not bool(blue_endpoint),
                stage="blue-before",
            )
        }

    blue_agent = LlmAgent("blue", blue_model, base_url=blue_endpoint, api_key=blue_api_key)
    blue_result = blue_agent.complete(
        "You are a blue-team IaC remediation agent.",
        f"Diagnose and patch these findings: {[finding.to_dict() for finding in findings]}",
        offline=use_blue_mock,
    )
    if not shared_endpoint:
        endpoint_metrics["blue"]["after"] = collect_run_metrics(
            run_dir=run_dir,
            base_url=blue_endpoint,
            offline=not bool(blue_endpoint),
            stage="blue-after",
        )

    patch_result = remediate_scenario_files(scenario_spec.name, workspace_dir)
    (run_dir / "remediation.patch").write_text(patch_result.diff, encoding="utf-8")
    if shared_endpoint:
        after_metrics = collect_run_metrics(
            run_dir=run_dir,
            base_url=red_endpoint,
            offline=not bool(red_endpoint),
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
    )
    (run_dir / "report.md").write_text(report, encoding="utf-8")

    _print_run_summary(run_dir, findings, before_attack, after_attack)
    _print_next_steps(
        [
            f"nullstate report {run_id} --runs-dir {runs_dir}",
            f"nullstate report --runs-dir {runs_dir}",
            f"nullstate status --runs-dir {runs_dir} --sandbox {backend.name}",
        ]
    )


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
    )


def _endpoint_status_detail() -> str:
    red = os.getenv("NULLSTATE_RED_LLM_BASE_URL")
    blue = os.getenv("NULLSTATE_BLUE_LLM_BASE_URL")
    shared = os.getenv("NULLSTATE_LLM_BASE_URL")
    if red or blue:
        return f"red={_redact_url(red)}, blue={_redact_url(blue)}"
    if shared:
        return f"shared={_redact_url(shared)}"
    return "Set NULLSTATE_LLM_BASE_URL or role-specific red/blue endpoints."


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
    return [name for name in names if name == base_name or name.startswith(f"{base_name}-")]


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


def _resolve_agent_base_url(role: str, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    role_env = f"NULLSTATE_{role.upper()}_LLM_BASE_URL"
    return os.getenv(role_env) or os.getenv("NULLSTATE_LLM_BASE_URL")


def _resolve_agent_api_key(role: str) -> str:
    role_env = f"NULLSTATE_{role.upper()}_LLM_API_KEY"
    return os.getenv(role_env) or os.getenv("NULLSTATE_LLM_API_KEY") or ""


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


def _latest_report_path(runs_dir: Path) -> Path | None:
    reports = [path for path in runs_dir.rglob("report.md") if path.is_file()]
    if not reports:
        return None
    return max(reports, key=lambda path: (path.parent.name, path.stat().st_mtime))
