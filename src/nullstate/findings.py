from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


PUBLIC_ACCESS_TYPES = {"blob", "container"}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    resource_address: str
    summary: str
    evidence: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def find_public_blob_exposures(plan: dict[str, Any]) -> list[Finding]:
    resources = list(_iter_resources(plan.get("planned_values", {}).get("root_module", {})))
    storage_accounts = [resource for resource in resources if resource.get("type") == "azurerm_storage_account"]
    containers = [resource for resource in resources if resource.get("type") == "azurerm_storage_container"]

    findings: list[Finding] = []
    for container in containers:
        values = container.get("values") or {}
        access_type = str(values.get("container_access_type") or "private").lower()
        if access_type not in PUBLIC_ACCESS_TYPES:
            continue

        account_public_setting = _storage_public_setting(storage_accounts, values)
        evidence = [f"container_access_type is {access_type!r}"]
        if account_public_setting is True:
            evidence.append("storage account allows nested items to be public")
        elif account_public_setting is False:
            evidence.append("storage account blocks nested public items, but the container still requests public access")
        else:
            evidence.append("Storage account public nesting setting was not found in the plan")

        findings.append(
            Finding(
                rule_id="AZURE_STORAGE_PUBLIC_BLOB",
                severity="high",
                resource_address=str(container.get("address", "azurerm_storage_container.unknown")),
                summary="Azure Blob container allows anonymous reads.",
                evidence="; ".join(evidence),
                remediation=(
                    "Set azurerm_storage_container.container_access_type to \"private\" and "
                    "set azurerm_storage_account.allow_nested_items_to_be_public to false."
                ),
            )
        )
    return findings


def find_scenario_findings(scenario_name: str, workspace_dir: Path, plan: dict[str, Any]) -> list[Finding]:
    if scenario_name == "azure-public-blob":
        return find_public_blob_exposures(plan)
    if scenario_name == "aws-public-s3":
        return find_public_s3_exposures(plan)
    if scenario_name == "k8s-privileged-pod":
        return find_privileged_k8s_workloads(workspace_dir)
    if scenario_name == "compose-exposed-admin":
        return find_compose_public_admin_ports(workspace_dir)
    if scenario_name == "onprem-ssh-password":
        return find_onprem_ssh_password_login(workspace_dir)
    if scenario_name == "generic-plan-review":
        return find_generic_public_admin_ingress(plan)
    return []


def find_public_s3_exposures(plan: dict[str, Any]) -> list[Finding]:
    resources = list(_iter_resources(plan.get("planned_values", {}).get("root_module", {})))
    findings: list[Finding] = []
    for resource in resources:
        if resource.get("type") != "aws_s3_bucket_public_access_block":
            continue
        values = resource.get("values") or {}
        disabled_controls = [
            key
            for key in ("block_public_acls", "block_public_policy", "ignore_public_acls", "restrict_public_buckets")
            if values.get(key) is False
        ]
        if not disabled_controls:
            continue
        findings.append(
            Finding(
                rule_id="AWS_S3_PUBLIC_ACCESS_BLOCK_DISABLED",
                severity="high",
                resource_address=str(resource.get("address", "aws_s3_bucket_public_access_block.unknown")),
                summary="S3 public access block controls are disabled.",
                evidence="Disabled controls: " + ", ".join(disabled_controls),
                remediation="Set every aws_s3_bucket_public_access_block control to true.",
            )
        )
    return findings


