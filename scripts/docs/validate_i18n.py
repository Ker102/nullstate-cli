"""Read-only checks for the repository's Markdown translation mirrors.

No CLI scenarios, model calls, cloud APIs, or deployments are executed. Supports
the inline/reference/HTML links and backtick/tilde fences used by these docs.
"""

import argparse
import hashlib
import html
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[2]
NAV = re.compile(r"<!-- i18n-switcher:start -->.*?<!-- i18n-switcher:end -->\n?", re.S)
IDS = re.compile(r'<a\s+id="[^"]+"\s*></a>\n?')
INLINE = re.compile(r"(`+)(?!`)(.+?)\1(?!`)")


def digest(text):
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def split_fences(text):
    blocks, outside, block = [], [], []
    marker = None
    for line in text.splitlines():
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if marker is None and match:
            marker = match.group(1)
            block = [line]
        elif marker is not None:
            block.append(line)
            if match and match.group(1)[0] == marker[0] and len(match.group(1)) >= len(marker) and not match.group(2).strip():
                blocks.append("\n".join(block))
                marker = None
        else:
            outside.append(line)
    if marker is not None:
        raise ValueError("unclosed Markdown fence")
    return blocks, "\n".join(outside) + "\n"


def body(text):
    return IDS.sub("", NAV.sub("", text))


def links(text):
    _, text = split_fences(text)
    text = INLINE.sub("", text)
    result = []
    # Balanced destinations keep filenames containing parentheses intact.
    for match in re.finditer(r"!?\[[^\]\n]*\]\(", text):
        start = match.end()
        if text[start:start + 1] == "<":
            end = text.find(">", start)
            if end != -1:
                result.append(text[start + 1:end])
            continue
        depth, end = 0, start
        while end < len(text):
            char = text[end]
            if char == "(" and (end == 0 or text[end - 1] != "\\"):
                depth += 1
            elif char == ")" and (end == 0 or text[end - 1] != "\\"):
                if depth == 0:
                    break
                depth -= 1
            elif char.isspace() and depth == 0:
                break
            end += 1
        result.append(text[start:end])
    for match in re.finditer(r"^ {0,3}\[[^\]]+\]:\s*(?:<([^>]+)>|(\S+))", text, re.M):
        result.append(match.group(1) or match.group(2))
    result.extend(re.findall(r"<(https?://[^>\s]+|mailto:[^>\s]+)>", text))
    result.extend(re.findall(r'<(?:a|img)\b[^>]*\b(?:href|src)="([^"]+)"', text))
    return [html.unescape(value) for value in result]


def anchors(text):
    _, outside = split_fences(text)
    result = set(re.findall(r'\bid="([^"]+)"', outside))
    seen = Counter()
    for match in re.finditer(r"^ {0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$", outside, re.M):
        title = re.sub(r"<[^>]*>", "", match.group(1))
        title = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", title)
        title = re.sub(r"[^\w\- ]", "", html.unescape(title).lower()).replace(" ", "-")
        suffix = f"-{seen[title]}" if seen[title] else ""
        result.add(title + suffix)
        seen[title] += 1
    return result


def safe_path(root, path):
    target = (root / path).resolve()
    if Path(path).is_absolute() or not target.is_relative_to(root.resolve()):
        raise ValueError(f"path outside repository: {path}")
    return target


def link_target(root, document, destination):
    parsed = urlsplit(destination)
    if parsed.scheme or parsed.netloc:
        return None, parsed.fragment
    path = unquote(parsed.path)
    target = (root / path.lstrip("/")) if path.startswith("/") else document.parent / path
    return target.resolve(), unquote(parsed.fragment)


def check_links(root, document, text, errors):
    for destination in links(text):
        target, fragment = link_target(root, document, destination)
        if target is None:
            continue
        if not target.is_relative_to(root.resolve()) or not target.exists():
            errors.append(f"{document.relative_to(root)}: broken link {destination}")
        elif fragment and target.suffix.lower() == ".md":
            if fragment not in anchors(target.read_text(encoding="utf-8")):
                errors.append(f"{document.relative_to(root)}: broken anchor {destination}")


