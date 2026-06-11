from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__


EVIDENCE_MANIFEST_SCHEMA_VERSION = 1
EVIDENCE_MANIFEST_FILENAME = "evidence-manifest.json"


def write_evidence_manifest(run_dir: Path, output_path: Path | None = None) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    target = output_path or run_dir / EVIDENCE_MANIFEST_FILENAME
    payload = build_evidence_manifest(run_dir, output_path=target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def build_evidence_manifest(run_dir: Path, *, output_path: Path | None = None) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    if not (run_dir / "report.md").is_file():
        raise ValueError(f"Run directory does not contain report.md: {run_dir}")

    events = _read_events(run_dir / "events.jsonl")
    attack_manifest = _read_json(run_dir / "attack-manifest.json", default={})
    artifacts = _artifact_inventory(run_dir, output_path=output_path)
    return {
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
            "excluded_paths": ["workspace/", ".terraform/", "__pycache__/", EVIDENCE_MANIFEST_FILENAME],
        },
        "signing": {
            "status": "unsigned",
            "algorithm": None,
            "signature": None,
            "notes": "This manifest records artifact integrity hashes. Cryptographic signing is not enabled yet.",
        },
    }


def _artifact_inventory(run_dir: Path, *, output_path: Path | None) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    excluded_dirs = {"workspace", ".terraform", "__pycache__"}
    excluded_files = {EVIDENCE_MANIFEST_FILENAME}
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
    payload = json.loads(path.read_text(encoding="utf-8"))
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