def find_privileged_k8s_workloads(workspace_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    for yaml_file in _iac_files(workspace_dir, ("*.yaml", "*.yml")):
        text = yaml_file.read_text(encoding="utf-8")
        evidence: list[str] = []
        if "privileged: true" in text:
            evidence.append("container securityContext sets privileged: true")
        if "hostPath:" in text:
            evidence.append("pod mounts hostPath storage")
        if not evidence:
            continue
        findings.append(
            Finding(
                rule_id="K8S_PRIVILEGED_WORKLOAD",
                severity="critical",
                resource_address=yaml_file.name,
                summary="Kubernetes workload can access host-level privileges.",
                evidence="; ".join(evidence),
                remediation="Set privileged to false and replace hostPath with an isolated volume.",
            )
        )
    return findings


def find_compose_public_admin_ports(workspace_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    for compose_file in _iac_files(workspace_dir, ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml")):
        text = compose_file.read_text(encoding="utf-8")
        if "0.0.0.0:" not in text:
            continue
        findings.append(
            Finding(
                rule_id="COMPOSE_PUBLIC_ADMIN_PORT",
                severity="high",
                resource_address=compose_file.name,
                summary="Docker Compose admin service is bound to all host interfaces.",
                evidence="A published port uses 0.0.0.0, exposing the service beyond localhost.",
                remediation="Bind admin service ports to 127.0.0.1 or remove the host port.",
            )
        )
    return findings


def find_onprem_ssh_password_login(workspace_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    for config_file in _iac_files(workspace_dir, ("*.yaml", "*.yml", "*.cfg", "*.conf")):
        text = config_file.read_text(encoding="utf-8")
        evidence: list[str] = []
        if "PasswordAuthentication yes" in text:
            evidence.append("PasswordAuthentication yes")
        if "PermitRootLogin yes" in text:
            evidence.append("PermitRootLogin yes")
        if not evidence:
            continue
        findings.append(
            Finding(
                rule_id="ONPREM_SSH_PASSWORD_LOGIN",
                severity="high",
                resource_address=config_file.name,
                summary="On-prem SSH baseline enables password or root login.",
                evidence="; ".join(evidence),
                remediation="Disable SSH password authentication and root login in the baseline.",
            )
        )
    return findings


def find_generic_public_admin_ingress(plan: dict[str, Any]) -> list[Finding]:
    resources = list(_iter_resources(plan.get("planned_values", {}).get("root_module", {})))
    findings: list[Finding] = []
    for resource in resources:
        values = resource.get("values") or {}
        if not _contains_public_cidr(values) or not _contains_admin_port(values):
            continue
        findings.append(
            Finding(
                rule_id="GENERIC_PUBLIC_ADMIN_INGRESS",
                severity="medium",
                resource_address=str(resource.get("address", "generic.resource")),
                summary="Plan-only review found public ingress to an administrative port.",
                evidence="Resource contains 0.0.0.0/0 and an administrative port such as 22 or 3389.",
                remediation="Restrict source ranges to a private management CIDR or remove the administrative listener.",
            )
        )
    return findings


def _iter_resources(module: dict[str, Any]) -> list[dict[str, Any]]:
    resources = list(module.get("resources") or [])
    for child in module.get("child_modules") or []:
        resources.extend(_iter_resources(child))
    return resources


def _iac_files(workspace_dir: Path, patterns: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        files.extend(path for path in workspace_dir.glob(pattern) if path.is_file())
    return sorted(set(files))


def _contains_public_cidr(value: Any) -> bool:
    if isinstance(value, str):
        return value == "0.0.0.0/0" or value == "::/0"
    if isinstance(value, list):
        return any(_contains_public_cidr(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_public_cidr(item) for item in value.values())
    return False


def _contains_admin_port(value: Any) -> bool:
    if isinstance(value, int):
        return value in {22, 3389, 5985, 5986}
    if isinstance(value, str) and value.isdigit():
        return int(value) in {22, 3389, 5985, 5986}
    if isinstance(value, list):
        return any(_contains_admin_port(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_admin_port(item) for item in value.values())
    return False


def _storage_public_setting(storage_accounts: list[dict[str, Any]], container_values: dict[str, Any]) -> bool | None:
    storage_account_id = str(container_values.get("storage_account_id") or "").lower()
    storage_account_name = str(container_values.get("storage_account_name") or "").lower()

    for account in storage_accounts:
        values = account.get("values") or {}
        account_name = str(values.get("name") or "").lower()
        account_id = str(values.get("id") or "").lower()
        matches_id = account_id and storage_account_id and account_id == storage_account_id
        matches_name = account_name and (
            account_name == storage_account_name or account_name in storage_account_id
        )
        if matches_id or matches_name or len(storage_accounts) == 1:
            raw_setting = values.get("allow_nested_items_to_be_public")
            return True if raw_setting is None else bool(raw_setting)
    return None
