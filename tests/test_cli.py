import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class CliTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
