from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    name: str
    backend: str
    mode: str
    iac_targets: tuple[str, ...]
    status: str
    evidence_level: str
    evidence_summary: str
    risk: str
    description: str


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        name="azure-public-blob",
        backend="localstack-azure",
        mode="executable",
        iac_targets=("Terraform AzureRM",),
        status="offline deterministic demo available; live LocalStack Azure validation blocked by emulator entitlement",
        evidence_level="offline-deterministic",
        evidence_summary="Static IaC detection, remediation, manifest-backed probe generation, and offline report evidence are implemented; live Azure emulator proof is pending.",
        risk="Anonymous Azure Blob reads",
        description="Detect and remediate an Azure Blob container with public container/blob access.",
    ),
    Scenario(
        name="aws-public-s3",
        backend="localstack-aws",
        mode="executable",
        iac_targets=("Terraform AWS",),
        status="live LocalStack demo available",
        evidence_level="live-validated",
        evidence_summary="LocalStack AWS S3 deployment and constrained anonymous object-read probe are validated before and after remediation.",
        risk="Public S3 bucket reads",
        description="Detect and remediate an S3 bucket with public ACL or public access block disabled.",
    ),
    Scenario(
        name="k8s-privileged-pod",
        backend="kind-kubernetes",
        mode="executable",
        iac_targets=("Kubernetes YAML", "Helm", "Kustomize"),
        status="offline demo available; live kind execution pending",
        evidence_level="scaffolded",
        evidence_summary="Offline deterministic detection and remediation flow is available; live kind cluster probing is not implemented yet.",
        risk="Privileged container escape path",
        description="Detect and remediate privileged pods, hostPath mounts, and unsafe securityContext fields.",
    ),
    Scenario(
        name="compose-exposed-admin",
        backend="docker-compose",
        mode="digital-twin",
        iac_targets=("Docker Compose",),
        status="offline demo available; live Docker probe pending",
        evidence_level="scaffolded",
        evidence_summary="Offline deterministic detection and remediation flow is available; live container/network probing is not implemented yet.",
        risk="Public admin service exposure",
        description="Detect and remediate admin services bound to broad host interfaces.",
    ),
    Scenario(
        name="onprem-ssh-password",
        backend="microvm-onprem",
        mode="digital-twin",
        iac_targets=("Ansible", "cloud-init", "libvirt Terraform", "Proxmox Terraform"),
        status="offline demo available; microVM digital twin pending",
        evidence_level="scaffolded",
        evidence_summary="Offline deterministic detection and remediation flow is available; microVM digital-twin execution is not implemented yet.",
        risk="Password SSH and broad management access",
        description="Model an on-prem VM baseline and detect password SSH or broad management ingress.",
    ),
    Scenario(
        name="generic-plan-review",
        backend="plan-only",
        mode="plan-only",
        iac_targets=("Terraform JSON", "OpenTofu JSON", "static IaC exports"),
        status="available",
        evidence_level="plan-only",
        evidence_summary="Static plan/configuration review is available; no executable sandbox or runtime exploit probe is attempted.",
        risk="Unsupported provider review",
        description="Run plan-only analysis and report attack hypotheses when no executable sandbox exists.",
    ),
)


def list_scenarios() -> list[Scenario]:
    return list(SCENARIOS)


def get_scenario(name: str) -> Scenario:
    for scenario in SCENARIOS:
        if scenario.name == name:
            return scenario
    known = ", ".join(scenario.name for scenario in SCENARIOS)
    raise KeyError(f"Unknown scenario {name!r}. Known scenarios: {known}")
