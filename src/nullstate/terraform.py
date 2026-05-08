from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_command(command: list[str], cwd: Path) -> CommandResult:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return CommandResult(command=command, returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)


def load_plan_json(terraform_dir: Path, offline: bool) -> tuple[dict[str, Any], list[CommandResult]]:
    if offline:
        return static_plan_from_tf(terraform_dir), []

    commands: list[CommandResult] = []
    init = run_command(["terraform", "init", "-input=false"], terraform_dir)
    commands.append(init)
    if not init.ok:
        raise RuntimeError(init.stderr or init.stdout)

    plan = run_command(["terraform", "plan", "-out=tfplan", "-input=false"], terraform_dir)
    commands.append(plan)
    if not plan.ok:
        raise RuntimeError(plan.stderr or plan.stdout)

    show = run_command(["terraform", "show", "-json", "tfplan"], terraform_dir)
    commands.append(show)
    if not show.ok:
        raise RuntimeError(show.stderr or show.stdout)

    return json.loads(show.stdout), commands


def static_plan_from_tf(terraform_dir: Path) -> dict[str, Any]:
    resources: list[dict[str, Any]] = []
    for tf_file in sorted(terraform_dir.glob("*.tf")):
        text = tf_file.read_text(encoding="utf-8")
        for resource_type, resource_name, body in _resource_blocks(text):
            if resource_type not in {"azurerm_storage_account", "azurerm_storage_container"}:
                continue
            values = _parse_values(body)
            resources.append(
                {
                    "address": f"{resource_type}.{resource_name}",
                    "type": resource_type,
                    "name": resource_name,
                    "values": values,
                }
            )

    return {"planned_values": {"root_module": {"resources": resources}}, "configuration": {"root_module": {}}}


def _resource_blocks(text: str) -> list[tuple[str, str, str]]:
    matches: list[tuple[str, str, str]] = []
    pattern = re.compile(r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{', re.MULTILINE)
    for match in pattern.finditer(text):
        body_start = match.end()
        body_end = _find_matching_brace(text, body_start - 1)
        if body_end == -1:
            continue
        matches.append((match.group(1), match.group(2), text[body_start:body_end]))
    return matches


def _find_matching_brace(text: str, opening_brace_index: int) -> int:
    depth = 0
    in_string = False
    escaped = False
    for index in range(opening_brace_index, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    return -1


def _parse_values(body: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for raw_line in body.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if "=" not in line:
            continue
        key, raw_value = [part.strip() for part in line.split("=", 1)]
        if not re.fullmatch(r"[A-Za-z0-9_]+", key):
            continue
        values[key] = _parse_value(raw_value.rstrip(","))
    return values


def _parse_value(raw_value: str) -> Any:
    if raw_value.startswith('"') and raw_value.endswith('"'):
        return raw_value[1:-1]
    if raw_value == "true":
        return True
    if raw_value == "false":
        return False
    return raw_value
