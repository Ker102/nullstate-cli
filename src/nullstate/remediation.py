from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PatchResult:
    changed: bool
    diff: str
    changed_files: list[str]


def remediate_terraform_files(terraform_dir: Path) -> PatchResult:
    changed_files: list[str] = []
    diff_parts: list[str] = []

    for tf_file in sorted(terraform_dir.glob("*.tf")):
        before = tf_file.read_text(encoding="utf-8")
        after = _remediate_text(before)
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


def _remediate_text(text: str) -> str:
    text = _update_resource_blocks(text, "azurerm_storage_container", _secure_container_block)
    text = _update_resource_blocks(text, "azurerm_storage_account", _secure_storage_account_block)
    return text


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
