from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


AGENT_MANIFEST_SCHEMA_ID = "https://schemas.nullstate.dev/external-agent-manifest.schema.json"
AGENT_MANIFEST_SCHEMA_VERSION = 1
SENSITIVE_DATA_CLASSIFICATIONS = {
    "confidential",
    "restricted",
    "secret",
    "sensitive",
    "pii",
    "phi",
}
HIGH_RISK_ACTION_TOKENS = {
    "delete",
    "write",
    "put",
    "passrole",
    "assumerole",
    "owner",
    "administrator",
    "contributor",
    "*",
}


def load_agent_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid external agent manifest JSON in {path}: {error.msg} at line {error.lineno}, column {error.colno}."
        ) from error
    except OSError as error:
        raise ValueError(f"Unable to read external agent manifest {path}: {error}") from error
    errors = validate_agent_manifest(payload)
    if errors:
        raise ValueError("Invalid external agent manifest: " + "; ".join(errors))
    return payload


def validate_agent_manifest(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["external agent manifest must be an object"]
    if payload.get("$schema") != AGENT_MANIFEST_SCHEMA_ID:
        errors.append("$schema must reference the nullstate external-agent-manifest schema")
    if payload.get("schema_version") != AGENT_MANIFEST_SCHEMA_VERSION:
        errors.append(f"schema_version must be {AGENT_MANIFEST_SCHEMA_VERSION}")

    agent = payload.get("agent")
    if not isinstance(agent, dict):
        errors.append("agent must be an object")
        errors.append("agent.id is required")
    elif not _non_empty_string(agent.get("id")):
        errors.append("agent.id is required")

    runtime = payload.get("runtime")
    if not isinstance(runtime, dict):
        errors.append("runtime must be an object")
        errors.append("runtime.environment is required")
    elif not _non_empty_string(runtime.get("environment")):
        errors.append("runtime.environment is required")

    identities = payload.get("identities")
    if not isinstance(identities, list) or not identities:
        errors.append("identities must include at least one identity")
    elif identity_errors := _validate_identities(identities):
        errors.extend(identity_errors)

    evidence = payload.get("posture_evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("posture_evidence must include at least one evidence claim")
    elif evidence_errors := _validate_evidence(evidence):
        errors.extend(evidence_errors)

    resources = payload.get("reachable_resources")
    if not isinstance(resources, list):
        errors.append("reachable_resources must be a list")
    elif resource_errors := _validate_resources(resources):
        errors.extend(resource_errors)

    return errors


def build_posture_report(payload: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    observed_now = now or datetime.now(UTC)
    findings: list[dict[str, str]] = []
    unknown_claims: list[str] = []
    stale_claims: list[str] = []
    failed_claims: list[str] = []
    evidence_classes: dict[str, int] = {}

    for claim in payload.get("posture_evidence") or []:
        claim_name = str(claim.get("claim") or "unknown")
        evidence_class = str(claim.get("evidence_class") or "unknown")
        evidence_classes[evidence_class] = evidence_classes.get(evidence_class, 0) + 1

        if evidence_class == "unknown" or claim.get("status") == "unknown":
            unknown_claims.append(claim_name)
            findings.append(
                {
                    "claim": claim_name,
                    "severity": "medium",
                    "detail": f"{claim_name} has unknown evidence and cannot be treated as secure.",
                }
            )
        if claim.get("status") == "fail":
            failed_claims.append(claim_name)
            findings.append(
                {
                    "claim": claim_name,
                    "severity": "high",
                    "detail": f"{claim_name} reported a failing runtime posture signal.",
                }
            )
        expires_at = _parse_datetime(claim.get("expires_at"))
        if expires_at is not None and expires_at < observed_now:
            stale_claims.append(claim_name)
            findings.append(
                {
                    "claim": claim_name,
                    "severity": "high",
                    "detail": f"{claim_name} evidence expired at {expires_at.isoformat()}.",
                }
            )

    status = "pass"
    if failed_claims or stale_claims:
        status = "fail"
    elif unknown_claims:
        status = "needs-review"

    return {
        "schema_version": 1,
        "agent_id": (payload.get("agent") or {}).get("id"),
        "runtime_environment": (payload.get("runtime") or {}).get("environment"),
        "status": status,
        "passed": status == "pass",
        "evidence_count": len(payload.get("posture_evidence") or []),
        "evidence_classes": evidence_classes,
        "unknown_claims": sorted(set(unknown_claims)),
        "stale_claims": sorted(set(stale_claims)),
        "failed_claims": sorted(set(failed_claims)),
        "findings": findings,
    }


def build_blast_radius_report(payload: dict[str, Any]) -> dict[str, Any]:
    identities = payload.get("identities") or []
    resources = payload.get("reachable_resources") or []
    identity_types = sorted({str(identity.get("type")) for identity in identities if identity.get("type")})
    permissions = sorted(
        {
            str(permission)
            for identity in identities
            for permission in identity.get("permissions", [])
            if isinstance(permission, str) and permission
        }
    )
    resource_actions = sorted(
        {
            str(action)
            for resource in resources
            for action in resource.get("actions", [])
            if isinstance(action, str) and action
        }
    )
    sensitive_resources = sorted(
        {
            str(resource.get("id"))
            for resource in resources
            if str(resource.get("data_classification", "")).lower() in SENSITIVE_DATA_CLASSIFICATIONS
        }
    )
    all_actions = sorted(set(permissions) | set(resource_actions))
    high_risk_actions = [action for action in all_actions if _is_high_risk_action(action)]
    attack_paths = _attack_paths(sensitive_resources, high_risk_actions, identity_types)

    return {
        "schema_version": 1,
        "agent_id": (payload.get("agent") or {}).get("id"),
        "identity_count": len(identities),
        "identity_types": identity_types,
        "permission_count": len(permissions),
        "permissions": permissions,
        "reachable_resource_count": len(resources),
        "sensitive_resource_count": len(sensitive_resources),
        "sensitive_resources": sensitive_resources,
        "high_risk_actions": high_risk_actions,
        "attack_paths": attack_paths,
    }


def _validate_identities(identities: list[Any]) -> list[str]:
    errors: list[str] = []
    for index, identity in enumerate(identities):
        if not isinstance(identity, dict):
            errors.append(f"identities[{index}] must be an object")
            continue
        for field_name in ("id", "type", "provider"):
            if not _non_empty_string(identity.get(field_name)):
                errors.append(f"identities[{index}].{field_name} is required")
        permissions = identity.get("permissions")
        if not isinstance(permissions, list) or any(not _non_empty_string(value) for value in permissions):
            errors.append(f"identities[{index}].permissions must be a list of non-empty strings")
    return errors


def _validate_evidence(evidence: list[Any]) -> list[str]:
    errors: list[str] = []
    for index, claim in enumerate(evidence):
        if not isinstance(claim, dict):
            errors.append(f"posture_evidence[{index}] must be an object")
            continue
        for field_name in ("claim", "status", "evidence_class", "observed_at"):
            if not _non_empty_string(claim.get(field_name)):
                errors.append(f"posture_evidence[{index}].{field_name} is required")
        if _non_empty_string(claim.get("observed_at")) and _parse_datetime(claim.get("observed_at")) is None:
            errors.append(f"posture_evidence[{index}].observed_at must be an ISO datetime")
        if _non_empty_string(claim.get("expires_at")) and _parse_datetime(claim.get("expires_at")) is None:
            errors.append(f"posture_evidence[{index}].expires_at must be an ISO datetime")
    return errors


def _validate_resources(resources: list[Any]) -> list[str]:
    errors: list[str] = []
    for index, resource in enumerate(resources):
        if not isinstance(resource, dict):
            errors.append(f"reachable_resources[{index}] must be an object")
            continue
        for field_name in ("id", "provider", "data_classification"):
            if not _non_empty_string(resource.get(field_name)):
                errors.append(f"reachable_resources[{index}].{field_name} is required")
        actions = resource.get("actions")
        if not isinstance(actions, list) or any(not _non_empty_string(value) for value in actions):
            errors.append(f"reachable_resources[{index}].actions must be a list of non-empty strings")
    return errors


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _is_high_risk_action(action: str) -> bool:
    normalized = action.lower().replace("_", "").replace("-", "")
    return any(token in normalized for token in HIGH_RISK_ACTION_TOKENS)


def _attack_paths(sensitive_resources: list[str], high_risk_actions: list[str], identity_types: list[str]) -> list[str]:
    paths: list[str] = []
    if sensitive_resources:
        paths.append("read_sensitive_data")
    if high_risk_actions:
        paths.append("privilege_escalation_or_write")
    if "delegated-user" in identity_types:
        paths.append("delegated_user_authority")
    return paths
