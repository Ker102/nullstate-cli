from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import requests


SandboxMode = Literal["executable", "digital-twin", "plan-only"]


@dataclass(frozen=True)
class SandboxBackend:
    name: str
    mode: SandboxMode
    target_iac: str
    description: str
    requirements: list[str]
    status: str
    available_without_runtime: bool = False

    def up_commands(self, env_file: Path | None = None) -> list[list[str]]:
        if self.name == "localstack-azure":
            return [
                ["docker", "pull", "localstack/localstack-azure-alpha"],
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    "localstack-azure",
                    "-p",
                    "127.0.0.1:4566:4566",
                    "-v",
                    "/var/run/docker.sock:/var/run/docker.sock",
                    "-v",
                    "~/.localstack/volume:/var/lib/localstack",
                    *_localstack_auth_args(env_file),
                    "localstack/localstack-azure-alpha",
                ],
            ]
        if self.name == "localstack-aws":
            return [
                ["docker", "pull", "localstack/localstack"],
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    "localstack",
                    "-p",
                    "127.0.0.1:4566:4566",
                    *_localstack_auth_args(env_file),
                    "localstack/localstack",
                ],
            ]
        if self.name == "kind-kubernetes":
            return [["kind", "create", "cluster", "--name", "nullstate"]]
        if self.name == "docker-compose":
            return [["docker", "compose", "up", "-d"]]
        if self.name == "microvm-onprem":
            return [["nullstate", "sandbox", "plan", "microvm-onprem"]]
        return []

    def down_commands(self) -> list[list[str]]:
        if self.name == "localstack-azure":
            return [["docker", "rm", "-f", "localstack-azure"]]
        if self.name == "localstack-aws":
            return [["docker", "rm", "-f", "localstack"]]
        if self.name == "kind-kubernetes":
            return [["kind", "delete", "cluster", "--name", "nullstate"]]
        if self.name == "docker-compose":
            return [["docker", "compose", "down"]]
        return []


@dataclass(frozen=True)
class RuntimeProbe:
    name: str
    status: str
    detail: str


BACKENDS: tuple[SandboxBackend, ...] = (
    SandboxBackend(
        name="localstack-azure",
        mode="executable",
        target_iac="Terraform AzureRM",
        description="Runs Azure cloud-control-plane scenarios against LocalStack for Azure.",
        requirements=["Docker", "LOCALSTACK_AUTH_TOKEN", "Terraform", "Azure CLI or azlocal"],
        status="v1 demo target",
    ),
    SandboxBackend(
        name="localstack-aws",
        mode="executable",
        target_iac="Terraform AWS",
        description="Runs AWS-style cloud scenarios against the LocalStack AWS emulator.",
        requirements=["Docker", "LOCALSTACK_AUTH_TOKEN", "Terraform", "AWS provider tooling"],
        status="adapter scaffolded",
    ),
    SandboxBackend(
        name="kind-kubernetes",
        mode="executable",
        target_iac="Kubernetes YAML, Helm, Kustomize",
        description="Runs cluster misconfiguration scenarios in a disposable local Kubernetes cluster.",
        requirements=["Docker", "kind", "kubectl"],
        status="adapter scaffolded",
    ),
    SandboxBackend(
        name="docker-compose",
        mode="digital-twin",
        target_iac="Docker Compose and app stacks",
        description="Creates an isolated Docker network to emulate on-prem application topology.",
        requirements=["Docker Compose"],
        status="adapter scaffolded",
    ),
    SandboxBackend(
        name="microvm-onprem",
        mode="digital-twin",
        target_iac="Ansible, Linux hardening, libvirt/Proxmox-style Terraform",
        description="Maps on-prem intent into disposable VM or container-lab attack surfaces.",
        requirements=["Provider-specific VM or container-lab runtime"],
        status="design-ready fallback",
    ),
    SandboxBackend(
        name="plan-only",
        mode="plan-only",
        target_iac="Any IaC with a parser or exported plan",
        description="Runs static plan analysis, attack hypotheses, remediation, and report generation without execution.",
        requirements=[],
        status="available",
        available_without_runtime=True,
    ),
)


