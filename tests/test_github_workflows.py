import unittest
from pathlib import Path


class GithubWorkflowTests(unittest.TestCase):
    def test_nullstate_sarif_workflow_exports_and_uploads_sarif(self):
        workflow = Path(".github/workflows/nullstate-sarif.yml")

        self.assertTrue(workflow.is_file(), "Expected the Nullstate SARIF workflow to exist.")
        text = workflow.read_text(encoding="utf-8")

        self.assertIn(
            "python -m nullstate run examples/aws-public-s3 --offline --mock-agents --ci --fail-on-severity none --runs-dir runs/ci",
            text,
        )
        self.assertIn("python -m nullstate sarif --runs-dir runs/ci --output artifacts/nullstate.sarif", text)
        self.assertIn("github/codeql-action/upload-sarif", text)
        self.assertIn("security-events: write", text)

    def test_release_workflow_generates_manifest_and_attestations(self):
        workflow = Path(".github/workflows/release.yml")

        self.assertTrue(workflow.is_file(), "Expected the release workflow to exist.")
        text = workflow.read_text(encoding="utf-8")

        self.assertIn("contents: write", text)
        self.assertIn("id-token: write", text)
        self.assertIn("attestations: write", text)
        self.assertIn("python -m build", text)
        self.assertIn("release-manifest.json", text)
        self.assertIn("sbom.spdx.json", text)
        self.assertIn("spdxVersion", text)
        self.assertIn("tomllib", text)
        self.assertIn("python -m venv .sbom-venv", text)
        self.assertIn(".sbom-venv/bin/python -m pip install dist/*.whl", text)
        self.assertIn("import importlib.metadata", text)
        self.assertIn('excluded_tools = {"pip", "setuptools", "wheel"}', text)
        self.assertIn('"versionInfo": distribution.version', text)
        self.assertIn("Validate release SBOM", text)
        self.assertIn('sbom_path = Path("dist/sbom.spdx.json")', text)
        self.assertIn('if sbom.get("spdxVersion") != "SPDX-2.3"', text)
        self.assertIn('required_package_fields = {"SPDXID", "name", "versionInfo"}', text)
        self.assertIn('forbidden_packages = {"pip", "setuptools", "wheel"}', text)
        self.assertIn('relationshipType") == "DESCRIBES"', text)
        self.assertIn("Validate SBOM with SPDX tools", text)
        self.assertIn(".sbom-venv/bin/python -m pip install spdx-tools==0.8.5", text)
        self.assertIn(".sbom-venv/bin/pyspdxtools -i dist/sbom.spdx.json", text)
        self.assertIn("relationships", text)
        self.assertIn('r"[<>=!~;\\[\\], ]"', text)
        self.assertIn("hashlib.sha256", text)
        self.assertIn("actions/attest@v4", text)
        self.assertIn("subject-path: dist/*", text)
        self.assertIn("Attest release SBOM", text)
        self.assertIn("sbom-path: dist/sbom.spdx.json", text)
        self.assertIn("Sign release artifacts", text)
        self.assertIn("sigstore/gh-action-sigstore-python@v3.4.0", text)
        self.assertIn("dist/*.whl", text)
        self.assertIn("dist/*.tar.gz", text)
        self.assertIn("dist/sbom.spdx.json", text)
        self.assertIn("dist/release-manifest.json", text)
        self.assertIn("release-signing-artifacts: false", text)
        self.assertIn("Validate release signatures", text)
        self.assertIn('signature_path = path.with_name(path.name + ".sigstore.json")', text)
        self.assertIn('gh release create "${GITHUB_REF_NAME}" dist/* --generate-notes', text)

    def test_release_docs_include_sbom_attestation_verification(self):
        docs_text = "\n".join(
            [
                Path("README.md").read_text(encoding="utf-8"),
                Path("docs/ci-cd.md").read_text(encoding="utf-8"),
            ]
        )

        self.assertIn(
            "gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli --predicate-type https://spdx.dev/Document/v2.3",
            docs_text,
        )
        self.assertIn("cosign verify-blob", docs_text)
        self.assertIn("https://github.com/Ker102/nullstate-cli/.github/workflows/release.yml@refs/tags/v0.1.0", docs_text)
        self.assertIn("https://token.actions.githubusercontent.com", docs_text)


if __name__ == "__main__":
    unittest.main()
