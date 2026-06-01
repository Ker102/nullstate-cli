from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PatchResult:
    changed: bool
    diff: str
    changed_files: list[str]


def remediate_terraform_files(terraform_dir: Path) -> PatchResult:
    return remediate_scenario_files("azure-public-blob", terraform_dir)


def remediate_scenario_files(scenario_name: str, terraform_dir: Path) -> PatchResult:
    if scenario_name == "azure-public-blob":
        return _remediate_files(terraform_dir, ("*.tf",), _remediate_azure_text)
    if scenario_name == "aws-public-s3":
        return _remediate_files(terraform_dir, ("*.tf",), _remediate_aws_text)
    if scenario_name == "k8s-privileged-pod":
        return _remediate_files(terraform_dir, ("*.yaml", "*.yml"), _remediate_k8s_text)
    if scenario_name == "compose-exposed-admin":
        return _remediate_files(
            terraform_dir,
            ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml"),
            _remediate_compose_text,
        )
    if scenario_name == "onprem-ssh-password":
        return _remediate_files(terraform_dir, ("*.yaml", "*.yml", "*.cfg", "*.conf"), _remediate_onprem_text)
    if scenario_name == "generic-plan-review":
        return _remediate_files(terraform_dir, ("*.json",), _remediate_generic_plan_text)
    return PatchResult(changed=False, diff="", changed_files=[])


def _remediate_files(terraform_dir: Path, patterns: tuple[str, ...], updater) -> PatchResult:
    changed_files: list[str] = []
    diff_parts: list[str] = []

    files: list[Path] = []
    for pattern in patterns:
        files.extend(path for path in terraform_dir.glob(pattern) if path.is_file())

    for tf_file in sorted(set(files)):
        before = tf_file.read_text(encoding="utf-8")
        after = updater(before)
        if before == after:
            continue
        tf_file.write_text(after, encoding="utf-8")
        changed_files.append(str(tf_file))
        diff_parts.append(
            "".join(
                difflib.unified_diff(
                    before.splitlines(keepends=True),
                    after.splitlines(keepends=True),
                    fromfile=f"a/{tf_file.name}",
                    tofile=f"b/{tf_file.name}",
                )
            )
        )

    return PatchResult(changed=bool(changed_files), diff="\n".join(diff_parts), changed_files=changed_files)


def _remediate_azure_text(text: str) -> str:
    text = _update_resource_blocks(text, "azurerm_storage_container", _secure_container_block)
    text = _update_resource_blocks(text, "azurerm_storage_account", _secure_storage_account_block)
    return text


def _remediate_aws_text(text: str) -> str:
    for key in ("block_public_acls", "block_public_policy", "ignore_public_acls", "restrict_public_buckets"):
        text = re.sub(rf"({key}\s*=\s*)false", r"\1true", text)
    text = _remove_resource_blocks(text, "aws_s3_bucket_policy")
    text = _remove_resource_blocks(text, "aws_s3_object", resource_name="evidence")
    return text


def _remediate_k8s_text(text: str) -> str:
    text = text.replace("privileged: true", "privileged: false")
    text = text.replace("    - name: host-root\n      hostPath:\n        path: /\n", "    - name: host-root\n      emptyDir: {}\n")
    return text


def _remediate_compose_text(text: str) -> str:
    return text.replace("0.0.0.0:", "127.0.0.1:")


def _remediate_onprem_text(text: str) -> str:
    text = text.replace("PasswordAuthentication yes", "PasswordAuthentication no")
    text = text.replace("PermitRootLogin yes", "PermitRootLogin no")
    return text


def _remediate_generic_plan_text(text: str) -> str:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text
    updated = _replace_public_cidr(payload)
    return json.dumps(updated, indent=2) + "\n"


def _replace_public_cidr(value):
    if isinstance(value, str):
        return "10.0.0.0/8" if value in {"0.0.0.0/0", "::/0"} else value
    if isinstance(value, list):
        return [_replace_public_cidr(item) for item in value]
    if isinstance(value, dict):
        return {key: _replace_public_cidr(item) for key, item in value.items()}
    return value


def _update_resource_blocks(text: str, resource_type: str, updater) -> str:
    pattern = re.compile(rf'(resource\s+"{re.escape(resource_type)}"\s+"[^"]+"\s*\{{)', re.MULTILINE)
    output: list[str] = []
    cursor = 0
    for match in pattern.finditer(text):
        opening_index = match.end() - 1
        closing_index = _find_matching_brace(text, opening_index)
        if closing_index == -1:
            continue
        output.append(text[cursor:match.start()])
        output.append(match.group(1))
        body = text[match.end():closing_index]
        output.append(updater(body))
        output.append("}")
        cursor = closing_index + 1
    output.append(text[cursor:])
    return "".join(output)


def _remove_resource_blocks(text: str, resource_type: str, *, resource_name: str | None = None) -> str:
    name_pattern = re.escape(resource_name) if resource_name else r'[^"]+'
    pattern = re.compile(rf'resource\s+"{re.escape(resource_type)}"\s+"{name_pattern}"\s*\{{', re.MULTILINE)
    output: list[str] = []
    cursor = 0
    for match in pattern.finditer(text):
        opening_index = match.end() - 1
        closing_index = _find_matching_brace(text, opening_index)
        if closing_index == -1:
            continue
        output.append(text[cursor:match.start()])
        cursor = closing_index + 1
        if cursor < len(text) and text[cursor] == "\n":
            cursor += 1
    output.append(text[cursor:])
    return "".join(output)


def _secure_container_block(body: str) -> str:
    if re.search(r'container_access_type\s*=\s*"(blob|container)"', body):
        return re.sub(r'container_access_type\s*=\s*"(blob|container)"', 'container_access_type = "private"', body)
    return body


def _secure_storage_account_block(body: str) -> str:
    if re.search(r"allow_nested_items_to_be_public\s*=", body):
        return re.sub(r"allow_nested_items_to_be_public(\s*)=(\s*)true", r"allow_nested_items_to_be_public\1=\2false", body)
    insertion = _line_indent(body) + "allow_nested_items_to_be_public = false\n"
    if body.endswith("\n"):
        return body + insertion
    return body + "\n" + insertion


def _line_indent(body: str) -> str:
    for line in body.splitlines():
        stripped = line.lstrip()
        if stripped and not stripped.startswith("#"):
            return line[: len(line) - len(stripped)]
    return "  "


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
