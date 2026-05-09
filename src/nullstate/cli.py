from __future__ import annotations

import os
import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .agents import LlmAgent
from .artifacts import EventLog, new_run_id, write_json
from .attack import simulate_attack, write_attack_script
from .demo import create_demo
from .findings import find_scenario_findings
from .metrics import collect_run_metrics
from .remediation import remediate_scenario_files
from .report import render_report
from .sandbox import get_backend, list_backends, probe_backend, render_commands, run_commands
from .scenario_detection import infer_scenario
from .scenarios import get_scenario, list_scenarios
from .terraform import load_plan_json


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
        table.add_row("LLM endpoint", "configured" if _llm_configured() else "missing", "NULLSTATE_LLM_BASE_URL")

    console.print(table)


@app.command("init-demo")
def init_demo(
    name: str = typer.Argument(..., help="Demo name. Run `nullstate scenarios list` to see options."),
    output: Path = typer.Option(Path("examples/azure-public-blob"), "--output", "-o", help="Directory to create."),
) -> None:
    """Create an intentionally vulnerable IaC demo."""
    create_demo(name, output)
    console.print(f"Created demo at {output}")


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
) -> None:
    """Run detection, attack, remediation, and validation."""
    scenario_spec = _resolve_scenario(terraform_dir, scenario)
    backend = _resolve_backend(target, scenario_spec.backend)
    if scenario_spec.name != "azure-public-blob" and not offline:
        raise typer.BadParameter(
            f"Scenario {scenario_spec.name!r} supports offline demo execution only for now. "
            "Use --offline until its live sandbox adapter is implemented."
        )
    if backend.mode == "plan-only":
        offline = True
    llm_base_url = os.getenv("NULLSTATE_LLM_BASE_URL")
    use_mock_agents = mock_agents or not bool(llm_base_url)

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
    )

    plan, commands = load_plan_json(workspace_dir, offline=offline)
    for result in commands:
        events.write("terraform", "Command completed", command=result.command, returncode=result.returncode)

    findings = find_scenario_findings(scenario_spec.name, workspace_dir, plan)
    events.write("analysis", "IaC input analyzed", finding_count=len(findings))
    write_json(run_dir / "findings.json", [finding.to_dict() for finding in findings])
    before_metrics = collect_run_metrics(
        run_dir=run_dir,
        base_url=llm_base_url,
        offline=not bool(llm_base_url),
        stage="before",
    )

    write_attack_script(run_dir / "attack.py", scenario_spec.name)
    red_agent = LlmAgent("red", red_model)
    red_result = red_agent.complete(
        "You are a red-team IaC security agent constrained to the generated local sandbox and run evidence.",
        f"Find an exploit for these findings: {[finding.to_dict() for finding in findings]}",
        offline=use_mock_agents,
    )
    before_attack = simulate_attack(findings, "before")
    events.write("red-team", "Attack attempted before remediation", result=before_attack, agent=red_result)

    blue_agent = LlmAgent("blue", blue_model)
    blue_result = blue_agent.complete(
        "You are a blue-team IaC remediation agent.",
        f"Diagnose and patch these findings: {[finding.to_dict() for finding in findings]}",
        offline=use_mock_agents,
    )

    patch_result = remediate_scenario_files(scenario_spec.name, workspace_dir)
    (run_dir / "remediation.patch").write_text(patch_result.diff, encoding="utf-8")
    after_metrics = collect_run_metrics(
        run_dir=run_dir,
        base_url=llm_base_url,
        offline=not bool(llm_base_url),
        stage="after",
    )
    write_json(
        run_dir / "metrics.json",
        {
            "model_calls": [red_result.metrics.to_dict(), blue_result.metrics.to_dict()],
            "endpoint": {
                "before": before_metrics,
                "after": after_metrics,
            },
            "notes": (
                "Token metrics come from OpenAI-compatible response usage when available. "
                "Offline mock mode records zero token counts. User-authored prompts are not required; "
                "nullstate sends internal agent instructions plus scenario evidence."
            ),
        },
    )
    events.write("blue-team", "IaC remediation generated", changed=patch_result.changed, agent=blue_result)

    remediated_plan, _ = load_plan_json(workspace_dir, offline=True)
    remaining_findings = find_scenario_findings(scenario_spec.name, workspace_dir, remediated_plan)
    after_attack = simulate_attack(remaining_findings, "after")
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


@sandbox_app.command("up")
def sandbox_up(
    name: str = typer.Argument("localstack-azure", help="Sandbox backend name."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print commands without running them."),
) -> None:
    """Start a sandbox backend."""
    try:
        backend = get_backend(name)
    except KeyError as error:
        raise typer.BadParameter(str(error)) from error

    commands = backend.up_commands()
    if dry_run or not commands:
        console.print(render_commands(commands))
        return
    results = run_commands(commands)
    failed = [result for result in results if result.returncode != 0]
    if failed:
        raise typer.Exit(code=1)


@sandbox_app.command("down")
def sandbox_down(
    name: str = typer.Argument("localstack-azure", help="Sandbox backend name."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print commands without running them."),
) -> None:
    """Stop a sandbox backend."""
    try:
        backend = get_backend(name)
    except KeyError as error:
        raise typer.BadParameter(str(error)) from error

    commands = backend.down_commands()
    if dry_run or not commands:
        console.print(render_commands(commands))
        return
    results = run_commands(commands)
    failed = [result for result in results if result.returncode != 0]
    if failed:
        raise typer.Exit(code=1)


@app.command()
def report(run_id: str, runs_dir: Path = typer.Option(Path("runs"), "--runs-dir", help="Directory containing runs.")) -> None:
    """Print a previous run report."""
    report_path = runs_dir / run_id / "report.md"
    if not report_path.exists():
        raise typer.BadParameter(f"Report not found: {report_path}")
    console.print(report_path.read_text(encoding="utf-8"))


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
    import os

    return bool(os.getenv("NULLSTATE_LLM_BASE_URL"))


def _print_banner() -> None:
    console.print(BANNER, style="bold cyan")


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
