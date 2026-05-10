import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class CliTests(unittest.TestCase):
    def test_root_command_prints_launch_screen(self):
        completed = subprocess.run(
            [sys.executable, "-m", "nullstate"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Autonomous Purple-Team Sandbox", completed.stdout)
        self.assertIn("nullstate status", completed.stdout)
        self.assertIn("nullstate sandbox up localstack-aws", completed.stdout)

    def test_doctor_offline_exits_successfully(self):
        completed = subprocess.run(
            [sys.executable, "-m", "nullstate", "doctor", "--offline"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Offline mode", completed.stdout)

    def test_offline_run_creates_report_artifacts(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            demo_dir = root / "demo"
            runs_dir = root / "runs"

            init_completed = subprocess.run(
                [sys.executable, "-m", "nullstate", "init-demo", "azure-public-blob", "--output", str(demo_dir)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(init_completed.returncode, 0, init_completed.stderr)

            run_completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nullstate",
                    "run",
                    str(demo_dir),
                    "--offline",
                    "--runs-dir",
                    str(runs_dir),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(run_completed.returncode, 0, run_completed.stderr)
            reports = list(runs_dir.glob("*/report.md"))
            findings = list(runs_dir.glob("*/findings.json"))
            metrics = list(runs_dir.glob("*/metrics.json"))
            self.assertEqual(len(reports), 1)
            self.assertEqual(len(findings), 1)
            self.assertEqual(len(metrics), 1)
            self.assertIn("Exploit blocked after remediation", reports[0].read_text(encoding="utf-8"))
            self.assertIn('container_access_type = "container"', (demo_dir / "main.tf").read_text(encoding="utf-8"))
            self.assertIn("Next", run_completed.stdout)
            self.assertIn("nullstate report", run_completed.stdout)

    def test_report_without_run_id_opens_latest_nested_report(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            older = runs_dir / "live-azure-model" / "20260509-190000"
            latest = runs_dir / "live-aws-model" / "20260509-200601"
            older.mkdir(parents=True)
            latest.mkdir(parents=True)
            (older / "report.md").write_text("older report", encoding="utf-8")
            (latest / "report.md").write_text("latest aws report", encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, "-m", "nullstate", "report", "--runs-dir", str(runs_dir)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("latest aws report", completed.stdout)
            self.assertIn("Report:", completed.stdout)

    def test_report_finds_run_id_inside_nested_runs_directory(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            report_dir = runs_dir / "live-aws-model" / "20260509-200601"
            report_dir.mkdir(parents=True)
            (report_dir / "report.md").write_text("nested report", encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, "-m", "nullstate", "report", "20260509-200601", "--runs-dir", str(runs_dir)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("nested report", completed.stdout)

    def test_console_safe_text_replaces_unprintable_chars_for_legacy_encoding(self):
        from nullstate.cli import _console_safe_text

        report_text = "safe text with model checkmark ✅"

        self.assertEqual(_console_safe_text(report_text, encoding="utf-8"), report_text)
        self.assertEqual(_console_safe_text(report_text, encoding="cp1252"), "safe text with model checkmark ?")

    def test_status_prints_workflow_state_and_next_commands(self):
        with TemporaryDirectory() as raw_tmp:
            runs_dir = Path(raw_tmp) / "runs"
            report_dir = runs_dir / "live-aws-model" / "20260509-200601"
            report_dir.mkdir(parents=True)
            (report_dir / "report.md").write_text("aws report", encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, "-m", "nullstate", "status", "--runs-dir", str(runs_dir), "--sandbox", "localstack-aws"],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Latest run", completed.stdout)
            self.assertIn("20260509-200601", completed.stdout)
            self.assertIn("LLM endpoints", completed.stdout)
            self.assertIn("Next", completed.stdout)
            self.assertIn("nullstate sandbox status localstack-aws", completed.stdout)
            self.assertIn("nullstate run examples/aws-public-s3", completed.stdout)


if __name__ == "__main__":
    unittest.main()
