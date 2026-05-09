import os
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nullstate.cli import _localstack_azure_auth_env


FAKE_TERRAFORM = r'''
import json
import sys
from pathlib import Path

cwd = Path.cwd()
args = sys.argv[1:]
command = args[0] if args else ""

if command == "init":
    sys.exit(0)

if command == "plan":
    (cwd / "tfplan").write_text("fake", encoding="utf-8")
    sys.exit(0)

if command == "show":
    text = (cwd / "main.tf").read_text(encoding="utf-8")
    public = "block_public_acls       = false" in text
    payload = {
        "planned_values": {
            "root_module": {
                "resources": [
                    {
                        "address": "aws_s3_bucket_public_access_block.public_logs",
                        "type": "aws_s3_bucket_public_access_block",
                        "name": "public_logs",
                        "values": {
                            "block_public_acls": not public,
                            "block_public_policy": not public,
                            "ignore_public_acls": not public,
                            "restrict_public_buckets": not public,
                        },
                    }
                ]
            }
        },
        "configuration": {"root_module": {}},
    }
    print(json.dumps(payload))
    sys.exit(0)

if command == "apply":
    with (cwd / "apply.log").open("a", encoding="utf-8") as handle:
        handle.write(" ".join(args) + "\n")
    sys.exit(0)

print(f"unsupported terraform command: {args}", file=sys.stderr)
sys.exit(1)
'''


class CliLiveSandboxTests(unittest.TestCase):
    def test_localstack_azure_auth_env_uses_dummy_credentials(self):
        env = _localstack_azure_auth_env("localstack-azure", offline=False)

        self.assertEqual(env["ARM_SUBSCRIPTION_ID"], "00000000-0000-0000-0000-000000000000")
        self.assertEqual(env["ARM_TENANT_ID"], "00000000-0000-0000-0000-000000000000")
        self.assertIn("ARM_CLIENT_SECRET", env)
        self.assertEqual(_localstack_azure_auth_env("localstack-azure", offline=True), {})
        self.assertEqual(_localstack_azure_auth_env("localstack-aws", offline=False), {})

    def test_live_localstack_aws_run_applies_before_and_after_remediation(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_script = fake_bin / "fake_terraform.py"
            fake_script.write_text(FAKE_TERRAFORM, encoding="utf-8")

            runs_dir = root / "runs"
            env = os.environ.copy()
            env["PATH"] = str(fake_bin) + os.pathsep + env["PATH"]
            env["NULLSTATE_TERRAFORM_COMMAND"] = json.dumps([sys.executable, str(fake_script)])
            env.pop("NULLSTATE_LLM_BASE_URL", None)
            env.pop("NULLSTATE_RED_LLM_BASE_URL", None)
            env.pop("NULLSTATE_BLUE_LLM_BASE_URL", None)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "run",
                    "examples/aws-public-s3",
                    "--target",
                    "localstack-aws",
                    "--scenario",
                    "aws-public-s3",
                    "--runs-dir",
                    str(runs_dir),
                ],
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            run_dir = next(runs_dir.iterdir())
            apply_log = run_dir / "workspace" / "apply.log"
            self.assertEqual(apply_log.read_text(encoding="utf-8").count("apply -auto-approve"), 2)
            self.assertIn("Exploit blocked after remediation", (run_dir / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
