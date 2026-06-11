import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class EvidenceManifestTests(unittest.TestCase):
    def test_evidence_manifest_writes_artifact_inventory_without_workspace_or_self(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            run_dir = _minimal_run(runs_dir)
            workspace_secret = run_dir / "workspace" / "terraform.tfstate"
            workspace_secret.parent.mkdir()
            workspace_secret.write_text("secret-state", encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "evidence-manifest",
                    run_dir.name,
                    "--runs-dir",
                    str(runs_dir),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest_path = run_dir / "evidence-manifest.json"
            self.assertTrue(manifest_path.is_file())
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["run"]["id"], run_dir.name)
            self.assertEqual(payload["run"]["scenario"], "aws-public-s3")
            self.assertEqual(payload["run"]["target"], "localstack-aws")
            self.assertEqual(payload["artifact_count"], len(payload["artifacts"]))
            paths = [item["path"] for item in payload["artifacts"]]
            self.assertIn("report.md", paths)
            self.assertIn("findings.json", paths)
            self.assertIn("events.jsonl", paths)
            self.assertNotIn("workspace/terraform.tfstate", paths)
            self.assertNotIn("evidence-manifest.json", paths)
            report_artifact = next(item for item in payload["artifacts"] if item["path"] == "report.md")
            expected_report_hash = hashlib.sha256((run_dir / "report.md").read_bytes()).hexdigest()
            self.assertEqual(report_artifact["sha256"], expected_report_hash)
            self.assertRegex(report_artifact["sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(report_artifact["size_bytes"], (run_dir / "report.md").stat().st_size)
            self.assertEqual(payload["signing"]["status"], "unsigned")
            self.assertIsNone(payload["signing"]["signature"])
            self.assertIn("Evidence manifest:", completed.stdout)

    def test_evidence_manifest_accepts_custom_output_path(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            runs_dir = root / "runs"
            run_dir = _minimal_run(runs_dir)
            output_path = root / "exports" / "evidence.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "evidence-manifest",
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
            self.assertFalse((run_dir / "evidence-manifest.json").exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["run"]["id"], run_dir.name)


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
