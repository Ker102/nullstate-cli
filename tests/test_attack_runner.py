import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nullstate.attack_runner import run_attack_script


class AttackRunnerTests(unittest.TestCase):
    def test_runs_generated_attack_script_and_captures_command_evidence(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            attack_script = run_dir / "attack.py"
            attack_script.write_text(
                "import argparse\n"
                "parser = argparse.ArgumentParser()\n"
                "parser.add_argument('--target-url')\n"
                "parser.add_argument('--stage')\n"
                "parser.add_argument('--manifest')\n"
                "args = parser.parse_args()\n"
                "print(f'target={args.target_url} stage={args.stage} manifest={args.manifest}')\n",
                encoding="utf-8",
            )
            manifest = run_dir / "attack-manifest.json"
            manifest.write_text('{"scenario": "aws-public-s3"}\n', encoding="utf-8")

            result = run_attack_script(
                attack_script,
                run_dir=run_dir,
                target_url="http://localhost.localstack.cloud:4566",
                stage="before",
                manifest_path=manifest,
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.target_url, "http://localhost.localstack.cloud:4566")
            self.assertEqual(result.stage, "before")
            self.assertEqual(result.command[0], sys.executable)
            self.assertIn("attack.py", result.command[1])
            self.assertIn(str(manifest), result.command)
            self.assertIn(
                f"target=http://localhost.localstack.cloud:4566 stage=before manifest={manifest}",
                result.stdout,
            )
            self.assertEqual(result.stderr, "")
            payload = result.to_dict()
            self.assertEqual(payload["returncode"], 0)
            self.assertIn("started_at", payload)
            self.assertIn("ended_at", payload)
            json.dumps(payload)

    def test_rejects_scripts_outside_the_run_directory(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            run_dir = root / "run"
            run_dir.mkdir()
            outside_script = root / "attack.py"
            outside_script.write_text("print('not allowed')\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                run_attack_script(
                    outside_script,
                    run_dir=run_dir,
                    target_url="http://localhost.localstack.cloud:4566",
                    stage="before",
                )

    def test_rejects_non_attack_script_names(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            script = run_dir / "arbitrary.py"
            script.write_text("print('not allowed')\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                run_attack_script(
                    script,
                    run_dir=run_dir,
                    target_url="http://localhost.localstack.cloud:4566",
                    stage="before",
                )

    def test_rejects_manifest_outside_the_run_directory(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            run_dir = root / "run"
            run_dir.mkdir()
            attack_script = run_dir / "attack.py"
            attack_script.write_text("print('allowed script')\n", encoding="utf-8")
            outside_manifest = root / "attack-manifest.json"
            outside_manifest.write_text("{}", encoding="utf-8")

            with self.assertRaises(ValueError):
                run_attack_script(
                    attack_script,
                    run_dir=run_dir,
                    target_url="http://localhost.localstack.cloud:4566",
                    stage="before",
                    manifest_path=outside_manifest,
                )


if __name__ == "__main__":
    unittest.main()
