from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


POLICY_SCHEMA_VERSION = 1
POLICY_SCHEMA_ID = "https://schemas.nullstate.dev/nullstate-policy.schema.json"
DEFAULT_POLICY_FILENAME = "nullstate-policy.json"
DEFAULT_ALLOWED_TARGET_CLASSIFICATIONS = {"offline", "local", "local-http"}
DEFAULT_ALLOWED_TARGET_HOSTS = {
    "*.localhost.localstack.cloud",
    "127.0.0.1",
    "::1",
    "localhost",
    "localhost.localstack.cloud",
}
DEFAULT_ALLOWED_COMMAND_POLICY_IDS = {"generated-attack-script-v1"}
DEFAULT_ALLOWED_ATTACK_SCRIPT_ARGS = {"--manifest", "--stage", "--target-url"}
DEFAULT_ALLOWED_STAGES = {"after", "before"}
DEFAULT_MAX_TIMEOUT_SECONDS = 30
DEFAULT_MAX_OUTPUT_BYTES = 12_000
POLICY_VALIDATION_FILENAME = "policy-validation.json"
DEFAULT_ALLOWED_SCENARIOS = {
    "aws-public-s3",
    "azure-public-blob",
    "compose-exposed-admin",
    "generic-plan-review",
    "k8s-privileged-pod",
    "onprem-ssh-password",
}
DEFAULT_ALLOWED_BACKENDS = {
    "docker-compose",
    "kind-kubernetes",
    "localstack-aws",
    "localstack-azure",
    "microvm-onprem",
    "plan-only",
}


@dataclass(frozen=True)
class AttackPolicy:
    allowed_target_classifications: set[str]
    allowed_command_policy_ids: set[str]
    allowed_target_hosts: set[str] | None = None
    allowed_scenarios: set[str] | None = None
    allowed_backends: set[str] | None = None
    allowed_stages: set[str] | None = None
    allowed_attack_script_args: set[str] | None = None
    max_timeout_seconds: int | None = None
    max_output_bytes: int | None = None


def default_policy_payload() -> dict[str, Any]:
    return {
        "$schema": POLICY_SCHEMA_ID,
        "schema_version": POLICY_SCHEMA_VERSION,
        "preset": "default",
        "allowed_target_classifications": sorted(DEFAULT_ALLOWED_TARGET_CLASSIFICATIONS),
        "allowed_target_hosts": sorted(DEFAULT_ALLOWED_TARGET_HOSTS),
        "allowed_command_policy_ids": sorted(DEFAULT_ALLOWED_COMMAND_POLICY_IDS),
        "allowed_scenarios": sorted(DEFAULT_ALLOWED_SCENARIOS),
        "allowed_backends": sorted(DEFAULT_ALLOWED_BACKENDS),
        "allowed_stages": sorted(DEFAULT_ALLOWED_STAGES),
        "allowed_attack_script_args": sorted(DEFAULT_ALLOWED_ATTACK_SCRIPT_ARGS),
        "max_timeout_seconds": DEFAULT_MAX_TIMEOUT_SECONDS,
        "max_output_bytes": DEFAULT_MAX_OUTPUT_BYTES,
        "notes": "Controls constrained red-tool execution. This does not grant arbitrary shell access.",
    }


def scenario_policy_payload(scenario_name: str, backend_name: str) -> dict[str, Any]:
    payload = default_policy_payload()
    payload["preset"] = f"scenario:{scenario_name}"
    payload["allowed_scenarios"] = [scenario_name]
    payload["allowed_backends"] = [backend_name]
    payload["notes"] = (
        "Controls constrained red-tool execution for one scenario/backend pair. "
        "This does not grant arbitrary shell access."
    )
    return payload


