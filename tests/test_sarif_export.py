import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class SarifExportTests(unittest.TestCase):
    def test_sarif_command_writes_code_scanning_artifact_for_run_findings(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            run_dir = _minimal_run(runs_dir)

            completed = subprocess.run(
                [sys.executable, "-m", "nullstate", "sarif", run_dir.name, "--runs-dir", str(runs_dir)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            sarif_path = run_dir / "nullstate.sarif"
            self.assertTrue(sarif_path.is_file())
            payload = json.loads(sarif_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["version"], "2.1.0")
            run = payload["runs"][0]
            self.assertEqual(run["tool"]["driver"]["name"], "nullstate")
            self.assertEqual(run["tool"]["driver"]["rules"][0]["id"], "AWS_S3_PUBLIC_ACCESS_BLOCK_DISABLED")
            result = run["results"][0]
            self.assertEqual(result["ruleId"], "AWS_S3_PUBLIC_ACCESS_BLOCK_DISABLED")
            self.assertEqual(result["level"], "error")
            self.assertIn("S3 public access block controls are disabled.", result["message"]["text"])
            self.assertNotIn("logicalLocations", result)
            location = result["locations"][0]
            self.assertEqual(
                location["logicalLocations"][0]["fullyQualifiedName"],
                "aws_s3_bucket_public_access_block.public_logs",
            )
            self.assertEqual(result["properties"]["severity"], "high")
            self.assertEqual(result["properties"]["remediation"], "enable controls")
            self.assertIn("SARIF:", completed.stdout)

    def test_sarif_command_accepts_custom_output_path(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            runs_dir = root / "runs"
            run_dir = _minimal_run(runs_dir)
            output_path = root / "exports" / "scan.sarif"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "sarif",
                    run_dir.name,
                    "--runs-dir",
                    str(runs_dir),
                    "--output",
                    str(output_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(output_path.is_file())
            self.assertFalse((run_dir / "nullstate.sarif").exists())


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
    return run_dir


if __name__ == "__main__":
    unittest.main()
