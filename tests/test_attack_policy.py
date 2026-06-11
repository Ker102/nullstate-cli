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
            self.assertIn("Policy:", completed.stdout)

    def test_attack_runner_rejects_policy_denied_target_classification(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            attack_script = run_dir / "attack.py"
            attack_script.write_text("print('allowed script')\n", encoding="utf-8")
            policy = AttackPolicy(
                allowed_target_classifications={"offline"},
                allowed_command_policy_ids={"generated-attack-script-v1"},
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
            )

            with self.assertRaisesRegex(ValueError, "command policy"):
                run_attack_script(
                    attack_script,
                    run_dir=run_dir,
                    target_url="offline://aws-public-s3",
                    stage="before",
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


if __name__ == "__main__":
    unittest.main()
