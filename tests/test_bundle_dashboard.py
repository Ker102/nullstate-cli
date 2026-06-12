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
            self.assertEqual(payload["evidence"]["remediation"]["ruleset_version"], "2026.06.1")
            self.assertIn("AWS_S3_BLOCK_PUBLIC_ACCESS", payload["evidence"]["remediation"]["rules_applied"])
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

    def test_scrub_command_writes_sanitized_run_copy(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            runs_dir = root / "runs"
            output_dir = root / "scrubbed-runs"
            run_dir = _minimal_run(runs_dir)
            scrub_fixture_text = (
                "LOCALSTACK_AUTH_TOKEN=fixture-value\n"
                "NULLSTATE_LLM_API_KEY=fixture-value\n"
                "ARM_CLIENT_SECRET=fixture-value\n"
                "tenant=11111111-2222-3333-4444-555555555555\n"
                "private=10.20.30.40 loopback=127.0.0.1\n"
            )
            (run_dir / "events.jsonl").write_text(scrub_fixture_text, encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "scrub",
                    run_dir.name,
                    "--runs-dir",
                    str(runs_dir),
                    "--output-dir",
                    str(output_dir),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            scrubbed_dir = output_dir / run_dir.name
            self.assertTrue(scrubbed_dir.is_dir())
            self.assertEqual(run_dir.joinpath("events.jsonl").read_text(encoding="utf-8"), scrub_fixture_text)
            scrubbed_events = scrubbed_dir.joinpath("events.jsonl").read_text(encoding="utf-8")
            self.assertIn("<redacted-localstack-auth-token>", scrubbed_events)
            self.assertIn("<redacted-model-api-key>", scrubbed_events)
            self.assertIn("<redacted-azure-client-secret>", scrubbed_events)
            self.assertIn("<redacted-uuid>", scrubbed_events)
            self.assertIn("<redacted-private-ipv4>", scrubbed_events)
            self.assertIn("127.0.0.1", scrubbed_events)
            scrub_report = json.loads(scrubbed_dir.joinpath("scrub-report.json").read_text(encoding="utf-8"))
            self.assertEqual(scrub_report["schema_version"], 1)
            self.assertIn("events.jsonl", scrub_report["files_changed"])
            self.assertEqual(scrub_report["redaction_counts"]["localstack_auth_token"], 1)
            self.assertEqual(scrub_report["redaction_counts"]["private_ipv4"], 1)
            self.assertIn("Scrubbed run:", completed.stdout)

    def test_scrub_command_refuses_to_overwrite_existing_output(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            runs_dir = root / "runs"
            output_dir = root / "scrubbed-runs"
            run_dir = _minimal_run(runs_dir)
            (output_dir / run_dir.name).mkdir(parents=True)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "scrub",
                    run_dir.name,
                    "--runs-dir",
                    str(runs_dir),
                    "--output-dir",
                    str(output_dir),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("already exists", completed.stderr)


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
    (run_dir / "remediation.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "scenario": "aws-public-s3",
                "changed": True,
                "changed_files": ["workspace/main.tf"],
                "ruleset_version": "2026.06.1",
                "rules_applied": ["AWS_S3_BLOCK_PUBLIC_ACCESS", "AWS_S3_REMOVE_PUBLIC_READ_POLICY"],
            }
        ),
        encoding="utf-8",
    )
    return run_dir


if __name__ == "__main__":
    unittest.main()