def write_default_policy(path: Path, *, scenario_name: str | None = None, backend_name: str | None = None) -> dict[str, Any]:
    payload = (
        scenario_policy_payload(scenario_name, backend_name)
        if scenario_name is not None and backend_name is not None
        else default_policy_payload()
    )
    errors = validate_policy_payload(payload)
    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"Invalid policy: {joined}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def write_policy_validation(path: Path, output_path: Path) -> dict[str, Any]:
    payload = build_policy_validation(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def build_policy_validation(path: Path) -> dict[str, Any]:
    try:
        policy = load_attack_policy(path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return {
            "schema_version": 1,
            "generated_at": datetime.now(UTC).isoformat(),
            "status": "invalid",
            "valid": False,
            "policy": {
                "path": str(path),
                "schema_version": _safe_schema_version(path),
                "fields": [],
            },
            "warnings": [],
            "error": str(error),
        }
    if policy is None:
        raise ValueError("Policy validation requires a policy path.")
    payload = _read_policy_payload(path)
    fields = sorted(key for key in payload if key != "notes")
    warnings = _policy_validation_warnings(policy)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "valid",
        "valid": True,
        "policy": {
            "path": str(path),
            "schema_version": payload.get("schema_version"),
            "fields": fields,
            "constrained_field_count": len(fields),
        },
        "warnings": warnings,
        "error": None,
    }


def load_attack_policy(path: Path | None) -> AttackPolicy | None:
    if path is None:
        return None
    payload = _read_policy_payload(path)
    return AttackPolicy(
        allowed_target_classifications=set(_string_list(payload, "allowed_target_classifications")),
        allowed_command_policy_ids=set(_string_list(payload, "allowed_command_policy_ids")),
        allowed_target_hosts=_optional_string_set(payload, "allowed_target_hosts"),
        allowed_scenarios=_optional_string_set(payload, "allowed_scenarios"),
        allowed_backends=_optional_string_set(payload, "allowed_backends"),
        allowed_stages=_optional_string_set(payload, "allowed_stages"),
        allowed_attack_script_args=_optional_string_set(payload, "allowed_attack_script_args"),
        max_timeout_seconds=_optional_positive_int(payload, "max_timeout_seconds"),
        max_output_bytes=_optional_positive_int(payload, "max_output_bytes"),
    )


def enforce_attack_policy(
    policy: AttackPolicy | None,
    *,
    target_classification: str,
    target_url: str | None = None,
    command_policy_id: str,
    scenario_name: str | None = None,
    backend_name: str | None = None,
    stage: str | None = None,
    attack_script_args: set[str] | None = None,
    timeout_seconds: int | None = None,
    max_output_bytes: int | None = None,
) -> None:
    if policy is None:
        return
    if target_classification not in policy.allowed_target_classifications:
        raise ValueError(f"Attack target classification {target_classification!r} is not allowed by policy.")
    if policy.allowed_target_hosts is not None:
        _enforce_target_host_policy(target_url, policy.allowed_target_hosts)
    if command_policy_id not in policy.allowed_command_policy_ids:
        raise ValueError(f"Attack command policy {command_policy_id!r} is not allowed by policy.")
    if policy.allowed_scenarios is not None and scenario_name not in policy.allowed_scenarios:
        raise ValueError(f"Attack scenario {scenario_name!r} is not allowed by policy.")
    if policy.allowed_backends is not None and backend_name not in policy.allowed_backends:
        raise ValueError(f"Attack backend {backend_name!r} is not allowed by policy.")
    if policy.allowed_stages is not None and stage not in policy.allowed_stages:
        raise ValueError(f"Attack stage {stage!r} is not allowed by policy.")
    if policy.allowed_attack_script_args is not None:
        requested_args = attack_script_args or set()
        denied_args = sorted(requested_args - policy.allowed_attack_script_args)
        if denied_args:
            raise ValueError(f"Attack script argument {denied_args[0]!r} is not allowed by policy.")
    if policy.max_timeout_seconds is not None and timeout_seconds is not None and timeout_seconds > policy.max_timeout_seconds:
        raise ValueError(
            f"Attack timeout {timeout_seconds} seconds exceeds policy maximum {policy.max_timeout_seconds} seconds."
        )
    if policy.max_output_bytes is not None and max_output_bytes is not None and max_output_bytes > policy.max_output_bytes:
        raise ValueError(
            f"Attack output limit {max_output_bytes} bytes exceeds policy maximum {policy.max_output_bytes} bytes."
        )


def validate_policy_payload(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["policy must be an object"]

    if payload.get("$schema") != POLICY_SCHEMA_ID:
        errors.append("$schema must reference the nullstate policy schema")
    if payload.get("schema_version") != POLICY_SCHEMA_VERSION:
        errors.append(f"schema_version must be {POLICY_SCHEMA_VERSION}")
    if not isinstance(payload.get("preset"), str) or not payload.get("preset"):
        errors.append("preset is required")

    list_fields = [
        "allowed_target_classifications",
        "allowed_target_hosts",
        "allowed_command_policy_ids",
        "allowed_scenarios",
        "allowed_backends",
        "allowed_stages",
        "allowed_attack_script_args",
    ]
    for field_name in list_fields:
        values = payload.get(field_name)
        if not isinstance(values, list):
            errors.append(f"{field_name} must be a list")
            continue
        for index, value in enumerate(values):
            if not isinstance(value, str) or not value:
                errors.append(f"{field_name}[{index}] must be a non-empty string")

    if not _is_positive_int(payload.get("max_timeout_seconds")):
        errors.append("max_timeout_seconds must be a positive integer")
    if not _is_positive_int(payload.get("max_output_bytes")):
        errors.append("max_output_bytes must be a positive integer")
    if "notes" in payload and not isinstance(payload.get("notes"), str):
        errors.append("notes must be a string")

    return errors


def _string_list(payload: dict[str, Any], key: str) -> list[str]:
    values = payload.get(key)
    if not isinstance(values, list):
        raise ValueError(f"Policy field {key!r} must be a list.")
    return [str(value) for value in values]


def _optional_string_set(payload: dict[str, Any], key: str) -> set[str] | None:
    if key not in payload:
        return None
    return set(_string_list(payload, key))


def _optional_positive_int(payload: dict[str, Any], key: str) -> int | None:
    if key not in payload:
        return None
    value = payload.get(key)
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"Policy field {key!r} must be a positive integer.")
    return value


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and value > 0


def _enforce_target_host_policy(target_url: str | None, allowed_target_hosts: set[str]) -> None:
    if target_url is None:
        raise ValueError("Attack target host is required for host allowlist policy enforcement.")
    parsed = urlparse(target_url)
    if parsed.scheme not in {"http", "https"}:
        return
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise ValueError("Attack target host is required for host allowlist policy enforcement.")
    if not _target_host_allowed(hostname, allowed_target_hosts):
        raise ValueError(f"Attack target host {hostname!r} is not allowed by policy.")


def _target_host_allowed(hostname: str, allowed_target_hosts: set[str]) -> bool:
    normalized_hosts = {host.lower() for host in allowed_target_hosts}
    if hostname in normalized_hosts:
        return True
    for pattern in normalized_hosts:
        if pattern.startswith("*.") and hostname.endswith(pattern[1:]):
            return True
    return False


def _read_policy_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Policy file must contain a JSON object.")
    return payload


def _safe_schema_version(path: Path) -> Any:
    try:
        payload = _read_policy_payload(path)
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    return payload.get("schema_version")


def _policy_validation_warnings(policy: AttackPolicy) -> list[str]:
    warnings = []
    optional_fields = {
        "allowed_scenarios": policy.allowed_scenarios,
        "allowed_backends": policy.allowed_backends,
        "allowed_target_hosts": policy.allowed_target_hosts,
        "allowed_stages": policy.allowed_stages,
        "allowed_attack_script_args": policy.allowed_attack_script_args,
        "max_timeout_seconds": policy.max_timeout_seconds,
        "max_output_bytes": policy.max_output_bytes,
    }
    for field_name, value in optional_fields.items():
        if value is None:
            warnings.append(f"Optional policy field {field_name!r} is omitted; that dimension is not constrained.")
    return warnings
