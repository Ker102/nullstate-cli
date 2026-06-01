import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class BundleDashboardTests(unittest.TestCase):
    def test_bundle_command_writes_portable_run_bundle(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            run_dir = _minimal_run(runs_dir)

            completed = subprocess.run(
                [sys.executable, "-m", "nullstate", "bundle", run_dir.name, "--runs-dir", str(runs_dir)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            bundle_path = run_dir / "run-bundle.json"
            self.assertTrue(bundle_path.is_file())
            payload = json.loads(bundle_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["run"]["id"], run_dir.name)
            self.assertEqual(payload["run"]["verdict"], "blocked")
            self.assertEqual(payload["run"]["finding_count"], 1)
            self.assertFalse(payload["scrub"]["workspace_included"])
            self.assertIn("report.md", {artifact["path"] for artifact in payload["artifacts"]})
            self.assertIn("Bundle:", completed.stdout)

    def test_dashboard_command_writes_local_html_dashboard(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            run_dir = _minimal_run(runs_dir)

            completed = subprocess.run(
                [sys.executable, "-m", "nullstate", "dashboard", run_dir.name, "--runs-dir", str(runs_dir)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            dashboard_path = run_dir / "dashboard.html"
            self.assertTrue(dashboard_path.is_file())
            html = dashboard_path.read_text(encoding="utf-8")
            self.assertIn("nullstate local dashboard", html)
            self.assertIn("Evidence timeline", html)
            self.assertIn("AWS_S3_PUBLIC_ACCESS_BLOCK_DISABLED", html)
            self.assertIn("Dashboard:", completed.stdout)


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
        json.dumps(
            {
                "scenario": "aws-public-s3",
                "backend": "localstack-aws",
                "target_url": "offline://aws-public-s3",
                "resources": {"object_key": "evidence.txt"},
            }
        ),
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