def list_backends() -> list[SandboxBackend]:
    return list(BACKENDS)


def get_backend(name: str) -> SandboxBackend:
    normalized = "plan-only" if name == "offline-plan" else name
    for backend in BACKENDS:
        if backend.name == normalized:
            return backend
    known = ", ".join(backend.name for backend in BACKENDS)
    raise KeyError(f"Unknown sandbox backend {name!r}. Known backends: {known}")


def render_commands(commands: list[list[str]]) -> str:
    return "\n".join(" ".join(command) for command in commands) if commands else "No runtime commands required."


def run_commands(commands: list[list[str]]) -> list[subprocess.CompletedProcess[str]]:
    completed: list[subprocess.CompletedProcess[str]] = []
    for command in commands:
        completed.append(subprocess.run(command, text=True, check=False))
    return completed


def _localstack_auth_args(env_file: Path | None) -> list[str]:
    if env_file is not None:
        return ["--env-file", str(env_file)]
    return ["-e", "LOCALSTACK_AUTH_TOKEN"]


def probe_backend(backend: SandboxBackend) -> list[RuntimeProbe]:
    if backend.name == "localstack-azure":
        return [
            _probe_docker("Runtime docker", ["name=localstack-azure", "ancestor=localstack/localstack-azure-alpha"]),
            _probe_http("Runtime HTTP", "http://localhost.localstack.cloud:4566/_localstack/health"),
        ]
    if backend.name == "localstack-aws":
        return [
            _probe_docker("Runtime docker", ["name=localstack", "ancestor=localstack/localstack"]),
            _probe_http("Runtime HTTP", "http://localhost.localstack.cloud:4566/_localstack/health"),
        ]
    if backend.name == "docker-compose":
        return [_probe_docker("Runtime docker", ["label=com.docker.compose.project"])]
    if backend.name == "kind-kubernetes":
        return [_probe_command("Runtime kind", ["kind", "get", "clusters"])]
    return [RuntimeProbe("Runtime", "not required", "This backend does not require a live sandbox runtime.")]


def _probe_docker(name: str, filters: list[str]) -> RuntimeProbe:
    details: list[str] = []
    for item_filter in filters:
        result = _run_probe_command(["docker", "ps", "--filter", item_filter, "--format", "{{.Names}}"])
        if result.returncode != 0:
            return RuntimeProbe(name, "unavailable", _clean_probe_error(result))
        if result.stdout.strip():
            details.extend(line.strip() for line in result.stdout.splitlines() if line.strip())
    if details:
        return RuntimeProbe(name, "running", ", ".join(sorted(set(details))))
    return RuntimeProbe(name, "not found", "No matching running container was found.")


def _probe_http(name: str, url: str) -> RuntimeProbe:
    try:
        response = requests.get(url, timeout=2)
    except requests.RequestException as error:
        return RuntimeProbe(name, "unreachable", str(error))
    if response.ok:
        return RuntimeProbe(name, "reachable", f"{url} returned HTTP {response.status_code}")
    return RuntimeProbe(name, "unhealthy", f"{url} returned HTTP {response.status_code}")


def _probe_command(name: str, command: list[str]) -> RuntimeProbe:
    result = _run_probe_command(command)
    if result.returncode == 0:
        detail = result.stdout.strip() or "command completed"
        return RuntimeProbe(name, "available", detail)
    return RuntimeProbe(name, "unavailable", _clean_probe_error(result))


def _run_probe_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, text=True, capture_output=True, check=False, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        return subprocess.CompletedProcess(command, 1, "", str(error))


def _clean_probe_error(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stderr or result.stdout or "probe failed").strip()
