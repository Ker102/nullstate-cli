import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class UploadCommandTests(unittest.TestCase):
    def test_upload_dry_run_writes_plan_and_bundle_without_network(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            run_dir = _minimal_run(runs_dir)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "upload",
                    run_dir.name,
                    "--runs-dir",
                    str(runs_dir),
                    "--dry-run",
                    "--endpoint",
                    "https://example.invalid/v1/runs",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            plan_path = run_dir / "upload-plan.json"
            bundle_path = run_dir / "run-bundle.json"
            self.assertTrue(plan_path.is_file())
            self.assertTrue(bundle_path.is_file())
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertTrue(plan["dry_run"])
            self.assertEqual(plan["endpoint"], "https://example.invalid/v1/runs")
            self.assertEqual(plan["run"]["id"], run_dir.name)
            self.assertEqual(plan["bundle"]["path"], "run-bundle.json")
            self.assertGreaterEqual(plan["bundle"]["artifact_count"], 5)
            self.assertFalse(plan["auth"]["token_present"])
            self.assertEqual(plan["auth"]["token_env"], "NULLSTATE_CLOUD_TOKEN")
            self.assertEqual(plan["preflight"]["scrub"]["status"], "not_performed")
            self.assertFalse(plan["preflight"]["scrub"]["scrub_report_present"])
            self.assertFalse(plan["preflight"]["scrub"]["upload_recommended"])
            self.assertIn("Run has not been scrubbed", plan["preflight"]["scrub"]["warnings"][0])
            self.assertIn("Upload plan:", completed.stdout)
            self.assertIn("Run has not been scrubbed", completed.stdout)

    def test_upload_dry_run_records_token_presence_without_leaking_secret(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            run_dir = _minimal_run(runs_dir)
            env = os.environ.copy()
            env["NULLSTATE_CLOUD_TOKEN"] = "super-secret-token"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "upload",
                    run_dir.name,
                    "--runs-dir",
                    str(runs_dir),
                    "--dry-run",
                ],
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            plan_text = (run_dir / "upload-plan.json").read_text(encoding="utf-8")
            plan = json.loads(plan_text)
            self.assertTrue(plan["auth"]["token_present"])
            self.assertNotIn("super-secret-token", plan_text)
            self.assertNotIn("super-secret-token", completed.stdout)

    def test_upload_dry_run_detects_scrubbed_run_copy(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            runs_dir = root / "runs"
            run_dir = _minimal_run(runs_dir)
            scrubbed_runs_dir = root / "scrubbed-runs"

            scrub_completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "scrub",
                    run_dir.name,
                    "--runs-dir",
                    str(runs_dir),
                    "--output-dir",
                    str(scrubbed_runs_dir),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(scrub_completed.returncode, 0, scrub_completed.stderr)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "upload",
                    run_dir.name,
                    "--runs-dir",
                    str(scrubbed_runs_dir),
                    "--dry-run",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            scrubbed_run_dir = scrubbed_runs_dir / run_dir.name
            plan = json.loads((scrubbed_run_dir / "upload-plan.json").read_text(encoding="utf-8"))
            self.assertEqual(plan["preflight"]["scrub"]["status"], "scrubbed")
            self.assertTrue(plan["preflight"]["scrub"]["scrub_report_present"])
            self.assertTrue(plan["preflight"]["scrub"]["upload_recommended"])
            self.assertEqual(plan["preflight"]["scrub"]["scrub_report_path"], "scrub-report.json")
            self.assertEqual(plan["preflight"]["scrub"]["warnings"], [])
            self.assertNotIn("Run has not been scrubbed", completed.stdout)


def _minimal_run(runs_dir: Path) -> Path:
    run_dir = runs_dir / "20260601-120000"
    run_dir.mkdir(parents=True)
    (run_dir / "report.md").write_text("# nullstate Run Report\n\nExploit blocked after remediation\n", encoding="utf-8")
    (run_dir / "findings.json").write_text(
        json.dumps(
            [
                {
                    "rule_id": "AWS_S3_PUBLIC_ACCESS_BLOCK_DISABLED",
                    "severity": "high",
                    "resource_address": "aws_s3_bucket_public_access_block.public_logs",
                    "summary": "S3 public access block controls are disabled.",
                    "evidence": "disabled",
                    "remediation": "enable controls",
                }
            ]
        ),
        encoding="utf-8",
    )
    (run_dir / "metrics.json").write_text(json.dumps({"model_calls": []}), encoding="utf-8")
    (run_dir / "attack-manifest.json").write_text(
        json.dumps({"scenario": "aws-public-s3", "backend": "localstack-aws"}),
        encoding="utf-8",
    )
    (run_dir / "events.jsonl").write_text(
        json.dumps(
            {
                "timestamp": "2026-06-01T12:00:00+00:00",
                "phase": "start",
                "message": "Run started",
                "data": {"scenario": "aws-public-s3", "target": "localstack-aws", "offline": True},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "remediation.patch").write_text("--- a/main.tf\n+++ b/main.tf\n", encoding="utf-8")
    return run_dir


if __name__ == "__main__":
    unittest.main()
