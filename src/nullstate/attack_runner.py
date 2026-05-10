from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class AttackToolResult:
    command: list[str]
    target_url: str
    stage: str
    returncode: int
    stdout: str
    stderr: str
    started_at: str
    ended_at: str
    duration_seconds: float

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
    timeout_seconds: int = 30,
) -> AttackToolResult:
    resolved_script = script_path.resolve()
    resolved_run_dir = run_dir.resolve()
    _validate_attack_script(resolved_script, resolved_run_dir)

    command = [
        sys.executable,
        str(resolved_script),
        "--target-url",
        target_url,
        "--stage",
        stage,
    ]
    started_at = datetime.now(UTC).isoformat()
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=resolved_run_dir,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout_seconds,
    )
    ended_at = datetime.now(UTC).isoformat()
    return AttackToolResult(
        command=command,
        target_url=target_url,
        stage=stage,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=round(time.monotonic() - started, 3),
    )


def _validate_attack_script(script_path: Path, run_dir: Path) -> None:
    if script_path.name != "attack.py":
        raise ValueError("Only generated attack.py scripts are allowed.")
    if script_path.parent != run_dir:
        raise ValueError("Attack scripts must live directly inside the run directory.")
    if not script_path.is_file():
        raise ValueError(f"Attack script not found: {script_path}")
