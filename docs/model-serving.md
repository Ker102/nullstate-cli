# Model Serving Runbook

This project uses OpenAI-compatible local endpoints so the CLI does not care whether the model is served by vLLM, SGLang, or a managed fallback.

## Recommended MI300X Split

Use two containers when testing red and blue roles independently:

| Role | Serving stack | First model | Reason |
|---|---|---|---|
| Red | vLLM ROCm fallback | `Qwen/Qwen3-4B-Instruct-2507` | This model has already booted successfully on the MI300X droplet with vLLM and gives us a stable red endpoint. |
| Red experimental | SGLang ROCm | `Qwen/Qwen3.5-9B` or `Qwen/Qwen3.5-35B-A3B` | Keep this as a stretch path; the current SGLang image imports incompatible `aiter` modules on the droplet. |
| Blue | vLLM ROCm | `google/gemma-4-E4B-it` first, then `google/gemma-4-26B-A4B-it` or `google/gemma-4-31B-it` | Gemma 4 support requires a current vLLM ROCm image; start small, then scale. |

Do not start with Nemotron 3 Super on the single 1x MI300X droplet. The public model cards list much larger hardware requirements for the BF16/FP8 releases than one MI300X provides. Keep it in the case study as a future multi-GPU target or managed-endpoint comparison.

## Start Stable Red Qwen Endpoint

Use this vLLM path first. It avoids the SGLang/Quark/AITER import failure observed on the DigitalOcean ROCm image.

```bash
MODEL_ID=Qwen/Qwen3-4B-Instruct-2507 \
SERVED_MODEL_NAME=nullstate-qwen3-4b \
HOST_PORT=8001 \
GPU_MEMORY_UTILIZATION=0.40 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen-vllm-rocm.sh
```

## Start Experimental Red Qwen3.5 SGLang Endpoint

Run on the droplet:

```bash
cd /opt/nullstate

MODEL_ID=Qwen/Qwen3.5-9B \
SERVED_MODEL_NAME=nullstate-qwen35-9b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

The Qwen SGLang script sets `SGLANG_USE_AITER=0` by default. On the DigitalOcean ROCm image, the SGLang container can exit during startup with `ImportError: aiter is required when SGLANG_USE_AITER is set to True`; the smoke-test path favors a stable boot over AITER-specific kernels. SGLang parses this value as an integer, so use `0` or `1`, not `false` or `true`. Re-enable it only after confirming the container image has a matching `aiter` build:

```bash
SGLANG_USE_AITER=1 \
MODEL_ID=Qwen/Qwen3.5-9B \
SERVED_MODEL_NAME=nullstate-qwen35-9b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

For a stronger red model after the first smoke test:

```bash
MODEL_ID=Qwen/Qwen3.5-35B-A3B \
SERVED_MODEL_NAME=nullstate-qwen35-35b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

## Start Blue Gemma 4 Endpoint

Run on the droplet:

```bash
MODEL_ID=google/gemma-4-E4B-it \
SERVED_MODEL_NAME=nullstate-gemma4-e4b \
HOST_PORT=8002 \
bash /path/to/nullstate-cli/scripts/droplet/serve-gemma4-vllm-rocm.sh
```

For larger blue-team analysis after the E4B endpoint is stable:

```bash
MODEL_ID=google/gemma-4-26B-A4B-it \
SERVED_MODEL_NAME=nullstate-gemma4-26b-a4b \
HOST_PORT=8002 \
MAX_MODEL_LEN=32768 \
bash /path/to/nullstate-cli/scripts/droplet/serve-gemma4-vllm-rocm.sh
```

## Tunnel To Local Windows

From Windows PowerShell:

```powershell
ssh -i "$env:USERPROFILE\Documents\AMDhackkey" -N `
  -L 8001:127.0.0.1:8001 `
  -L 8002:127.0.0.1:8002 `
  root@<droplet-ip>
```

Then configure nullstate locally:

```powershell
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
python -m nullstate run examples/aws-public-s3 --target localstack-aws --scenario aws-public-s3 --red-model nullstate-qwen3-4b --blue-model nullstate-gemma4-e4b
```

Use `--offline` only when you want static IaC parsing without Terraform apply. Use `--mock-agents` only when you want no model calls.

## Evidence Collection

On the droplet:

```bash
bash /path/to/nullstate-cli/scripts/droplet/collect-endpoint-evidence.sh http://127.0.0.1:8001 nullstate-qwen3-4b
bash /path/to/nullstate-cli/scripts/droplet/collect-endpoint-evidence.sh http://127.0.0.1:8002 nullstate-gemma4-e4b
```

Save the generated evidence directory plus the nullstate run artifacts:

- `models.json`
- `metrics.prom`
- `chat-completion.json`
- `host-snapshot.txt`
- `runs/<id>/metrics.json`
- `runs/<id>/vllm-metrics-red-*.prom`
- `runs/<id>/vllm-metrics-blue-*.prom`
