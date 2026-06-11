from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


POLICY_SCHEMA_VERSION = 1
DEFAULT_POLICY_FILENAME = "nullstate-policy.json"
DEFAULT_ALLOWED_TARGET_CLASSIFICATIONS = {"offline", "local", "local-http"}
DEFAULT_ALLOWED_COMMAND_POLICY_IDS = {"generated-attack-script-v1"}


@dataclass(frozen=True)
class AttackPolicy:
    allowed_target_classifications: set[str]
    allowed_command_policy_ids: set[str]


def default_policy_payload() -> dict[str, Any]:
    return {
        "schema_version": POLICY_SCHEMA_VERSION,
        "allowed_target_classifications": sorted(DEFAULT_ALLOWED_TARGET_CLASSIFICATIONS),
        "allowed_command_policy_ids": sorted(DEFAULT_ALLOWED_COMMAND_POLICY_IDS),
        "notes": "Controls constrained red-tool execution. This does not grant arbitrary shell access.",
    }


def write_default_policy(path: Path) -> dict[str, Any]:
    payload = default_policy_payload()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def load_attack_policy(path: Path | None) -> AttackPolicy | None:
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return AttackPolicy(
        allowed_target_classifications=set(_string_list(payload, "allowed_target_classifications")),
        allowed_command_policy_ids=set(_string_list(payload, "allowed_command_policy_ids")),
    )


def enforce_attack_policy(
    policy: AttackPolicy | None,
    *,
    target_classification: str,
    command_policy_id: str,
) -> None:
    if policy is None:
        return
    if target_classification not in policy.allowed_target_classifications:
        raise ValueError(f"Attack target classification {target_classification!r} is not allowed by policy.")
    if command_policy_id not in policy.allowed_command_policy_ids:
        raise ValueError(f"Attack command policy {command_policy_id!r} is not allowed by policy.")


def _string_list(payload: dict[str, Any], key: str) -> list[str]:
    values = payload.get(key)
    if not isinstance(values, list):
        raise ValueError(f"Policy field {key!r} must be a list.")
    return [str(value) for value in values]
