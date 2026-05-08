import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nullstate.scenarios import get_scenario, list_scenarios


class ScenarioTests(unittest.TestCase):
    def test_lists_hackathon_scenarios_across_iac_targets(self):
        scenario_names = {scenario.name for scenario in list_scenarios()}

        self.assertIn("azure-public-blob", scenario_names)
        self.assertIn("aws-public-s3", scenario_names)
        self.assertIn("k8s-privileged-pod", scenario_names)
        self.assertIn("compose-exposed-admin", scenario_names)
        self.assertIn("onprem-ssh-password", scenario_names)
        self.assertIn("generic-plan-review", scenario_names)

    def test_scenario_maps_to_expected_backend_and_mode(self):
        scenario = get_scenario("onprem-ssh-password")

        self.assertEqual(scenario.backend, "microvm-onprem")
        self.assertEqual(scenario.mode, "digital-twin")
        self.assertIn("Ansible", scenario.iac_targets)

    def test_scenarios_list_cli_prints_exact_names(self):
        completed = subprocess.run(
            [sys.executable, "-m", "nullstate", "scenarios", "list"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("aws-public-s3", completed.stdout)
        self.assertIn("generic-plan-review", completed.stdout)

    def test_init_demo_creates_non_azure_scenario_fixture(self):
        with TemporaryDirectory() as raw_tmp:
            output = Path(raw_tmp) / "aws-public-s3"

            completed = subprocess.run(
                [sys.executable, "-m", "nullstate", "init-demo", "aws-public-s3", "--output", str(output)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((output / "main.tf").exists())
            self.assertIn("aws_s3_bucket_public_access_block", (output / "main.tf").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
