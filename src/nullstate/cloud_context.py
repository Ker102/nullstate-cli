from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CLOUD_CONTEXT_SCHEMA_ID = "https://schemas.nullstate.dev/cloud-context.schema.json"
CLOUD_CONTEXT_SCHEMA_VERSION = 1
SENSITIVE_CLASSIFICATIONS = {"confidential", "restricted", "secret", "sensitive", "pii", "phi"}


def load_cloud_context(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid cloud context JSON in {path}: {error.msg} at line {error.lineno}, column {error.colno}.") from error
    except OSError as error:
        raise ValueError(f"Unable to read cloud context {path}: {error}") from error
    errors = validate_cloud_context(payload)
    if errors:
        raise ValueError("Invalid cloud context: " + "; ".join(errors))
    return payload


def validate_cloud_context(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["cloud context must be an object"]
    if payload.get("$schema") != CLOUD_CONTEXT_SCHEMA_ID:
        errors.append("$schema must reference the nullstate cloud-context schema")
    if payload.get("schema_version") != CLOUD_CONTEXT_SCHEMA_VERSION:
        errors.append(f"schema_version must be {CLOUD_CONTEXT_SCHEMA_VERSION}")
    scope = payload.get("scope")
    if not isinstance(scope, dict) or scope.get("mode") != "read-only":
        errors.append("scope.mode must be read-only")
    providers = payload.get("providers")
    if not isinstance(providers, list) or not providers:
        errors.append("providers must include at least one provider context")
    elif provider_errors := _validate_providers(providers):
        errors.extend(provider_errors)
    return errors


def build_context_summary(payload: dict[str, Any]) -> dict[str, Any]:
    providers = payload.get("providers") or []
    provider_names = sorted({str(provider.get("name")) for provider in providers if provider.get("name")})
    accounts = [account for provider in providers for account in provider.get("accounts", []) if isinstance(account, dict)]
    identities = [identity for provider in providers for identity in provider.get("identities", []) if isinstance(identity, dict)]
    resources = [resource for provider in providers for resource in provider.get("resources", []) if isinstance(resource, dict)]
    public_resources = [resource for resource in resources if resource.get("public") is True]
    sensitive_resources = [
        resource
        for resource in resources
        if str(resource.get("data_classification", "")).lower() in SENSITIVE_CLASSIFICATIONS
    ]
    return {
        "schema_version": 1,
        "mode": (payload.get("scope") or {}).get("mode"),
        "providers": provider_names,
        "provider_count": len(provider_names),
        "account_count": len(accounts),
        "identity_count": len(identities),
        "resource_count": len(resources),
        "public_resource_count": len(public_resources),
        "sensitive_resource_count": len(sensitive_resources),
        "public_resources": sorted(str(resource.get("id")) for resource in public_resources if resource.get("id")),
        "sensitive_resources": sorted(str(resource.get("id")) for resource in sensitive_resources if resource.get("id")),
    }


def _validate_providers(providers: list[Any]) -> list[str]:
    errors: list[str] = []
    for index, provider in enumerate(providers):
        if not isinstance(provider, dict):
            errors.append(f"providers[{index}] must be an object")
            continue
        if not isinstance(provider.get("name"), str) or not provider.get("name"):
            errors.append(f"providers[{index}].name is required")
        for field_name in ("accounts", "identities", "resources"):
            if not isinstance(provider.get(field_name), list):
                errors.append(f"providers[{index}].{field_name} must be a list")
    return errors
