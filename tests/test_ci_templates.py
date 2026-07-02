import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nullstate.ci_templates import render_github_workflow, write_github_ci_files


class CiTemplateTests(unittest.TestCase):
    def test_render_github_workflow_replaces_user_facing_defaults(self):
        workflow = render_github_workflow(
            scenario="azure-public-blob",
            iac_path="infra/azure",
            policy_file="security/nullstate-policy.json",
            baseline_file="security/nullstate-baseline.json",
            fail_on_severity="critical",
        )

        self.assertIn("NULLSTATE_SCENARIO: azure-public-blob", workflow)
        self.assertIn("NULLSTATE_IAC_PATH: infra/azure", workflow)
        self.assertIn("NULLSTATE_POLICY_FILE: security/nullstate-policy.json", workflow)
        self.assertIn("NULLSTATE_BASELINE_FILE: security/nullstate-baseline.json", workflow)
        self.assertIn("NULLSTATE_FAIL_ON_SEVERITY: critical", workflow)

    def test_write_github_ci_files_writes_workflow_and_policy(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            workflow_path = root / ".github" / "workflows" / "nullstate.yml"
            policy_path = root / "nullstate-policy.json"

            result = write_github_ci_files(
                workflow_path=workflow_path,
                policy_path=policy_path,
                scenario="aws-public-s3",
                iac_path="examples/aws-public-s3",
                fail_on_severity="high",
            )

            self.assertEqual(result["workflow_path"], str(workflow_path))
            self.assertEqual(result["policy_path"], str(policy_path))
            self.assertTrue(workflow_path.is_file())
            self.assertTrue(policy_path.is_file())
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            self.assertEqual(policy["preset"], "scenario:aws-public-s3")
            self.assertEqual(policy["allowed_scenarios"], ["aws-public-s3"])

    def test_write_github_ci_files_refuses_to_overwrite_without_force(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            workflow_path = root / ".github" / "workflows" / "nullstate.yml"
            policy_path = root / "nullstate-policy.json"
            workflow_path.parent.mkdir(parents=True)
            workflow_path.write_text("existing workflow", encoding="utf-8")

            with self.assertRaisesRegex(FileExistsError, "already exists"):
                write_github_ci_files(
                    workflow_path=workflow_path,
                    policy_path=policy_path,
                    scenario="aws-public-s3",
                    iac_path="examples/aws-public-s3",
                    fail_on_severity="high",
                )

    def test_init_ci_github_cli_writes_workflow_and_policy(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            workflow_path = root / ".github" / "workflows" / "nullstate.yml"
            policy_path = root / "nullstate-policy.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "init-ci",
                    "github",
                    "--output",
                    str(workflow_path),
                    "--policy-output",
                    str(policy_path),
                    "--scenario",
                    "aws-public-s3",
                    "--iac-path",
                    "examples/aws-public-s3",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(workflow_path.is_file())
            self.assertTrue(policy_path.is_file())
            self.assertIn("GitHub Actions workflow", completed.stdout)


if __name__ == "__main__":
    unittest.main()
