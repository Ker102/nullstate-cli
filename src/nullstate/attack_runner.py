from __future__ import annotations

import hashlib
import ipaddress
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from .policy import AttackPolicy, enforce_attack_policy


@dataclass(frozen=True)
class AttackToolResult:
    schema_version: int
    command_policy_id: str
    command: list[str]
    target_url: str
    target_classification: str
    scenario_name: str | None
    backend_name: str | None
    stage: str
    live_cloud_allowed: bool
    returncode: int
    stdout: str
    stderr: str
    stdout_truncated: bool
    stderr_truncated: bool
    started_at: str
    ended_at: str
    duration_seconds: float
    attack_script_sha256: str
    manifest_sha256: str | None

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_attack_script(
    script_path: Path,
    *,
    run_dir: Path,
    target_url: str,
    stage: str,
    manifest_path: Path | None = None,
    scenario_name: str | None = None,
    backend_name: str | None = None,
    timeout_seconds: int = 30,
    max_output_bytes: int = 12_000,
    policy: AttackPolicy | None = None,
    allow_live_cloud: bool = False,
) -> AttackToolResult:
    resolved_script = script_path.resolve()
    resolved_run_dir = run_dir.resolve()
    _validate_attack_script(resolved_script, resolved_run_dir)
    resolved_manifest = _validate_attack_manifest(manifest_path, resolved_run_dir)
    target_classification = _validate_target_url(target_url, allow_live_cloud=allow_live_cloud)
    command_policy_id = "generated-attack-script-v1"
    attack_script_args = {"--target-url", "--stage"}
    if resolved_manifest is not None:
        attack_script_args.add("--manifest")
    enforce_attack_policy(
        policy,
        target_classification=target_classification,
        target_url=target_url,
        command_policy_id=command_policy_id,
        scenario_name=scenario_name,
        backend_name=backend_name,
        stage=stage,
        attack_script_args=attack_script_args,
        timeout_seconds=timeout_seconds,
        max_output_bytes=max_output_bytes,
    )

    command = [
        sys.executable,
        str(resolved_script),
        "--target-url",
        target_url,
        "--stage",
        stage,
    ]
    if resolved_manifest is not None:
        command.extend(["--manifest", str(resolved_manifest)])
    started_at = datetime.now(UTC).isoformat()
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=resolved_run_dir,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
        returncode = completed.returncode
        completed_stdout = completed.stdout
        completed_stderr = completed.stderr
    except subprocess.TimeoutExpired as error:
        returncode = 124
        completed_stdout = _coerce_timeout_output(error.stdout)
        completed_stderr = _coerce_timeout_output(error.stderr)
        timeout_message = f"Attack command timed out after {timeout_seconds} seconds."
        completed_stderr = f"{completed_stderr}\n{timeout_message}".strip()
    ended_at = datetime.now(UTC).isoformat()
    stdout, stdout_truncated = _truncate_text(completed_stdout, max_output_bytes)
    stderr, stderr_truncated = _truncate_text(completed_stderr, max_output_bytes)
    return AttackToolResult(
        schema_version=1,
        command_policy_id=command_policy_id,
        command=command,
        target_url=target_url,
        target_classification=target_classification,
        scenario_name=scenario_name,
        backend_name=backend_name,
        stage=stage,
        live_cloud_allowed=allow_live_cloud,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        stdout_truncated=stdout_truncated,
        stderr_truncated=stderr_truncated,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=round(time.monotonic() - started, 3),
        attack_script_sha256=_sha256_file(resolved_script),
        manifest_sha256=_sha256_file(resolved_manifest) if resolved_manifest is not None else None,
    )


def _validate_attack_script(script_path: Path, run_dir: Path) -> None:
    if script_path.name != "attack.py":
        raise ValueError("Only generated attack.py scripts are allowed.")
    if script_path.parent != run_dir:
        raise ValueError("Attack scripts must live directly inside the run directory.")
    if not script_path.is_file():
        raise ValueError(f"Attack script not found: {script_path}")


def _validate_attack_manifest(manifest_path: Path | None, run_dir: Path) -> Path | None:
    if manifest_path is None:
        return None
    resolved_manifest = manifest_path.resolve()
    if resolved_manifest.name != "attack-manifest.json":
        raise ValueError("Only generated attack-manifest.json manifests are allowed.")
    if resolved_manifest.parent != run_dir:
        raise ValueError("Attack manifests must live directly inside the run directory.")
    if not resolved_manifest.is_file():
        raise ValueError(f"Attack manifest not found: {resolved_manifest}")
    return resolved_manifest


def _validate_target_url(target_url: str, *, allow_live_cloud: bool = False) -> str:
    parsed = urlparse(target_url)
    if parsed.scheme == "offline":
        return "offline"
    if parsed.scheme == "local":
        return "local"
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Attack target URLs must use offline, local, http, or https schemes.")
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise ValueError("Attack target URLs must include a hostname.")
    if hostname in {"localhost", "localhost.localstack.cloud"}:
        return "local-http"
    if hostname.endswith(".localhost.localstack.cloud"):
        return "local-http"
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        if address.is_loopback:
            return "local-http"
    if allow_live_cloud:
        return "external-http"
    raise ValueError(f"Attack target host must be local or LocalStack-scoped: {hostname}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _truncate_text(value: str, max_bytes: int) -> tuple[str, bool]:
    encoded = value.encode("utf-8")
    if len(encoded) <= max_bytes:
        return value, False
    if max_bytes <= 0:
        return "", True
    return encoded[:max_bytes].decode("utf-8", errors="replace").rstrip() + "\n... truncated ...", True


def _coerce_timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
