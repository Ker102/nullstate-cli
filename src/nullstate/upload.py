from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .bundle import BUNDLE_FILENAME, build_run_bundle, write_run_bundle


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
        "schema_version": 1,
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
        "notes": "Dry run only. No network request was sent and token values are never written.",
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
