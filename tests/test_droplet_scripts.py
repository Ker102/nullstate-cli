from pathlib import Path
import unittest


class DropletScriptTests(unittest.TestCase):
    def test_qwen_sglang_script_disables_aiter_by_default_for_rocm_smoke_path(self):
        script = Path("scripts/droplet/serve-qwen35-sglang-rocm.sh").read_text(encoding="utf-8")

        self.assertIn('SGLANG_USE_AITER="${SGLANG_USE_AITER:-0}"', script)
        self.assertIn('-e "SGLANG_USE_AITER=${SGLANG_USE_AITER}"', script)

    def test_qwen_vllm_script_provides_red_endpoint_fallback(self):
        script = Path("scripts/droplet/serve-qwen-vllm-rocm.sh").read_text(encoding="utf-8")

        self.assertIn('MODEL_ID="${MODEL_ID:-Qwen/Qwen3-4B-Instruct-2507}"', script)
        self.assertIn('SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-nullstate-qwen3-4b}"', script)
        self.assertIn('GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.40}"', script)
        self.assertIn('-p "127.0.0.1:${HOST_PORT}:${CONTAINER_PORT}"', script)


if __name__ == "__main__":
    unittest.main()
