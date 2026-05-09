import json
import os
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory


class _OpenAiCompatHandler(BaseHTTPRequestHandler):
    request_count = 0

    def do_POST(self):  # noqa: N802
        if self.path != "/v1/chat/completions":
            self.send_response(404)
            self.end_headers()
            return
        _OpenAiCompatHandler.request_count += 1
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length))
        response = {
            "choices": [{"message": {"content": f"fake {body['model']} response"}}],
            "usage": {
                "prompt_tokens": 11,
                "completion_tokens": 7,
                "total_tokens": 18,
            },
        }
        self._send_json(response)

    def do_GET(self):  # noqa: N802
        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return
        payload = (
            '# HELP vllm:num_requests_running Number of requests currently running.\n'
            "# TYPE vllm:num_requests_running gauge\n"
            'vllm:num_requests_running{model_name="fake-model"} 0.0\n'
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload.encode("utf-8"))

    def log_message(self, format, *args):  # noqa: A002
        return

    def _send_json(self, payload):
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


class CliModelEndpointTests(unittest.TestCase):
    def test_offline_iac_mode_still_uses_configured_model_endpoint(self):
        _OpenAiCompatHandler.request_count = 0
        server = HTTPServer(("127.0.0.1", 0), _OpenAiCompatHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"

        try:
            with TemporaryDirectory() as raw_tmp:
                root = Path(raw_tmp)
                runs_dir = root / "runs"
                env = os.environ.copy()
                env["NULLSTATE_LLM_BASE_URL"] = base_url

                completed = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "nullstate",
                        "run",
                        "examples/azure-public-blob",
                        "--offline",
                        "--blue-model",
                        "fake-model",
                        "--red-model",
                        "fake-model",
                        "--runs-dir",
                        str(runs_dir),
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                    env=env,
                )

                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(_OpenAiCompatHandler.request_count, 2)
                run_dir = next(runs_dir.iterdir())
                metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
                self.assertEqual(metrics["model_calls"][0]["model"], "fake-model")
                self.assertEqual(metrics["model_calls"][0]["total_tokens"], 18)
                self.assertEqual(metrics["endpoint"]["before"]["endpoint_type"], "self-hosted")
                self.assertTrue((run_dir / "vllm-metrics-before.prom").exists())
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
