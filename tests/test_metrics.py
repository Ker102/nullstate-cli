import unittest

from nullstate.metrics import metrics_from_openai_response, parse_vllm_metrics


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


if __name__ == "__main__":
    unittest.main()
