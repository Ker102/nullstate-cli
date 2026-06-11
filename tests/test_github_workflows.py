import unittest
from pathlib import Path


class GithubWorkflowTests(unittest.TestCase):
    def test_nullstate_sarif_workflow_exports_and_uploads_sarif(self):
        workflow = Path(".github/workflows/nullstate-sarif.yml")

        self.assertTrue(workflow.is_file(), "Expected the Nullstate SARIF workflow to exist.")
        text = workflow.read_text(encoding="utf-8")

        self.assertIn("python -m nullstate run examples/aws-public-s3 --offline --mock-agents --runs-dir runs/ci", text)
        self.assertIn("python -m nullstate sarif --runs-dir runs/ci --output artifacts/nullstate.sarif", text)
        self.assertIn("github/codeql-action/upload-sarif", text)
        self.assertIn("security-events: write", text)


if __name__ == "__main__":
    unittest.main()
