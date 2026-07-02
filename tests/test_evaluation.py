import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nullstate.evaluation import EVAL_RESULTS_SCHEMA_ID, EVAL_SUITE_SCHEMA_ID, load_eval_suite, run_eval_suite, validate_eval_suite


EXAMPLE_SUITE = Path("examples/eval/iac-security-regression.json")


class EvaluationTests(unittest.TestCase):
    def test_loads_valid_eval_suite(self):
        suite = load_eval_suite(EXAMPLE_SUITE)

        self.assertEqual(suite["$schema"], EVAL_SUITE_SCHEMA_ID)
        self.assertEqual(suite["schema_version"], 1)
        self.assertEqual(suite["suite"]["id"], "iac-security-regression")
        self.assertEqual(len(suite["cases"]), 1)
        self.assertEqual(validate_eval_suite(suite), [])

    def test_eval_suite_validation_reports_missing_required_fields(self):
        errors = validate_eval_suite({"schema_version": 1})

        self.assertIn("$schema must reference the nullstate eval-suite schema", errors)
        self.assertIn("suite.id is required", errors)
        self.assertIn("cases must include at least one case", errors)

    def test_eval_suite_schema_document_matches_contract(self):
        schema_path = Path("docs/schemas/eval-suite.schema.json")
        self.assertTrue(schema_path.is_file())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(schema["$id"], EVAL_SUITE_SCHEMA_ID)
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertIn("cases", schema["required"])

    def test_eval_results_schema_document_matches_contract(self):
        schema_path = Path("docs/schemas/eval-results.schema.json")
        self.assertTrue(schema_path.is_file())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(schema["$id"], EVAL_RESULTS_SCHEMA_ID)
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertIn("cases", schema["required"])

    def test_run_eval_suite_writes_results_and_report(self):
        with TemporaryDirectory() as raw_tmp:
            output_dir = Path(raw_tmp) / "eval"

            results = run_eval_suite(EXAMPLE_SUITE, output_dir)

            self.assertEqual(results["$schema"], EVAL_RESULTS_SCHEMA_ID)
            self.assertEqual(results["suite"]["id"], "iac-security-regression")
            self.assertEqual(results["case_count"], 1)
            self.assertEqual(results["passed_count"], 1)
            self.assertEqual(results["failed_count"], 0)
            self.assertEqual(results["cases"][0]["status"], "passed")
            self.assertGreaterEqual(results["cases"][0]["duration_seconds"], 0)
            self.assertEqual(results["cases"][0]["summary"]["finding_count"], 1)
            self.assertEqual(results["cases"][0]["summary"]["attack"]["before"], "success")
            self.assertEqual(results["cases"][0]["summary"]["attack"]["after"], "blocked")
            self.assertIn("artifact_count", results["cases"][0]["metrics"])
            self.assertTrue((output_dir / "eval-results.json").is_file())
            self.assertTrue((output_dir / "eval-report.md").is_file())

    def test_eval_cli_runs_suite_and_writes_results(self):
        with TemporaryDirectory() as raw_tmp:
            output_dir = Path(raw_tmp) / "eval"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "eval",
                    "run",
                    str(EXAMPLE_SUITE),
                    "--output-dir",
                    str(output_dir),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads((output_dir / "eval-results.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["passed_count"], 1)
            self.assertIn("Evaluation results", completed.stdout)


if __name__ == "__main__":
    unittest.main()
