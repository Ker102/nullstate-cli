import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nullstate.evidence_manifest import EVIDENCE_MANIFEST_SCHEMA_ID, validate_evidence_manifest


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
            self.assertEqual(payload["$schema"], EVIDENCE_MANIFEST_SCHEMA_ID)
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
            self.assertIn("Evidence manifest validation: passed", completed.stdout)

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

    def test_evidence_manifest_validation_reports_missing_required_fields(self):
        errors = validate_evidence_manifest({"schema_version": 1})

        self.assertIn("$schema must reference the nullstate evidence-manifest schema", errors)
        self.assertIn("product must be nullstate", errors)
        self.assertIn("run.id is required", errors)
        self.assertIn("artifact_count must match artifacts length", errors)
        self.assertIn("artifacts must be a list", errors)
        self.assertIn("integrity.hash_algorithm must be sha256", errors)
        self.assertIn("signing must be an object", errors)

    def test_evidence_manifest_schema_document_matches_generated_contract(self):
        schema_path = Path("docs/schemas/evidence-manifest.schema.json")

        self.assertTrue(schema_path.is_file())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], EVIDENCE_MANIFEST_SCHEMA_ID)
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertIn("run", schema["required"])
        self.assertIn("artifacts", schema["required"])
        self.assertIn("integrity", schema["required"])
        self.assertIn("signing", schema["required"])

    def test_evidence_manifest_can_be_signed_with_env_key(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            run_dir = _minimal_run(runs_dir)
            env = _signed_env()

            completed = _run_nullstate(
                "evidence-manifest",
                run_dir.name,
                "--runs-dir",
                str(runs_dir),
                "--signing-key-env",
                "NULLSTATE_TEST_SIGNING_KEY",
                env=env,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest_text = (run_dir / "evidence-manifest.json").read_text(encoding="utf-8")
            self.assertNotIn(env["NULLSTATE_TEST_SIGNING_KEY"], manifest_text)
            payload = json.loads(manifest_text)
            self.assertEqual(payload["signing"]["status"], "signed")
            self.assertEqual(payload["signing"]["algorithm"], "hmac-sha256")
            self.assertEqual(payload["signing"]["key_id"], "NULLSTATE_TEST_SIGNING_KEY")
            self.assertRegex(payload["signing"]["signature"], r"^[0-9a-f]{64}$")
            self.assertIn("signing=signed", completed.stdout)

    def test_evidence_verify_passes_for_unchanged_manifest_artifacts(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            run_dir = _minimal_run(runs_dir)
            _run_nullstate("evidence-manifest", run_dir.name, "--runs-dir", str(runs_dir))

            completed = _run_nullstate("evidence-verify", run_dir.name, "--runs-dir", str(runs_dir))

            self.assertEqual(completed.returncode, 0, completed.stderr)
            result_path = run_dir / "evidence-verification.json"
            self.assertTrue(result_path.is_file())
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["run"]["id"], run_dir.name)
            self.assertEqual(payload["manifest"]["path"], "evidence-manifest.json")
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["failure_count"], 0)
            self.assertEqual(payload["failures"], [])
            self.assertGreaterEqual(payload["checked_artifact_count"], 5)
            self.assertIn("Evidence verification:", completed.stdout)
            self.assertIn("status=passed", completed.stdout)

    def test_evidence_verify_checks_signed_manifest(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            run_dir = _minimal_run(runs_dir)
            env = _signed_env()
            _run_nullstate(
                "evidence-manifest",
                run_dir.name,
                "--runs-dir",
                str(runs_dir),
                "--signing-key-env",
                "NULLSTATE_TEST_SIGNING_KEY",
                env=env,
            )

            completed = _run_nullstate(
                "evidence-verify",
                run_dir.name,
                "--runs-dir",
                str(runs_dir),
                "--signing-key-env",
                "NULLSTATE_TEST_SIGNING_KEY",
                env=env,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads((run_dir / "evidence-verification.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["signature"]["status"], "verified")
            self.assertEqual(payload["failure_count"], 0)

    def test_evidence_verify_fails_when_signed_manifest_is_changed(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            run_dir = _minimal_run(runs_dir)
            env = _signed_env()
            _run_nullstate(
                "evidence-manifest",
                run_dir.name,
                "--runs-dir",
                str(runs_dir),
                "--signing-key-env",
                "NULLSTATE_TEST_SIGNING_KEY",
                env=env,
            )
            manifest_path = run_dir / "evidence-manifest.json"
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload["run"]["target"] = "tampered-target"
            manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            completed = _run_nullstate(
                "evidence-verify",
                run_dir.name,
                "--runs-dir",
                str(runs_dir),
                "--signing-key-env",
                "NULLSTATE_TEST_SIGNING_KEY",
                env=env,
            )

            self.assertEqual(completed.returncode, 2, completed.stdout)
            result = json.loads((run_dir / "evidence-verification.json").read_text(encoding="utf-8"))
            self.assertEqual(result["signature"]["status"], "failed")
            self.assertIn({"path": None, "reason": "invalid_signature"}, result["failures"])

    def test_evidence_verify_fails_when_artifact_hash_changes(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            run_dir = _minimal_run(runs_dir)
            _run_nullstate("evidence-manifest", run_dir.name, "--runs-dir", str(runs_dir))
            (run_dir / "report.md").write_text("tampered report\n", encoding="utf-8")

            completed = _run_nullstate("evidence-verify", run_dir.name, "--runs-dir", str(runs_dir))

            self.assertEqual(completed.returncode, 2, completed.stderr)
            result_path = run_dir / "evidence-verification.json"
            self.assertTrue(result_path.is_file(), completed.stderr)
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["failure_count"], 1)
            self.assertEqual(payload["failures"][0]["path"], "report.md")
            self.assertEqual(payload["failures"][0]["reason"], "sha256_mismatch")
            self.assertRegex(payload["failures"][0]["expected_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(payload["failures"][0]["actual_sha256"], r"^[0-9a-f]{64}$")

    def test_evidence_verify_accepts_custom_manifest_path(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            runs_dir = root / "runs"
            run_dir = _minimal_run(runs_dir)
            manifest_path = root / "exports" / "evidence.json"
            _run_nullstate(
                "evidence-manifest",
                run_dir.name,
                "--runs-dir",
                str(runs_dir),
                "--output",
                str(manifest_path),
            )

            completed = _run_nullstate(
                "evidence-verify",
                run_dir.name,
                "--runs-dir",
                str(runs_dir),
                "--manifest",
                str(manifest_path),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads((run_dir / "evidence-verification.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["manifest"]["path"], str(manifest_path))

    def test_evidence_verify_fails_when_manifest_run_id_does_not_match(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            source_run = _minimal_run(runs_dir, run_id="20260601-120000")
            target_run = _minimal_run(runs_dir, run_id="20260601-130000")
            _run_nullstate("evidence-manifest", source_run.name, "--runs-dir", str(runs_dir))
            copied_manifest = target_run / "evidence-manifest.json"
            copied_manifest.write_text((source_run / "evidence-manifest.json").read_text(encoding="utf-8"), encoding="utf-8")

            completed = _run_nullstate("evidence-verify", target_run.name, "--runs-dir", str(runs_dir))

            self.assertEqual(completed.returncode, 2, completed.stdout)
            payload = json.loads((target_run / "evidence-verification.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "failed")
            self.assertIn(
                {"path": None, "reason": "manifest_run_id_mismatch", "expected_run_id": target_run.name, "actual_run_id": source_run.name},
                payload["failures"],
            )

    def test_evidence_verify_reports_malformed_manifest_as_cli_error(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            run_dir = _minimal_run(runs_dir)
            (run_dir / "evidence-manifest.json").write_text("{", encoding="utf-8")

            completed = _run_nullstate("evidence-verify", run_dir.name, "--runs-dir", str(runs_dir))

            self.assertEqual(completed.returncode, 2)
            self.assertIn("Invalid JSON file", completed.stderr)
            self.assertFalse((run_dir / "evidence-verification.json").exists())


def _minimal_run(runs_dir: Path, *, run_id: str = "20260601-120000") -> Path:
    run_dir = runs_dir / run_id
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


def _run_nullstate(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "nullstate", *args],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def _signed_env() -> dict[str, str]:
    import os

    env = os.environ.copy()
    env["NULLSTATE_TEST_SIGNING_KEY"] = "test-only-signing-key"
    return env


if __name__ == "__main__":
    unittest.main()
