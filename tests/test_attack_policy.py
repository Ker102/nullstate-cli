import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nullstate.attack_runner import run_attack_script
from nullstate.policy import AttackPolicy


class AttackPolicyTests(unittest.TestCase):
    def test_policy_init_writes_default_attack_allowlist(self):
        with TemporaryDirectory() as raw_tmp:
            output = Path(raw_tmp) / "nullstate-policy.json"

            completed = subprocess.run(
                [sys.executable, "-m", "nullstate", "policy", "init", "--output", str(output)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertIn("generated-attack-script-v1", payload["allowed_command_policy_ids"])
            self.assertIn("local-http", payload["allowed_target_classifications"])
            self.assertIn("aws-public-s3", payload["allowed_scenarios"])
            self.assertIn("localstack-aws", payload["allowed_backends"])
            self.assertIn("before", payload["allowed_stages"])
            self.assertIn("--target-url", payload["allowed_attack_script_args"])
            self.assertIn("--manifest", payload["allowed_attack_script_args"])
            self.assertEqual(payload["max_timeout_seconds"], 30)
            self.assertEqual(payload["max_output_bytes"], 12000)
            self.assertIn("Policy:", completed.stdout)

    def test_attack_runner_rejects_policy_denied_target_classification(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            attack_script = run_dir / "attack.py"
            attack_script.write_text("print('allowed script')\n", encoding="utf-8")
            policy = AttackPolicy(
                allowed_target_classifications={"offline"},
                allowed_command_policy_ids={"generated-attack-script-v1"},
                allowed_scenarios=None,
                allowed_backends=None,
                allowed_stages=None,
                allowed_attack_script_args=None,
                max_timeout_seconds=None,
                max_output_bytes=None,
            )

            with self.assertRaisesRegex(ValueError, "target classification"):
                run_attack_script(
                    attack_script,
                    run_dir=run_dir,
                    target_url="http://localhost.localstack.cloud:4566",
                    stage="before",
                    policy=policy,
                )

    def test_attack_runner_rejects_policy_denied_command_policy_id(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            attack_script = run_dir / "attack.py"
            attack_script.write_text("print('allowed script')\n", encoding="utf-8")
            policy = AttackPolicy(
                allowed_target_classifications={"offline"},
                allowed_command_policy_ids={"future-command-template"},
                allowed_scenarios=None,
                allowed_backends=None,
                allowed_stages=None,
                allowed_attack_script_args=None,
                max_timeout_seconds=None,
                max_output_bytes=None,
            )

            with self.assertRaisesRegex(ValueError, "command policy"):
                run_attack_script(
                    attack_script,
                    run_dir=run_dir,
                    target_url="offline://aws-public-s3",
                    stage="before",
                    policy=policy,
                )

    def test_attack_runner_rejects_policy_denied_scenario(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            attack_script = run_dir / "attack.py"
            attack_script.write_text("print('allowed script')\n", encoding="utf-8")
            policy = AttackPolicy(
                allowed_target_classifications={"offline"},
                allowed_command_policy_ids={"generated-attack-script-v1"},
                allowed_scenarios={"azure-public-blob"},
                allowed_backends=None,
                allowed_stages=None,
                allowed_attack_script_args=None,
                max_timeout_seconds=None,
                max_output_bytes=None,
            )

            with self.assertRaisesRegex(ValueError, "scenario"):
                run_attack_script(
                    attack_script,
                    run_dir=run_dir,
                    target_url="offline://aws-public-s3",
                    stage="before",
                    scenario_name="aws-public-s3",
                    policy=policy,
                )

    def test_attack_runner_rejects_policy_denied_backend(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            attack_script = run_dir / "attack.py"
            attack_script.write_text("print('allowed script')\n", encoding="utf-8")
            policy = AttackPolicy(
                allowed_target_classifications={"offline"},
                allowed_command_policy_ids={"generated-attack-script-v1"},
                allowed_scenarios=None,
                allowed_backends={"localstack-azure"},
                allowed_stages=None,
                allowed_attack_script_args=None,
                max_timeout_seconds=None,
                max_output_bytes=None,
            )

            with self.assertRaisesRegex(ValueError, "backend"):
                run_attack_script(
                    attack_script,
                    run_dir=run_dir,
                    target_url="offline://aws-public-s3",
                    stage="before",
                    backend_name="localstack-aws",
                    policy=policy,
                )

    def test_attack_runner_rejects_policy_denied_stage(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            attack_script = run_dir / "attack.py"
            attack_script.write_text("print('allowed script')\n", encoding="utf-8")
            policy = AttackPolicy(
                allowed_target_classifications={"offline"},
                allowed_command_policy_ids={"generated-attack-script-v1"},
                allowed_scenarios=None,
                allowed_backends=None,
                allowed_stages={"after"},
                allowed_attack_script_args=None,
                max_timeout_seconds=None,
                max_output_bytes=None,
            )

            with self.assertRaisesRegex(ValueError, "stage"):
                run_attack_script(
                    attack_script,
                    run_dir=run_dir,
                    target_url="offline://aws-public-s3",
                    stage="before",
                    policy=policy,
                )

    def test_attack_runner_rejects_timeout_above_policy_ceiling(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            attack_script = run_dir / "attack.py"
            attack_script.write_text("print('allowed script')\n", encoding="utf-8")
            policy = AttackPolicy(
                allowed_target_classifications={"offline"},
                allowed_command_policy_ids={"generated-attack-script-v1"},
                allowed_scenarios=None,
                allowed_backends=None,
                allowed_stages=None,
                allowed_attack_script_args=None,
                max_timeout_seconds=5,
                max_output_bytes=None,
            )

            with self.assertRaisesRegex(ValueError, "timeout"):
                run_attack_script(
                    attack_script,
                    run_dir=run_dir,
                    target_url="offline://aws-public-s3",
                    stage="before",
                    timeout_seconds=30,
                    policy=policy,
                )

    def test_attack_runner_rejects_output_limit_above_policy_ceiling(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            attack_script = run_dir / "attack.py"
            attack_script.write_text("print('allowed script')\n", encoding="utf-8")
            policy = AttackPolicy(
                allowed_target_classifications={"offline"},
                allowed_command_policy_ids={"generated-attack-script-v1"},
                allowed_scenarios=None,
                allowed_backends=None,
                allowed_stages=None,
                allowed_attack_script_args=None,
                max_timeout_seconds=None,
                max_output_bytes=1024,
            )

            with self.assertRaisesRegex(ValueError, "output"):
                run_attack_script(
                    attack_script,
                    run_dir=run_dir,
                    target_url="offline://aws-public-s3",
                    stage="before",
                    max_output_bytes=12_000,
                    policy=policy,
                )

    def test_attack_runner_rejects_policy_denied_manifest_argument(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            attack_script = run_dir / "attack.py"
            attack_script.write_text("print('allowed script')\n", encoding="utf-8")
            manifest = run_dir / "attack-manifest.json"
            manifest.write_text("{}", encoding="utf-8")
            policy = AttackPolicy(
                allowed_target_classifications={"offline"},
                allowed_command_policy_ids={"generated-attack-script-v1"},
                allowed_scenarios=None,
                allowed_backends=None,
                allowed_stages=None,
                allowed_attack_script_args={"--target-url", "--stage"},
                max_timeout_seconds=None,
                max_output_bytes=None,
            )

            with self.assertRaisesRegex(ValueError, "argument"):
                run_attack_script(
                    attack_script,
                    run_dir=run_dir,
                    target_url="offline://aws-public-s3",
                    stage="before",
                    manifest_path=manifest,
                    policy=policy,
                )

    def test_run_rejects_policy_file_that_denies_offline_target(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            runs_dir = root / "runs"
            policy_path = root / "policy.json"
            policy_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "allowed_target_classifications": ["local-http"],
                        "allowed_command_policy_ids": ["generated-attack-script-v1"],
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "run",
                    "examples/aws-public-s3",
                    "--offline",
                    "--mock-agents",
                    "--policy-file",
                    str(policy_path),
                    "--runs-dir",
                    str(runs_dir),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("target classification", completed.stderr)

    def test_run_rejects_policy_file_that_denies_scenario(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            runs_dir = root / "runs"
            policy_path = root / "policy.json"
            policy_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "allowed_target_classifications": ["offline"],
                        "allowed_command_policy_ids": ["generated-attack-script-v1"],
                        "allowed_scenarios": ["azure-public-blob"],
                        "allowed_backends": ["localstack-aws"],
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "run",
                    "examples/aws-public-s3",
                    "--offline",
                    "--mock-agents",
                    "--policy-file",
                    str(policy_path),
                    "--runs-dir",
                    str(runs_dir),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("scenario", completed.stderr)


if __name__ == "__main__":
    unittest.main()
