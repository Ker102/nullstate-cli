import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nullstate.summary import RUN_SUMMARY_SCHEMA_ID, build_run_summary, validate_run_summary


class RunSummaryTests(unittest.TestCase):
    def test_build_run_summary_returns_agent_friendly_evidence_object(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = _write_run(Path(raw_tmp) / "20260702-120000")

            summary = build_run_summary(run_dir)

            self.assertEqual(summary["$schema"], RUN_SUMMARY_SCHEMA_ID)
            self.assertEqual(summary["schema_version"], 1)
            self.assertEqual(summary["run"]["id"], "20260702-120000")
            self.assertEqual(summary["scenario"]["name"], "aws-public-s3")
            self.assertEqual(summary["scenario"]["evidence_level"], "live-validated")
            self.assertEqual(summary["status"], "failed")
            self.assertEqual(summary["finding_count"], 1)
            self.assertEqual(summary["highest_severity"], "high")
            self.assertEqual(summary["attack"]["before"], "success")
            self.assertEqual(summary["attack"]["after"], "blocked")
            self.assertTrue(summary["remediation_available"])
            self.assertEqual(summary["tokens"]["prompt_tokens"], 12)
            self.assertEqual(summary["tokens"]["completion_tokens"], 20)
            self.assertIn("report", summary["artifacts"])
            self.assertIn("findings", summary["artifacts"])
            self.assertIn("events", summary["artifacts"])
            self.assertEqual(summary["limitations"], [])
            self.assertEqual(validate_run_summary(summary), [])

    def test_summary_reports_missing_optional_artifacts_as_limitations(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp) / "20260702-120000"
            run_dir.mkdir()
            (run_dir / "findings.json").write_text("[]", encoding="utf-8")

            summary = build_run_summary(run_dir)

            self.assertEqual(summary["status"], "passed")
            self.assertIn("events.jsonl missing", summary["limitations"])
            self.assertIn("report.md missing", summary["limitations"])
            self.assertIn("metrics.json missing", summary["limitations"])

    def test_validate_run_summary_reports_contract_errors(self):
        errors = validate_run_summary({"schema_version": 1})

        self.assertIn("$schema must reference the nullstate run-summary schema", errors)
        self.assertIn("run.id is required", errors)
        self.assertIn("status is required", errors)
        self.assertIn("finding_count must be an integer", errors)
        self.assertIn("artifacts must be an object", errors)

    def test_summary_schema_document_matches_contract(self):
        schema_path = Path("docs/schemas/run-summary.schema.json")
        self.assertTrue(schema_path.is_file())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(schema["$id"], RUN_SUMMARY_SCHEMA_ID)
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertIn("scenario", schema["required"])
        self.assertIn("artifacts", schema["required"])

    def test_summary_cli_prints_json_for_latest_run(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            _write_run(runs_dir / "20260702-120000")

            completed = subprocess.run(
                [sys.executable, "-m", "nullstate", "summary", "--runs-dir", str(runs_dir), "--json"],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["run"]["id"], "20260702-120000")
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["attack"]["before"], "success")


def _write_run(run_dir: Path) -> Path:
    run_dir.mkdir(parents=True)
    (run_dir / "findings.json").write_text(
        json.dumps(
            [
                {
                    "severity": "high",
                    "rule_id": "AWS_S3_PUBLIC_ACCESS_BLOCK_DISABLED",
                    "resource": "aws_s3_bucket_public_access_block.public_logs",
                }
            ]
        ),
        encoding="utf-8",
    )
    (run_dir / "events.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "phase": "start",
                        "message": "Run started",
                        "data": {
                            "scenario": "aws-public-s3",
                            "scenario_evidence_level": "live-validated",
                            "scenario_evidence_summary": "LocalStack AWS S3 runtime probe validated.",
                        },
                    }
                ),
                json.dumps(
                    {
                        "phase": "red-team",
                        "message": "Attack attempted before remediation",
                        "data": {"result": {"status": "success"}},
                    }
                ),
                json.dumps(
                    {
                        "phase": "validation",
                        "message": "Attack attempted after remediation",
                        "data": {"result": {"status": "blocked"}},
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "metrics.json").write_text(
        json.dumps(
            {
                "model_calls": [
                    {"prompt_tokens": 5, "completion_tokens": 8, "total_tokens": 13},
                    {"prompt_tokens": 7, "completion_tokens": 12, "total_tokens": 19},
                ]
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "report.md").write_text("# Report\n", encoding="utf-8")
    (run_dir / "remediation.patch").write_text("diff --git a/main.tf b/main.tf\n", encoding="utf-8")
    (run_dir / "run-bundle.json").write_text("{}", encoding="utf-8")
    return run_dir


if __name__ == "__main__":
    unittest.main()
