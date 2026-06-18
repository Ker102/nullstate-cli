from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__
from .bundle import BUNDLE_FILENAME, build_run_bundle, write_run_bundle


UPLOAD_PLAN_SCHEMA_VERSION = 1
UPLOAD_PLAN_SCHEMA_ID = "https://schemas.nullstate.dev/upload-plan.schema.json"
UPLOAD_PLAN_FILENAME = "upload-plan.json"
DEFAULT_UPLOAD_ENDPOINT = "https://api.nullstate.dev/v1/runs"
DEFAULT_UPLOAD_TOKEN_ENV = "NULLSTATE_CLOUD_TOKEN"


def write_upload_plan(
    run_dir: Path,
    *,
    endpoint: str,
    token_env: str = DEFAULT_UPLOAD_TOKEN_ENV,
) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    bundle = write_run_bundle(run_dir)
    bundle_path = run_dir / BUNDLE_FILENAME
    plan = build_upload_plan(
        run_dir,
        bundle=bundle,
        bundle_path=bundle_path,
        endpoint=endpoint,
        token_env=token_env,
    )
    errors = validate_upload_plan(plan)
    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"Invalid upload plan: {joined}")
    (run_dir / UPLOAD_PLAN_FILENAME).write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return plan


def build_upload_plan(
    run_dir: Path,
    *,
    bundle: dict[str, Any] | None = None,
    bundle_path: Path | None = None,
    endpoint: str,
    token_env: str,
) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    resolved_bundle = bundle or build_run_bundle(run_dir)
    resolved_bundle_path = bundle_path or run_dir / BUNDLE_FILENAME
    artifacts = resolved_bundle.get("artifacts") if isinstance(resolved_bundle, dict) else []
    artifact_count = len(artifacts) if isinstance(artifacts, list) else 0
    return {
        "$schema": UPLOAD_PLAN_SCHEMA_ID,
        "schema_version": UPLOAD_PLAN_SCHEMA_VERSION,
        "product": "nullstate",
        "product_version": __version__,
        "generated_at": datetime.now(UTC).isoformat(),
        "dry_run": True,
        "endpoint": endpoint,
        "method": "POST",
        "run": {
            "id": str((resolved_bundle.get("run") or {}).get("id") or run_dir.name),
            "scenario": (resolved_bundle.get("run") or {}).get("scenario"),
            "target": (resolved_bundle.get("run") or {}).get("target"),
            "verdict": (resolved_bundle.get("run") or {}).get("verdict"),
        },
        "bundle": {
            "path": resolved_bundle_path.relative_to(run_dir).as_posix(),
            "schema_version": resolved_bundle.get("schema_version"),
            "sha256": _sha256(resolved_bundle_path),
            "artifact_count": artifact_count,
        },
        "auth": {
            "token_env": token_env,
            "token_present": bool(os.getenv(token_env)),
            "token_value_included": False,
        },
        "preflight": {
            "scrub": _build_scrub_preflight(run_dir),
        },
        "notes": "Dry run only. No network request was sent and token values are never written.",
    }


def validate_upload_plan(plan: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(plan, dict):
        return ["upload plan must be an object"]

    if plan.get("$schema") != UPLOAD_PLAN_SCHEMA_ID:
        errors.append("$schema must reference the nullstate upload-plan schema")
    if plan.get("schema_version") != UPLOAD_PLAN_SCHEMA_VERSION:
        errors.append(f"schema_version must be {UPLOAD_PLAN_SCHEMA_VERSION}")
    if plan.get("product") != "nullstate":
        errors.append("product must be nullstate")
    if not isinstance(plan.get("generated_at"), str) or not plan.get("generated_at"):
        errors.append("generated_at is required")
    if plan.get("dry_run") is not True:
        errors.append("dry_run must be true")
    if not isinstance(plan.get("endpoint"), str) or not plan.get("endpoint"):
        errors.append("endpoint is required")
    if plan.get("method") != "POST":
        errors.append("method must be POST")

    run = plan.get("run")
    if not isinstance(run, dict):
        errors.append("run must be an object")
        errors.append("run.id is required")
    elif not run.get("id"):
        errors.append("run.id is required")

    bundle = plan.get("bundle")
    if not isinstance(bundle, dict):
        errors.append("bundle must be an object")
        errors.append("bundle.path is required")
        errors.append("bundle.sha256 is required")
    else:
        if not bundle.get("path"):
            errors.append("bundle.path is required")
        if bundle.get("schema_version") is None:
            errors.append("bundle.schema_version is required")
        sha256 = bundle.get("sha256")
        if not isinstance(sha256, str) or len(sha256) != 64 or any(char not in "0123456789abcdef" for char in sha256):
            errors.append("bundle.sha256 is required")
        if not isinstance(bundle.get("artifact_count"), int):
            errors.append("bundle.artifact_count must be an integer")

    auth = plan.get("auth")
    if not isinstance(auth, dict):
        errors.append("auth must be an object")
        errors.append("auth.token_env is required")
        errors.append("auth.token_value_included must be false")
    else:
        if not auth.get("token_env"):
            errors.append("auth.token_env is required")
        if not isinstance(auth.get("token_present"), bool):
            errors.append("auth.token_present must be a boolean")
        if auth.get("token_value_included") is not False:
            errors.append("auth.token_value_included must be false")

    preflight = plan.get("preflight")
    if not isinstance(preflight, dict):
        errors.append("preflight must be an object")
        errors.append("preflight.scrub must be an object")
    elif not isinstance(preflight.get("scrub"), dict):
        errors.append("preflight.scrub must be an object")

    return errors


def _build_scrub_preflight(run_dir: Path) -> dict[str, Any]:
    report_path = run_dir / "scrub-report.json"
    if report_path.is_file():
        return {
            "status": "scrubbed",
            "scrub_report_present": True,
            "scrub_report_path": report_path.relative_to(run_dir).as_posix(),
            "upload_recommended": True,
            "warnings": [],
        }
    return {
        "status": "not_performed",
        "scrub_report_present": False,
        "upload_recommended": False,
        "warnings": [
            "Run has not been scrubbed. Run nullstate scrub before sharing or future cloud upload.",
        ],
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
