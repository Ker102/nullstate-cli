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


class _RoleEndpointHandler(BaseHTTPRequestHandler):
    request_log: list[dict[str, str]] = []

    def do_POST(self):  # noqa: N802
        if self.path != "/v1/chat/completions":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length))
        role = self.server.role_name  # type: ignore[attr-defined]
        _RoleEndpointHandler.request_log.append({"role": role, "model": body["model"]})
        response = {
            "choices": [{"message": {"content": f"{role} endpoint response"}}],
            "usage": {
                "prompt_tokens": 10 if role == "red" else 20,
                "completion_tokens": 5 if role == "red" else 8,
                "total_tokens": 15 if role == "red" else 28,
            },
        }
        self._send_json(response)

    def do_GET(self):  # noqa: N802
        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return
        role = self.server.role_name  # type: ignore[attr-defined]
        payload = (
            f'# HELP vllm:request_success_total Requests by role {role}.\n'
            "# TYPE vllm:request_success_total counter\n"
            f'vllm:request_success_total{{model_name="{role}-model"}} 1.0\n'
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

    def test_uses_separate_red_and_blue_model_endpoints(self):
        _RoleEndpointHandler.request_log = []
        red_server = HTTPServer(("127.0.0.1", 0), _RoleEndpointHandler)
        red_server.role_name = "red"  # type: ignore[attr-defined]
        blue_server = HTTPServer(("127.0.0.1", 0), _RoleEndpointHandler)
        blue_server.role_name = "blue"  # type: ignore[attr-defined]
        servers = [red_server, blue_server]
        threads = [threading.Thread(target=server.serve_forever, daemon=True) for server in servers]
        for thread in threads:
            thread.start()

        try:
            with TemporaryDirectory() as raw_tmp:
                root = Path(raw_tmp)
                runs_dir = root / "runs"
                env = os.environ.copy()
                env["NULLSTATE_RED_LLM_BASE_URL"] = f"http://127.0.0.1:{red_server.server_port}"
                env["NULLSTATE_BLUE_LLM_BASE_URL"] = f"http://127.0.0.1:{blue_server.server_port}"

                completed = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "nullstate",
                        "run",
                        "examples/azure-public-blob",
                        "--offline",
                        "--red-model",
                        "red-model",
                        "--blue-model",
                        "blue-model",
                        "--runs-dir",
                        str(runs_dir),
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                    env=env,
                )

                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(
                    _RoleEndpointHandler.request_log,
                    [{"role": "red", "model": "red-model"}, {"role": "blue", "model": "blue-model"}],
                )
                run_dir = next(runs_dir.iterdir())
                metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
                self.assertEqual(metrics["model_calls"][0]["total_tokens"], 15)
                self.assertEqual(metrics["model_calls"][1]["total_tokens"], 28)
                self.assertEqual(metrics["endpoints"]["red"]["before"]["endpoint_type"], "self-hosted")
                self.assertEqual(metrics["endpoints"]["blue"]["before"]["endpoint_type"], "self-hosted")
                self.assertTrue((run_dir / "vllm-metrics-red-before.prom").exists())
                self.assertTrue((run_dir / "vllm-metrics-blue-after.prom").exists())
        finally:
            for server in servers:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
