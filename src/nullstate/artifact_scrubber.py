from __future__ import annotations

import ipaddress
import re
import shutil
from pathlib import Path
from typing import Any

from .artifacts import write_json


REDACTION_RULES: tuple[tuple[str, str, str], ...] = (
    (
        "localstack_auth_token",
        r"(?i)(LOCALSTACK_AUTH_TOKEN\s*[=:]\s*)[^\s\"']+",
        r"\1<redacted-localstack-auth-token>",
    ),
    (
        "model_api_key",
        r"(?i)((?:NULLSTATE_)?(?:RED_|BLUE_)?LLM_API_KEY\s*[=:]\s*)[^\s\"']+",
        r"\1<redacted-model-api-key>",
    ),
    (
        "azure_client_secret",
        r"(?i)(ARM_CLIENT_SECRET\s*[=:]\s*)[^\s\"']+",
        r"\1<redacted-azure-client-secret>",
    ),
    (
        "bearer_token",
        r"(?i)(Authorization:\s*Bearer\s+)[^\s\"']+",
        r"\1<redacted-bearer-token>",
    ),
    (
        "aws_access_key",
        r"\b(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}\b",
        r"<redacted-aws-access-key>",
    ),
    (
        "uuid",
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        r"<redacted-uuid>",
    ),
)


TEXT_SUFFIXES = {
    "",
    ".cfg",
    ".conf",
    ".env",
    ".hcl",
    ".json",
    ".jsonl",
    ".md",
    ".patch",
    ".prom",
    ".py",
    ".tf",
    ".txt",
    ".yaml",
    ".yml",
}


def scrub_run_artifacts(run_dir: Path, output_dir: Path) -> dict[str, Any]:
    source = run_dir.resolve()
    if not source.is_dir():
        raise FileNotFoundError(f"Run directory not found: {source}")

    destination = output_dir.resolve() / source.name
    if destination.exists():
        raise FileExistsError(f"Scrubbed output already exists: {destination}")

    shutil.copytree(source, destination)
    redaction_counts = {name: 0 for name, _, _ in REDACTION_RULES}
    redaction_counts["private_ipv4"] = 0
    changed_files: list[str] = []
    scanned_files = 0

    for path in sorted(item for item in destination.rglob("*") if item.is_file()):
        if path.name == "scrub-report.json" or not _is_text_artifact(path):
            continue
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        scanned_files += 1
        redacted, file_counts = _redact_text(original)
        if redacted == original:
            continue
        path.write_text(redacted, encoding="utf-8")
        changed_files.append(str(path.relative_to(destination)))
        for name, count in file_counts.items():
            redaction_counts[name] += count

    report: dict[str, Any] = {
        "schema_version": 1,
        "source_run_dir": str(source),
        "scrubbed_run_dir": str(destination),
        "files_scanned": scanned_files,
        "files_changed": changed_files,
        "redaction_counts": {key: value for key, value in redaction_counts.items() if value},
        "notes": "Original run artifacts were not modified.",
    }
    write_json(destination / "scrub-report.json", report)
    return report


def _is_text_artifact(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES


def _redact_text(value: str) -> tuple[str, dict[str, int]]:
    counts = {name: 0 for name, _, _ in REDACTION_RULES}
    counts["private_ipv4"] = 0
    redacted = value
    for name, pattern, replacement in REDACTION_RULES:
        redacted, count = re.subn(pattern, replacement, redacted)
        counts[name] += count
    redacted, private_count = _redact_private_ipv4_values(redacted)
    counts["private_ipv4"] += private_count
    return redacted, counts


def _redact_private_ipv4_values(value: str) -> tuple[str, int]:
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        raw = match.group(0)
        try:
            address = ipaddress.ip_address(raw)
        except ValueError:
            return raw
        if address.is_private and not address.is_loopback:
            count += 1
            return "<redacted-private-ipv4>"
        return raw

    return re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", replace, value), count
