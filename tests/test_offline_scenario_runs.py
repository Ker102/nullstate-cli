import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nullstate.scenarios import get_scenario


OFFLINE_SCENARIOS = {
    "aws-public-s3": "AWS_S3_PUBLIC_ACCESS_BLOCK_DISABLED",
    "k8s-privileged-pod": "K8S_PRIVILEGED_WORKLOAD",
    "compose-exposed-admin": "COMPOSE_PUBLIC_ADMIN_PORT",
    "onprem-ssh-password": "ONPREM_SSH_PASSWORD_LOGIN",
    "generic-plan-review": "GENERIC_PUBLIC_ADMIN_INGRESS",
}


class OfflineScenarioRunTests(unittest.TestCase):
    def test_doctor_prints_nullstate_banner(self):
        completed = subprocess.run(
            [sys.executable, "-m", "nullstate", "doctor", "--offline"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Nullstate", completed.stdout)
        self.assertIn("Autonomous Purple-Team Sandbox", completed.stdout)

    def test_all_scaffolded_scenarios_run_offline_end_to_end(self):
        for scenario_name, expected_rule_id in OFFLINE_SCENARIOS.items():
            with self.subTest(scenario=scenario_name):
                with TemporaryDirectory() as raw_tmp:
                    root = Path(raw_tmp)
                    demo_dir = root / scenario_name
                    runs_dir = root / "runs"
                    scenario = get_scenario(scenario_name)

                    init_completed = subprocess.run(
                        [sys.executable, "-m", "nullstate", "init-demo", scenario_name, "--output", str(demo_dir)],
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(init_completed.returncode, 0, init_completed.stderr)

                    run_completed = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "nullstate",
                            "run",
                            str(demo_dir),
                            "--offline",
                            "--target",
                            scenario.backend,
                            "--scenario",
                            scenario.name,
                            "--runs-dir",
                            str(runs_dir),
                        ],
                        text=True,
                        capture_output=True,
                        check=False,
                    )

                    self.assertEqual(run_completed.returncode, 0, run_completed.stderr)
                    self.assertIn("Nullstate", run_completed.stdout)
                    run_dirs = list(runs_dir.iterdir())
                    self.assertEqual(len(run_dirs), 1)
                    run_dir = run_dirs[0]
                    findings = json.loads((run_dir / "findings.json").read_text(encoding="utf-8"))
                    report = (run_dir / "report.md").read_text(encoding="utf-8")
                    patch = (run_dir / "remediation.patch").read_text(encoding="utf-8")

                    self.assertTrue(findings)
                    self.assertEqual(findings[0]["rule_id"], expected_rule_id)
                    self.assertIn(expected_rule_id, report)
                    self.assertIn("Exploit blocked after remediation", report)
                    self.assertTrue(patch.strip())

    def test_run_infers_scenario_and_target_when_omitted(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            demo_dir = root / "aws-public-s3"
            runs_dir = root / "runs"

            init_completed = subprocess.run(
                [sys.executable, "-m", "nullstate", "init-demo", "aws-public-s3", "--output", str(demo_dir)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(init_completed.returncode, 0, init_completed.stderr)

            run_completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "run",
                    str(demo_dir),
                    "--offline",
                    "--runs-dir",
                    str(runs_dir),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(run_completed.returncode, 0, run_completed.stderr)
            self.assertIn("Scenario: aws-public-s3", run_completed.stdout)
            self.assertIn("Target: localstack-aws", run_completed.stdout)
            run_dir = next(runs_dir.iterdir())
            findings = json.loads((run_dir / "findings.json").read_text(encoding="utf-8"))
            self.assertEqual(findings[0]["rule_id"], "AWS_S3_PUBLIC_ACCESS_BLOCK_DISABLED")


if __name__ == "__main__":
    unittest.main()
