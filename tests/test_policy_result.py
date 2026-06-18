import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class PolicyResultTests(unittest.TestCase):
    def test_policy_result_exports_threshold_decision_for_existing_run(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            runs_dir = root / "runs"
            run_dir = _minimal_run(runs_dir)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "policy-result",
                    run_dir.name,
                    "--runs-dir",
                    str(runs_dir),
                    "--fail-on-severity",
                    "high",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            result_path = run_dir / "policy-result.json"
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["run_id"], run_dir.name)
            self.assertTrue(payload["failed"])
            self.assertEqual(payload["exit_code"], 2)
            self.assertEqual(payload["max_severity"], "high")
            self.assertEqual(payload["evaluated_finding_count"], 1)
            self.assertIn("Policy result:", completed.stdout)

    def test_policy_result_uses_baseline_to_evaluate_new_findings_only(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            runs_dir = root / "runs"
            run_dir = _minimal_run(runs_dir)
            baseline_path = root / "baseline.json"
            _write_baseline(
                baseline_path,
                "AWS_S3_PUBLIC_ACCESS_BLOCK_DISABLED",
                "aws_s3_bucket_public_access_block.public_logs",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "policy-result",
                    run_dir.name,
                    "--runs-dir",
                    str(runs_dir),
                    "--baseline-file",
                    str(baseline_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads((run_dir / "policy-result.json").read_text(encoding="utf-8"))
            self.assertFalse(payload["failed"])
            self.assertEqual(payload["baseline"]["known_finding_count"], 1)
            self.assertEqual(payload["baseline"]["new_finding_count"], 0)
            self.assertEqual(payload["evaluated_finding_count"], 0)

    def test_policy_result_fails_closed_when_findings_are_missing(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            run_dir = _minimal_run(runs_dir)
            (run_dir / "findings.json").unlink()

            completed = subprocess.run(
                [sys.executable, "-m", "nullstate", "policy-result", run_dir.name, "--runs-dir", str(runs_dir)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 2)
            self.assertIn("findings.json", completed.stderr)
            self.assertFalse((run_dir / "policy-result.json").exists())

    def test_policy_result_fails_closed_when_findings_are_not_a_list(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            run_dir = _minimal_run(runs_dir)
            (run_dir / "findings.json").write_text(json.dumps({"findings": []}), encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, "-m", "nullstate", "policy-result", run_dir.name, "--runs-dir", str(runs_dir)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 2)
            self.assertIn("findings.json", completed.stderr)
            self.assertFalse((run_dir / "policy-result.json").exists())


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
