import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nullstate.ci import CI_SUMMARY_SCHEMA_ID, validate_ci_summary


class CliCiModeTests(unittest.TestCase):
    def test_ci_mode_writes_summary_and_exits_nonzero_for_high_findings_by_default(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"

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
            self.assertEqual(summary["$schema"], CI_SUMMARY_SCHEMA_ID)
            self.assertTrue(summary["failed"])
            self.assertEqual(summary["schema_version"], 1)
            self.assertEqual(summary["exit_code"], 2)
            self.assertEqual(summary["fail_on_severity"], "high")
            self.assertEqual(summary["max_severity"], "high")
            self.assertEqual(summary["finding_count"], 1)
            self.assertEqual(summary["run_id"], run_dir.name)
            self.assertIn("CI summary:", completed.stdout)
            self.assertIn("CI summary validation: passed", completed.stdout)

    def test_ci_mode_allows_threshold_above_findings_to_pass(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"

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
                    "--fail-on-severity",
                    "critical",
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
            self.assertEqual(summary["exit_code"], 0)
            self.assertEqual(summary["fail_on_severity"], "critical")
            self.assertEqual(summary["max_severity"], "high")

    def test_ci_summary_validation_reports_contract_errors(self):
        errors = validate_ci_summary({"schema_version": 1})

        self.assertIn("$schema must reference the nullstate ci-summary schema", errors)
        self.assertIn("run_id is required", errors)
        self.assertIn("failed must be a boolean", errors)
        self.assertIn("exit_code must be an integer", errors)
        self.assertIn("baseline must be an object", errors)

    def test_ci_summary_schema_document_matches_generated_contract(self):
        schema_path = Path("docs/schemas/ci-summary.schema.json")
        self.assertTrue(schema_path.is_file())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(schema["$id"], CI_SUMMARY_SCHEMA_ID)
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertIn("baseline", schema["required"])


if __name__ == "__main__":
    unittest.main()
