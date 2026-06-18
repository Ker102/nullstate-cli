import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from nullstate.metrics import (
    classify_endpoint,
    collect_run_metrics,
    gpu_snapshot,
    metrics_from_openai_response,
    parse_vllm_metrics,
)


class MetricsTests(unittest.TestCase):
    def test_metrics_from_openai_response_counts_tokens_and_throughput(self):
        metrics = metrics_from_openai_response(
            role="blue",
            model="gemma-4-31b-it",
            latency_seconds=2.0,
            response_payload={
                "usage": {
                    "prompt_tokens": 1200,
                    "completion_tokens": 300,
                    "total_tokens": 1500,
                }
            },
        )

        self.assertEqual(metrics.role, "blue")
        self.assertEqual(metrics.prompt_tokens, 1200)
        self.assertEqual(metrics.completion_tokens, 300)
        self.assertEqual(metrics.total_tokens, 1500)
        self.assertEqual(metrics.output_tokens_per_second, 150.0)

    def test_parse_vllm_prometheus_metrics_extracts_key_counters(self):
        parsed = parse_vllm_metrics(
            """
            vllm:generation_tokens_total{model_name="demo"} 27453.0
            vllm:request_success_total{finished_reason="stop",model_name="demo"} 131.0
            vllm:num_requests_running{model_name="demo"} 3.0
            vllm:gpu_cache_usage_perc{model_name="demo"} 0.73
            """
        )

        self.assertEqual(parsed["generation_tokens_total"], 27453.0)
        self.assertEqual(parsed["request_success_total"], 131.0)
        self.assertEqual(parsed["num_requests_running"], 3.0)
        self.assertEqual(parsed["gpu_cache_usage_perc"], 0.73)

    def test_classifies_offline_managed_and_amd_endpoints(self):
        self.assertEqual(classify_endpoint(base_url=None, offline=True), "offline")
        self.assertEqual(classify_endpoint(base_url="https://api.fireworks.ai/inference/v1", offline=False), "managed")
        self.assertEqual(classify_endpoint(base_url="https://api.openai.com/v1", offline=False), "managed")
        self.assertEqual(
            classify_endpoint(base_url="https://openai.com.evil.example/v1", offline=False),
            "amd-gpu-hosted",
        )
        self.assertEqual(classify_endpoint(base_url="http://localhost:8000", offline=False), "self-hosted")
        self.assertEqual(classify_endpoint(base_url="http://10.10.0.5:8000", offline=False), "amd-gpu-hosted")

    def test_collect_run_metrics_writes_vllm_snapshots(self):
        with TemporaryDirectory() as raw_tmp:
            run_dir = Path(raw_tmp)
            response = Mock()
            response.text = 'vllm:generation_tokens_total{model_name="demo"} 42.0\n'
            response.raise_for_status.return_value = None

            with patch("nullstate.metrics.requests.get", return_value=response):
                summary = collect_run_metrics(
                    run_dir=run_dir,
                    base_url="http://10.10.0.5:8000",
                    offline=False,
                    stage="before",
                )

            self.assertEqual(summary["endpoint_type"], "amd-gpu-hosted")
            self.assertEqual(summary["vllm_metrics"]["generation_tokens_total"], 42.0)
            self.assertTrue((run_dir / "vllm-metrics-before.prom").exists())

    def test_gpu_snapshot_is_available_without_gpu_tools(self):
        snapshot = gpu_snapshot(command_runner=lambda command: None)

        self.assertEqual(snapshot["status"], "unavailable")
        self.assertIn("amd-smi", snapshot["attempted"])
        self.assertIn("rocm-smi", snapshot["attempted"])


if __name__ == "__main__":
    unittest.main()
