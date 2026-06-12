from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__


EVIDENCE_MANIFEST_SCHEMA_VERSION = 1
EVIDENCE_MANIFEST_FILENAME = "evidence-manifest.json"
EVIDENCE_VERIFICATION_FILENAME = "evidence-verification.json"


def write_evidence_manifest(
    run_dir: Path,
    output_path: Path | None = None,
    *,
    signing_key: str | None = None,
    signing_key_id: str | None = None,
) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    target = output_path or run_dir / EVIDENCE_MANIFEST_FILENAME
    payload = build_evidence_manifest(
        run_dir,
        output_path=target,
        signing_key=signing_key,
        signing_key_id=signing_key_id,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def verify_evidence_manifest(
    run_dir: Path,
    *,
    manifest_path: Path | None = None,
    output_path: Path | None = None,
    signing_key: str | None = None,
) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    source = manifest_path or run_dir / EVIDENCE_MANIFEST_FILENAME
    manifest = _read_json(source, default={})
    failures = _verify_manifest_identity(run_dir, manifest)
    signature_status, signature_failures = _verify_manifest_signature(manifest, signing_key=signing_key)
    failures.extend(signature_failures)
    failures.extend(_verify_manifest_artifacts(run_dir, manifest))
    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), list) else []
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "run": {
            "id": str((manifest.get("run") or {}).get("id") or run_dir.name),
            "path": str(run_dir),
            "scenario": (manifest.get("run") or {}).get("scenario"),
            "target": (manifest.get("run") or {}).get("target"),
        },
        "manifest": {
            "path": _manifest_display_path(run_dir, source),
            "schema_version": manifest.get("schema_version"),
            "hash_algorithm": (manifest.get("integrity") or {}).get("hash_algorithm"),
        },
        "signature": signature_status,
        "status": "failed" if failures else "passed",
        "checked_artifact_count": len(artifacts),
        "failure_count": len(failures),
        "failures": failures,
    }
    target = output_path or run_dir / EVIDENCE_VERIFICATION_FILENAME
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def build_evidence_manifest(
    run_dir: Path,
    *,
    output_path: Path | None = None,
    signing_key: str | None = None,
    signing_key_id: str | None = None,
) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    if not (run_dir / "report.md").is_file():
        raise ValueError(f"Run directory does not contain report.md: {run_dir}")

    events = _read_events(run_dir / "events.jsonl")
    attack_manifest = _read_json(run_dir / "attack-manifest.json", default={})
    artifacts = _artifact_inventory(run_dir, output_path=output_path)
    payload = {
        "schema_version": EVIDENCE_MANIFEST_SCHEMA_VERSION,
        "product": "nullstate",
        "product_version": __version__,
        "generated_at": datetime.now(UTC).isoformat(),
        "run": {
            "id": run_dir.name,
            "path": str(run_dir),
            "scenario": attack_manifest.get("scenario") or _event_data(events, "start", "scenario"),
            "target": attack_manifest.get("backend") or _event_data(events, "start", "target"),
            "offline": _event_data(events, "start", "offline"),
        },
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "integrity": {
            "hash_algorithm": "sha256",
            "workspace_included": False,
            "excluded_paths": [
                "workspace/",
                ".terraform/",
                "__pycache__/",
                EVIDENCE_MANIFEST_FILENAME,
                EVIDENCE_VERIFICATION_FILENAME,
            ],
        },
        "signing": {
            "status": "unsigned",
            "algorithm": None,
            "signature": None,
            "notes": "This manifest records artifact integrity hashes. Cryptographic signing is not enabled yet.",
        },
    }
    if signing_key is not None:
        _sign_manifest(payload, signing_key=signing_key, key_id=signing_key_id)
    return payload


