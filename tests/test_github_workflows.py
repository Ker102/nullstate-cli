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
        self.assertIn("hashlib.sha256", text)
        self.assertIn("actions/attest@v4", text)
        self.assertIn("subject-path: dist/*", text)
        self.assertIn('gh release create "${GITHUB_REF_NAME}" dist/* --generate-notes', text)


if __name__ == "__main__":
    unittest.main()
