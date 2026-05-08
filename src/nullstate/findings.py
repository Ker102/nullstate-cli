from __future__ import annotations

from dataclasses import asdict, dataclass
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


def _iter_resources(module: dict[str, Any]) -> list[dict[str, Any]]:
    resources = list(module.get("resources") or [])
    for child in module.get("child_modules") or []:
        resources.extend(_iter_resources(child))
    return resources


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
