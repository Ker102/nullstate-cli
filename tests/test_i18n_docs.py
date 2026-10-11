import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/docs/validate_i18n.py"
SPEC = importlib.util.spec_from_file_location("validate_i18n", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
i18n = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(i18n)


class I18nDocsTests(unittest.TestCase):
    def test_fences_keep_info_strings_comments_and_content(self):
        blocks, outside = i18n.split_fences("A\n~~~sh\necho ok\n~~~\nB\n")
        self.assertEqual(blocks, ["~~~sh\necho ok\n~~~"])
        self.assertEqual(outside, "A\nB\n")
        with self.assertRaises(ValueError):
            i18n.split_fences("```python\nx = 1\n")

    def test_links_ignore_code_and_accept_reference_images_and_html(self):
        text = (
            '[guide](guide.md#start) ![image](../assets/a.png)\n'
            '[ref][g]\n[g]: <guide.md#start> "title"\n'
            '<img src="../assets/b.png">\n'
            '`[not](missing.md)`\n```sh\n[not](missing.md)\n```\n'
        )
        self.assertEqual(
            i18n.links(text),
            ["guide.md#start", "../assets/a.png", "guide.md#start", "../assets/b.png"],
        )

    def test_heading_anchors_include_duplicates_and_explicit_ids(self):
        self.assertEqual(
            i18n.anchors('# Hello `API`\n## Hello `API`\n<a id="original"></a>\n'),
            {"hello-api", "hello-api-1", "original"},
        )

    def test_source_hash_is_independent_of_checkout_line_endings(self):
        self.assertEqual(i18n.digest("hello\r\n"), i18n.digest("hello\n"))

    def test_validation_detects_drift_links_code_and_false_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = '# Guide\n\nUse `api()` version 1.2.3.\n\n```sh\necho ok\n```\n'
            translated = '<a id="guide"></a>\n# Guía\n\nUse `api()` versión 1.2.3.\n\n```sh\necho ok\n```\n'
            (root / "guide.md").write_text(source, encoding="utf-8")
            mirror = root / "docs/i18n/es/guide.md"
            mirror.parent.mkdir(parents=True)
            mirror.write_text(translated, encoding="utf-8")
            manifest = {
                "schema_version": 1,
                "locales": ["es"],
                "sources": [{
                    "path": "guide.md", "sha256": i18n.digest(source),
                    "mirrors": {"es": {
                        "status": "complete", "path": "docs/i18n/es/guide.md",
                        "sha256": i18n.digest(translated),
                    }},
                }],
                "excluded": [], "shared_assets": [],
            }
            self.assertEqual(i18n.validate(root, manifest, check_inventory=False), [])
            mirror.write_text(translated.replace("echo ok", "echo changed") + '\n[bad](missing.md)\n', encoding="utf-8")
            errors = i18n.validate(root, manifest, check_inventory=False)
            self.assertTrue(any("fenced code" in e for e in errors))
            self.assertTrue(any("broken link" in e for e in errors))
            mirror.write_text(translated.replace("api()", "api(unsafe)"), encoding="utf-8")
            self.assertTrue(any("inline code" in e for e in i18n.validate(root, manifest, check_inventory=False)))
            (root / "guide.md").write_text(source + "Changed.\n", encoding="utf-8")
            self.assertTrue(any("source hash drift" in e for e in i18n.validate(root, manifest, check_inventory=False)))
            mirror.unlink()
            self.assertTrue(any("missing completed mirror" in e for e in i18n.validate(root, manifest, check_inventory=False)))
            manifest["sources"][0]["mirrors"]["es"] = {"status": "pending", "path": None}
            manifest["sources"][0]["sha256"] = i18n.digest(source + "Changed.\n")
            self.assertEqual(i18n.validate(root, manifest, check_inventory=False), [])

    def test_links_use_completed_mirrors_or_authoritative_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = '# Start\n\n[b](b.md#start)\n'
            (root / "a.md").write_text(source, encoding="utf-8")
            (root / "b.md").write_text("# Start\n", encoding="utf-8")
            mirror = root / "docs/i18n/es/a.md"
            mirror.parent.mkdir(parents=True)
            text = '<a id="start"></a>\n# Inicio\n\n[b](../../../b.md#start)\n'
            mirror.write_text(text, encoding="utf-8")
            manifest = {
                "schema_version": 1, "locales": ["es"],
                "sources": [{"path": "a.md", "sha256": i18n.digest(source), "mirrors": {
                    "es": {"status": "complete", "path": "docs/i18n/es/a.md", "sha256": i18n.digest(text)},
                }}], "excluded": [], "shared_assets": [],
            }
            self.assertEqual(i18n.validate(root, manifest, check_inventory=False), [])
            mirror.write_text(text.replace("../../../b.md#start", "../../../b.md#missing"), encoding="utf-8")
            self.assertTrue(any("broken anchor" in e for e in i18n.validate(root, manifest, check_inventory=False)))

    def test_repository_manifest_and_mirrors(self):
        root = SCRIPT.parents[2]
        manifest = json.loads((root / "docs/i18n/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(set(manifest["locales"]), {"es", "zh-CN", "fr", "ja", "de", "pt-BR"})
        entries = {entry["path"]: entry for entry in manifest["sources"]}
        self.assertGreaterEqual(len(entries), 38)
        for path in (
            "README.md", "CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md",
            "docs/architecture.md", "docs/quickstart-10-minutes.md", "docs/runbook.md",
            "docs/security-model.md", "docs/threat-model.md", "docs/ci-cd.md",
            "docs/model-serving.md",
        ):
            self.assertIn(path, entries)
        for path, entry in entries.items():
            for locale in manifest["locales"]:
                self.assertEqual(
                    entry["mirrors"][locale]["status"], "complete",
                    f"Maintained documentation gap: {locale}/{path}",
                )
        self.assertEqual(i18n.validate(root, manifest), [])
