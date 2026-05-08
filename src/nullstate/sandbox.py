from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Literal


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

    def up_commands(self) -> list[list[str]]:
        if self.name == "localstack-azure":
            return [
                ["docker", "pull", "localstack/localstack-azure-alpha"],
                [
                    "docker",
                    "run",
                    "--rm",
                    "-it",
                    "-p",
                    "4566:4566",
                    "-v",
                    "/var/run/docker.sock:/var/run/docker.sock",
                    "-v",
                    "~/.localstack/volume:/var/lib/localstack",
                    "-e",
                    "LOCALSTACK_AUTH_TOKEN=${LOCALSTACK_AUTH_TOKEN:?}",
                    "localstack/localstack-azure-alpha",
                ],
            ]
        if self.name == "localstack-aws":
            return [
                ["docker", "pull", "localstack/localstack"],
                ["docker", "run", "--rm", "-it", "-p", "4566:4566", "localstack/localstack"],
            ]
        if self.name == "kind-kubernetes":
            return [["kind", "create", "cluster", "--name", "nullstate"]]
        if self.name == "docker-compose":
            return [["docker", "compose", "up", "-d"]]
        if self.name == "microvm-onprem":
            return [["nullstate", "sandbox", "plan", "microvm-onprem"]]
        return []

    def down_commands(self) -> list[list[str]]:
        if self.name in {"localstack-azure", "localstack-aws"}:
            return [["docker", "ps", "--filter", "ancestor=localstack", "--format", "{{.ID}}"]]
        if self.name == "kind-kubernetes":
            return [["kind", "delete", "cluster", "--name", "nullstate"]]
        if self.name == "docker-compose":
            return [["docker", "compose", "down"]]
        return []


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
        requirements=["Docker", "Terraform", "AWS provider tooling"],
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
