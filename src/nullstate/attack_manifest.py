from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def write_attack_manifest(
    path: Path,
    *,
    scenario_name: str,
    backend_name: str,
    target_url: str,
    workspace_dir: Path,
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "scenario": scenario_name,
        "backend": backend_name,
        "target_url": target_url,
        "resources": _resource_hints(scenario_name, workspace_dir),
    }
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _resource_hints(scenario_name: str, workspace_dir: Path) -> dict[str, str]:
    terraform_text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(workspace_dir.glob("*.tf")))
    if scenario_name == "aws-public-s3":
        bucket_name = _tfstate_attribute(workspace_dir, "aws_s3_bucket", "public_logs", ("bucket", "id"))
        object_key = _tfstate_attribute(workspace_dir, "aws_s3_object", "evidence", ("key",))
        hints = {
            "bucket_name": bucket_name,
            "bucket_hint": _first_assignment(terraform_text, "bucket") or _first_assignment(terraform_text, "bucket_prefix"),
            "object_key": object_key or _first_assignment(terraform_text, "key") or "evidence.txt",
        }
        return {key: value for key, value in hints.items() if value}
    if scenario_name == "azure-public-blob":
        storage_account_name = _tfstate_attribute(workspace_dir, "azurerm_storage_account", "demo", ("name",))
        container_name = _tfstate_attribute(workspace_dir, "azurerm_storage_container", "secrets", ("name",))
        blob_name = _tfstate_attribute(workspace_dir, "azurerm_storage_blob", "evidence", ("name",))
        hints = {
            "storage_account_name": storage_account_name,
            "storage_account_hint": _first_assignment(terraform_text, "name", resource_type="azurerm_storage_account"),
            "container_name": container_name or _first_assignment(terraform_text, "name", resource_type="azurerm_storage_container"),
            "blob_name": blob_name or _first_assignment(terraform_text, "name", resource_type="azurerm_storage_blob") or "evidence.txt",
        }
        return {key: value for key, value in hints.items() if value}
    return {}


def _tfstate_attribute(
    workspace_dir: Path,
    resource_type: str,
    resource_name: str,
    candidate_keys: tuple[str, ...],
) -> str | None:
    state_path = workspace_dir / "terraform.tfstate"
    if not state_path.is_file():
        return None
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    for resource in payload.get("resources") or []:
        if resource.get("type") != resource_type or resource.get("name") != resource_name:
            continue
        for instance in resource.get("instances") or []:
            attributes = instance.get("attributes") or {}
            for key in candidate_keys:
                value = attributes.get(key)
                if isinstance(value, str) and value:
                    return value
    return None


def _first_assignment(text: str, key: str, *, resource_type: str | None = None) -> str | None:
    search_text = text
    if resource_type:
        resource_body = _first_resource_body(text, resource_type)
        if resource_body is None:
            return None
        search_text = resource_body
    match = re.search(rf"^\s*{re.escape(key)}\s*=\s*\"([^\"]+)\"", search_text, re.MULTILINE)
    return match.group(1) if match else None


def _first_resource_body(text: str, resource_type: str) -> str | None:
    pattern = re.compile(rf'resource\s+"{re.escape(resource_type)}"\s+"[^"]+"\s*\{{', re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return None
    closing = _find_matching_brace(text, match.end() - 1)
    if closing == -1:
        return None
    return text[match.end() : closing]


def _find_matching_brace(text: str, opening_brace_index: int) -> int:
    depth = 0
    in_string = False
    escaped = False
    for index in range(opening_brace_index, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    return -1
