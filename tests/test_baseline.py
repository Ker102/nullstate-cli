import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class BaselineTests(unittest.TestCase):
    def test_baseline_command_exports_finding_identities(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            run_dir = _minimal_run(runs_dir)
            output = Path(raw_tmp) / "nullstate-baseline.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "baseline",
                    run_dir.name,
                    "--runs-dir",
                    str(runs_dir),
                    "--output",
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["run_id"], run_dir.name)
            self.assertEqual(payload["finding_count"], 1)
            self.assertEqual(
                payload["findings"][0]["identity"],
                "AWS_S3_PUBLIC_ACCESS_BLOCK_DISABLED|aws_s3_bucket_public_access_block.public_logs",
            )
            self.assertIn("Baseline:", completed.stdout)

    def test_ci_baseline_allows_known_high_findings(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            baseline_path = root / "baseline.json"
            _write_baseline(
                baseline_path,
                "AWS_S3_PUBLIC_ACCESS_BLOCK_DISABLED",
                "aws_s3_bucket_public_access_block.public_logs",
            )
            runs_dir = root / "runs"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "run",
                    "examples/aws-public-s3",
                    "--offline",
                    "--mock-agents",
                    "--ci",
                    "--baseline-file",
                    str(baseline_path),
                    "--runs-dir",
                    str(runs_dir),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            run_dir = next(runs_dir.iterdir())
            summary = json.loads((run_dir / "ci-summary.json").read_text(encoding="utf-8"))
            self.assertFalse(summary["failed"])
            self.assertEqual(summary["baseline"]["known_finding_count"], 1)
            self.assertEqual(summary["baseline"]["new_finding_count"], 0)

    def test_ci_baseline_fails_on_new_high_findings(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            baseline_path = root / "baseline.json"
            _write_baseline(baseline_path, "UNRELATED_RULE", "unrelated.resource")
            runs_dir = root / "runs"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "run",
                    "examples/aws-public-s3",
                    "--offline",
                    "--mock-agents",
                    "--ci",
                    "--baseline-file",
                    str(baseline_path),
                    "--runs-dir",
                    str(runs_dir),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertTrue(runs_dir.is_dir(), completed.stderr)
            run_dir = next(runs_dir.iterdir())
            summary = json.loads((run_dir / "ci-summary.json").read_text(encoding="utf-8"))
            self.assertTrue(summary["failed"])
            self.assertEqual(summary["baseline"]["known_finding_count"], 0)
            self.assertEqual(summary["baseline"]["new_finding_count"], 1)


def _write_baseline(path: Path, rule_id: str, resource_address: str) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "findings": [
                    {
                        "identity": f"{rule_id}|{resource_address}",
                        "rule_id": rule_id,
                        "resource_address": resource_address,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


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
