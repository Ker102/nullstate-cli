import json
import threading
import sys
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

from nullstate.attack import write_attack_script
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
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["command_policy_id"], "generated-attack-script-v1")
            self.assertEqual(payload["returncode"], 0)
            self.assertEqual(payload["target_classification"], "local-http")
            self.assertFalse(payload["live_cloud_allowed"])
            self.assertRegex(str(payload["attack_script_sha256"]), r"^[0-9a-f]{64}$")
            self.assertRegex(str(payload["manifest_sha256"]), r"^[0-9a-f]{64}$")
            self.assertFalse(payload["stdout_truncated"])
            self.assertFalse(payload["stderr_truncated"])
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

    def test_rejects_non_local_http_targets_by_default(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            attack_script = run_dir / "attack.py"
            attack_script.write_text("print('allowed script')\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "must be local"):
                run_attack_script(
                    attack_script,
                    run_dir=run_dir,
                    target_url="https://example.com",
                    stage="before",
                )

    def test_allows_non_local_http_target_only_with_live_cloud_gate(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            attack_script = run_dir / "attack.py"
            attack_script.write_text(
                "import argparse\n"
                "parser = argparse.ArgumentParser()\n"
                "parser.add_argument('--target-url')\n"
                "parser.add_argument('--stage')\n"
                "args = parser.parse_args()\n"
                "print(f'target={args.target_url} stage={args.stage}')\n",
                encoding="utf-8",
            )

            result = run_attack_script(
                attack_script,
                run_dir=run_dir,
                target_url="https://example.com",
                stage="before",
                allow_live_cloud=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.target_classification, "external-http")
            payload = result.to_dict()
            self.assertTrue(payload["live_cloud_allowed"])
            self.assertIn("target=https://example.com stage=before", result.stdout)

    def test_allows_offline_local_loopback_and_localstack_targets(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            attack_script = run_dir / "attack.py"
            attack_script.write_text(
                "import argparse\n"
                "parser = argparse.ArgumentParser()\n"
                "parser.add_argument('--target-url')\n"
                "parser.add_argument('--stage')\n"
                "parser.add_argument('--manifest')\n"
                "parser.parse_args()\n",
                encoding="utf-8",
            )

            targets = {
                "offline://aws-public-s3": "offline",
                "local://kind-kubernetes/k8s-privileged-pod": "local",
                "http://127.0.0.1:4566": "local-http",
                "http://localhost:4566": "local-http",
                "http://s3.localhost.localstack.cloud:4566": "local-http",
            }
            for target_url, expected_classification in targets.items():
                with self.subTest(target_url=target_url):
                    result = run_attack_script(
                        attack_script,
                        run_dir=run_dir,
                        target_url=target_url,
                        stage="before",
                    )
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(result.target_classification, expected_classification)

    def test_truncates_large_stdout_and_marks_event_metadata(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            attack_script = run_dir / "attack.py"
            attack_script.write_text("print('x' * 200)\n", encoding="utf-8")

            result = run_attack_script(
                attack_script,
                run_dir=run_dir,
                target_url="offline://aws-public-s3",
                stage="before",
                max_output_bytes=20,
            )

            self.assertTrue(result.stdout_truncated)
            self.assertFalse(result.stderr_truncated)
            self.assertIn("... truncated ...", result.stdout)
            self.assertLess(len(result.stdout), 60)

    def test_timeout_returns_structured_command_evidence(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            attack_script = run_dir / "attack.py"
            attack_script.write_text(
                "import time\n"
                "print('starting slow probe')\n"
                "time.sleep(10)\n",
                encoding="utf-8",
            )

            result = run_attack_script(
                attack_script,
                run_dir=run_dir,
                target_url="offline://aws-public-s3",
                stage="before",
                timeout_seconds=1,
            )

            self.assertEqual(result.returncode, 124)
            self.assertIn("timed out after 1 seconds", result.stderr)
            self.assertEqual(result.target_classification, "offline")
            self.assertFalse(result.live_cloud_allowed)
            json.dumps(result.to_dict())

    def test_generated_aws_attack_script_reads_public_evidence_object(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), _EvidenceObjectHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with TemporaryDirectory() as raw_tmp:
                run_dir = Path(raw_tmp)
                attack_script = run_dir / "attack.py"
                write_attack_script(attack_script, "aws-public-s3")
                manifest = run_dir / "attack-manifest.json"
                manifest.write_text(
                    json.dumps(
                        {
                            "resources": {
                                "bucket_name": "public-bucket",
                                "object_key": "evidence.txt",
                            }
                        }
                    ),
                    encoding="utf-8",
                )

                result = run_attack_script(
                    attack_script,
                    run_dir=run_dir,
                    target_url=f"http://127.0.0.1:{server.server_port}",
                    stage="before",
                    manifest_path=manifest,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("candidate_url=", result.stdout)
                self.assertIn("/public-bucket/evidence.txt", result.stdout)
                self.assertIn("status=200", result.stdout)
                self.assertIn("body_excerpt=nullstate public evidence", result.stdout)
        finally:
            server.shutdown()
            server.server_close()

    def test_generated_azure_attack_script_reads_public_evidence_blob(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), _EvidenceObjectHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with TemporaryDirectory() as raw_tmp:
                run_dir = Path(raw_tmp)
                attack_script = run_dir / "attack.py"
                write_attack_script(attack_script, "azure-public-blob")
                manifest = run_dir / "attack-manifest.json"
                manifest.write_text(
                    json.dumps(
                        {
                            "resources": {
                                "storage_account_name": "acct",
                                "container_name": "secrets",
                                "blob_name": "evidence.txt",
                            }
                        }
                    ),
                    encoding="utf-8",
                )

                result = run_attack_script(
                    attack_script,
                    run_dir=run_dir,
                    target_url=f"http://127.0.0.1:{server.server_port}",
                    stage="before",
                    manifest_path=manifest,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("candidate_url=", result.stdout)
                self.assertIn("/acct/secrets/evidence.txt", result.stdout)
                self.assertIn("status=200", result.stdout)
                self.assertIn("body_excerpt=nullstate public evidence", result.stdout)
                self.assertIn("runtime_exploit_observed=true", result.stdout)
        finally:
            server.shutdown()
            server.server_close()


class _EvidenceObjectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in {"/public-bucket/evidence.txt", "/acct/secrets/evidence.txt"}:
            body = b"nullstate public evidence"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    unittest.main()