def _artifact_inventory(run_dir: Path, *, output_path: Path | None) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    excluded_dirs = {"workspace", ".terraform", "__pycache__"}
    excluded_files = {EVIDENCE_MANIFEST_FILENAME, EVIDENCE_VERIFICATION_FILENAME}
    if output_path is not None:
        try:
            excluded_files.add(output_path.resolve().relative_to(run_dir).as_posix())
        except ValueError:
            pass
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(run_dir).parts
        if any(part in excluded_dirs for part in relative_parts):
            continue
        relative = path.relative_to(run_dir).as_posix()
        if relative in excluded_files:
            continue
        artifacts.append(
            {
                "path": relative,
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return artifacts


def _verify_manifest_artifacts(run_dir: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    integrity = manifest.get("integrity") or {}
    if integrity.get("hash_algorithm") != "sha256":
        return [
            {
                "path": None,
                "reason": "unsupported_hash_algorithm",
                "expected_hash_algorithm": integrity.get("hash_algorithm"),
                "actual_hash_algorithm": "sha256",
            }
        ]

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        return [{"path": None, "reason": "invalid_artifacts"}]

    for item in artifacts:
        if not isinstance(item, dict):
            failures.append({"path": None, "reason": "invalid_artifact_entry"})
            continue
        relative = item.get("path")
        if not isinstance(relative, str) or not relative:
            failures.append({"path": None, "reason": "invalid_artifact_path"})
            continue
        artifact_path = (run_dir / relative).resolve()
        try:
            artifact_path.relative_to(run_dir)
        except ValueError:
            failures.append({"path": relative, "reason": "artifact_outside_run_dir"})
            continue
        if not artifact_path.is_file():
            failures.append({"path": relative, "reason": "missing"})
            continue
        actual_sha256 = _sha256(artifact_path)
        expected_sha256 = item.get("sha256")
        if actual_sha256 != expected_sha256:
            failures.append(
                {
                    "path": relative,
                    "reason": "sha256_mismatch",
                    "expected_sha256": expected_sha256,
                    "actual_sha256": actual_sha256,
                }
            )
            continue
        actual_size = artifact_path.stat().st_size
        expected_size = item.get("size_bytes")
        if actual_size != expected_size:
            failures.append(
                {
                    "path": relative,
                    "reason": "size_mismatch",
                    "expected_size_bytes": expected_size,
                    "actual_size_bytes": actual_size,
                }
            )
    return failures


def _verify_manifest_identity(run_dir: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    run = manifest.get("run")
    if not isinstance(run, dict):
        return [{"path": None, "reason": "invalid_manifest_run"}]

    failures: list[dict[str, Any]] = []
    actual_run_id = run.get("id")
    if actual_run_id != run_dir.name:
        failures.append(
            {
                "path": None,
                "reason": "manifest_run_id_mismatch",
                "expected_run_id": run_dir.name,
                "actual_run_id": actual_run_id,
            }
        )

    declared_path = run.get("path")
    if isinstance(declared_path, str) and declared_path:
        declared_run_name = _path_basename(declared_path)
        if declared_run_name and declared_run_name != run_dir.name:
            failures.append(
                {
                    "path": None,
                    "reason": "manifest_run_path_mismatch",
                    "expected_run_id": run_dir.name,
                    "actual_run_path": declared_path,
                }
            )
    return failures


def _sign_manifest(payload: dict[str, Any], *, signing_key: str, key_id: str | None) -> None:
    payload["signing"] = {
        "status": "signed",
        "algorithm": "hmac-sha256",
        "key_id": key_id,
        "signature": None,
        "notes": "Shared-key HMAC evidence signature. Keep the signing key outside run artifacts.",
    }
    payload["signing"]["signature"] = _manifest_signature(payload, signing_key)


def _verify_manifest_signature(
    manifest: dict[str, Any],
    *,
    signing_key: str | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    signing = manifest.get("signing")
    if not isinstance(signing, dict):
        signing = {}
    status = signing.get("status") or "unsigned"
    algorithm = signing.get("algorithm")
    signature = signing.get("signature")
    result = {
        "status": "unsigned" if status == "unsigned" else "not_checked",
        "algorithm": algorithm,
        "key_id": signing.get("key_id"),
    }

    if status == "unsigned":
        if signing_key is None:
            return result, []
        result["status"] = "failed"
        return result, [{"path": None, "reason": "missing_signature"}]

    if status != "signed" or algorithm != "hmac-sha256" or not isinstance(signature, str):
        result["status"] = "failed"
        return result, [{"path": None, "reason": "invalid_signature_metadata"}]

    if signing_key is None:
        result["status"] = "failed"
        return result, [{"path": None, "reason": "signature_key_unavailable"}]

    expected_signature = _manifest_signature(manifest, signing_key)
    if not hmac.compare_digest(signature, expected_signature):
        result["status"] = "failed"
        return result, [{"path": None, "reason": "invalid_signature"}]

    result["status"] = "verified"
    return result, []


def _manifest_signature(payload: dict[str, Any], signing_key: str) -> str:
    canonical = _canonical_manifest_bytes(payload)
    return hmac.new(signing_key.encode("utf-8"), canonical, hashlib.sha256).hexdigest()


def _canonical_manifest_bytes(payload: dict[str, Any]) -> bytes:
    canonical_payload = json.loads(json.dumps(payload, sort_keys=True))
    signing = canonical_payload.get("signing")
    if isinstance(signing, dict):
        signing["signature"] = None
    return json.dumps(canonical_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _path_basename(path: str) -> str:
    normalized = path.replace("\\", "/").rstrip("/")
    return normalized.rsplit("/", 1)[-1] if normalized else ""


def _manifest_display_path(run_dir: Path, manifest_path: Path) -> str:
    resolved = manifest_path.resolve()
    try:
        return resolved.relative_to(run_dir).as_posix()
    except ValueError:
        return str(resolved)


def _read_events(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        events.append(json.loads(line))
    return events


def _read_json(path: Path, *, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON file: {path}") from error
    return payload if isinstance(payload, dict) else default


def _event_data(events: list[dict[str, Any]], phase: str, key: str) -> Any:
    for event in events:
        if event.get("phase") != phase:
            continue
        data = event.get("data") or {}
        if isinstance(data, dict):
            return data.get(key)
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