def validate(root, manifest, check_inventory=True):
    errors = []
    locales = manifest["locales"]
    if manifest.get("schema_version") != 1 or len(locales) != len(set(locales)):
        return ["invalid manifest schema version or duplicate locales"]
    sources = manifest["sources"]
    source_paths = [entry["path"] for entry in sources]
    excluded_paths = [entry["path"] for entry in manifest["excluded"]]
    if len(set(source_paths + excluded_paths)) != len(source_paths + excluded_paths):
        errors.append("duplicate or overlapping inventory entries")
    declared = set()
    completed = {
        (entry["path"], locale): data["path"]
        for entry in sources for locale, data in entry["mirrors"].items()
        if data["status"] == "complete"
    }
    for entry in sources:
        path = safe_path(root, entry["path"])
        if not path.is_file():
            errors.append(f"missing English source: {entry['path']}")
            continue
        source = path.read_text(encoding="utf-8")
        if digest(source) != entry["sha256"]:
            errors.append(f"{entry['path']}: source hash drift; review all translations")
        if set(entry["mirrors"]) != set(locales):
            errors.append(f"{entry['path']}: incomplete locale inventory")
        source_blocks, source_prose = split_fences(body(source))
        for locale, data in entry["mirrors"].items():
            expected = f"docs/i18n/{locale}/{entry['path']}"
            if data["status"] == "pending":
                if data.get("path") is not None or (root / expected).exists():
                    errors.append(f"{expected}: pending entry must not claim or hide a mirror")
                continue
            if data["status"] != "complete" or data.get("path") != expected:
                errors.append(f"{expected}: invalid completion/path declaration")
                continue
            declared.add(expected)
            mirror = safe_path(root, expected)
            if not mirror.is_file():
                errors.append(f"missing completed mirror: {expected}")
                continue
            translated = mirror.read_text(encoding="utf-8")
            if digest(translated) != data.get("sha256"):
                errors.append(f"{expected}: mirror hash drift; review before recording hash")
            try:
                blocks, prose = split_fences(body(translated))
                if blocks != source_blocks:
                    errors.append(f"{expected}: fenced code differs from English source")
                source_codes = Counter(m.group(2) for m in INLINE.finditer(source_prose))
                mirror_codes = Counter(m.group(2) for m in INLINE.finditer(prose))
                if mirror_codes != source_codes:
                    errors.append(
                        f"{expected}: inline code differs from English source; "
                        f"missing={dict(source_codes - mirror_codes)}, "
                        f"added={dict(mirror_codes - source_codes)}"
                    )
                for pattern, label in [
                    (r"https?://[^\s<>\]\)\"`]+", "external URLs"),
                    (r"\bv?\d+(?:\.\d+)+(?:[-.][A-Za-z0-9]+)*", "version/numeric literals"),
                ]:
                    if Counter(re.findall(pattern, prose)) != Counter(re.findall(pattern, source_prose)):
                        errors.append(f"{expected}: {label} differ from English source")
                # Identical nonempty line counts and heading levels catch truncated mirrors.
                if len([s for s in prose.splitlines() if s.strip()]) != len([s for s in source_prose.splitlines() if s.strip()]):
                    errors.append(f"{expected}: prose line coverage differs from English source")
                if re.findall(r"^(#{1,6}) ", prose, re.M) != re.findall(r"^(#{1,6}) ", source_prose, re.M):
                    errors.append(f"{expected}: heading structure differs from English source")
                expected_links = []
                for destination in links(body(source)):
                    target, fragment = link_target(root, path, destination)
                    if target is None:
                        expected_links.append(destination)
                    elif target.is_relative_to(root.resolve()):
                        repo_path = target.relative_to(root.resolve()).as_posix()
                        expected_links.append((str((root / completed.get((repo_path, locale), repo_path)).resolve()), fragment))
                actual_links = []
                for destination in links(body(translated)):
                    target, fragment = link_target(root, mirror, destination)
                    actual_links.append(destination if target is None else (str(target), fragment))
                if Counter(expected_links) != Counter(actual_links):
                    errors.append(f"{expected}: doc/asset link targets differ from inventory routing")
                check_links(root, mirror, translated, errors)
            except ValueError as exc:
                errors.append(f"{expected}: {exc}")
    for entry in manifest["excluded"] + manifest.get("shared_assets", []):
        path = safe_path(root, entry["path"])
        if not path.is_file():
            errors.append(f"missing inventory item: {entry['path']}")
        elif digest(path.read_text(encoding="utf-8")) != entry["sha256"]:
            errors.append(f"{entry['path']}: inventory hash drift; re-evaluate scope")
    if check_inventory:
        tracked = subprocess.run(["git", "ls-files", "*.md"], cwd=root, check=True, capture_output=True, text=True).stdout.splitlines()
        english = {p for p in tracked if not p.startswith("docs/i18n/")}
        missing = english - set(source_paths + excluded_paths)
        if missing:
            errors.append("uninventoried tracked Markdown: " + ", ".join(sorted(missing)))
        actual = {p.relative_to(root).as_posix() for locale in locales for p in (root / "docs/i18n" / locale).rglob("*.md")}
        if actual != declared:
            errors.append("mirror files disagree with manifest: " + ", ".join(sorted(actual ^ declared)))
        for path in [root / "README.md", root / "docs/i18n/README.md"]:
            check_links(root, path, path.read_text(encoding="utf-8"), errors)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-complete", action="store_true", help="also fail for pending maintained mirrors")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "docs/i18n/manifest.json").read_text(encoding="utf-8"))
    try:
        errors = validate(ROOT, manifest)
    except (KeyError, ValueError, OSError) as exc:
        errors = [f"invalid inventory or document: {exc}"]
    for locale in manifest["locales"]:
        complete = sum(entry["mirrors"][locale]["status"] == "complete" for entry in manifest["sources"])
        pending = len(manifest["sources"]) - complete
        print(f"{locale}: {complete} complete, {pending} pending / {len(manifest['sources'])} maintained sources")
        if args.require_complete and pending:
            errors.append(f"{locale}: {pending} maintained mirrors are pending")
    for error in errors:
        print(f"ERROR: {error}")
    print("PASS: declared mirrors, preservation, links, and hashes" if not errors else f"FAIL: {len(errors)} issue(s)")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
