<a id="model-serving-runbook"></a>
# 模型服务运维手册

本项目使用 OpenAI 兼容端点，让 CLI 可连接本地 vLLM/SGLang、托管提供商预设或自定义代理。

自托管 AMD GPU 端点用 `NULLSTATE_LLM_PROVIDER=custom`。需要托管 Gemini 备用且不要求用户提供 base URL 时，以 Google AI Studio key 配合 `NULLSTATE_LLM_PROVIDER=google`。`NULLSTATE_LLM_PROVIDER=claude` 仅作为实验性 Anthropic OpenAI 兼容路径；生产依赖 Claude 专属功能前需原生适配器。

<a id="recommended-mi300x-split"></a>
## 推荐 MI300X 分工

独立测试红/蓝角色时使用两个容器：

| 角色 | 服务栈 | 首个模型 | 原因 |
|---|---|---|---|
| 红队 | vLLM ROCm 备用 | `Qwen/Qwen3-4B-Instruct-2507` | 此模型已在 MI300X droplet 上通过 vLLM 成功启动，提供稳定红队端点。 |
| 实验红队 | SGLang ROCm | `Qwen/Qwen3.5-9B` 或 `Qwen/Qwen3.5-35B-A3B` | 保留为拓展路径；当前 SGLang 镜像在 droplet 导入不兼容 `aiter` 模块。 |
| 蓝队 | vLLM ROCm | 先 `google/gemma-4-E4B-it`，再 `google/gemma-4-26B-A4B-it` 或 `google/gemma-4-31B-it` | Gemma 4 支持需要较新的 vLLM ROCm 镜像；先小后大。 |

单台 1x MI300X droplet 不要先用 Nemotron 3 Super。公开模型卡给出的 BF16/FP8 硬件需求远大于单台 MI300X。将其保留为未来多 GPU 目标或托管端点比较。

<a id="start-stable-red-qwen-endpoint"></a>
## 启动稳定红队 Qwen 端点

先用此 vLLM 路径，避开 DigitalOcean ROCm 镜像观察到的 SGLang/Quark/AITER 导入失败。

```bash
MODEL_ID=Qwen/Qwen3-4B-Instruct-2507 \
SERVED_MODEL_NAME=nullstate-qwen3-4b \
HOST_PORT=8001 \
GPU_MEMORY_UTILIZATION=0.40 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen-vllm-rocm.sh
```

<a id="start-experimental-red-qwen35-sglang-endpoint"></a>
## 启动实验红队 Qwen3.5 SGLang 端点

在 droplet 运行：

```bash
cd /opt/nullstate

MODEL_ID=Qwen/Qwen3.5-9B \
SERVED_MODEL_NAME=nullstate-qwen35-9b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

Qwen SGLang 脚本默认设置 `SGLANG_USE_AITER=0`。DigitalOcean ROCm 上，容器可能启动时报 `ImportError: aiter is required when SGLANG_USE_AITER is set to True` 并退出；冒烟测试优先稳定启动，不优先 AITER 内核。SGLang 按整数解析：用 `0` 或 `1`，不用 `false` 或 `true`。仅确认镜像有匹配 `aiter` 构建后重新启用：

```bash
SGLANG_USE_AITER=1 \
MODEL_ID=Qwen/Qwen3.5-9B \
SERVED_MODEL_NAME=nullstate-qwen35-9b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

首次冒烟测试后使用更强红队模型：

```bash
MODEL_ID=Qwen/Qwen3.5-35B-A3B \
SERVED_MODEL_NAME=nullstate-qwen35-35b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

<a id="start-blue-gemma-4-endpoint"></a>
## 启动蓝队 Gemma 4 端点

在 droplet 运行：

```bash
MODEL_ID=google/gemma-4-E4B-it \
SERVED_MODEL_NAME=nullstate-gemma4-e4b \
HOST_PORT=8002 \
bash /path/to/nullstate-cli/scripts/droplet/serve-gemma4-vllm-rocm.sh
```

E4B 稳定后进行更大规模蓝队分析：

```bash
MODEL_ID=google/gemma-4-26B-A4B-it \
SERVED_MODEL_NAME=nullstate-gemma4-26b-a4b \
HOST_PORT=8002 \
MAX_MODEL_LEN=32768 \
bash /path/to/nullstate-cli/scripts/droplet/serve-gemma4-vllm-rocm.sh
```

<a id="tunnel-to-local-windows"></a>
## 隧道连接本地 Windows

从 Windows PowerShell：

```powershell
ssh -i "$env:USERPROFILE\Documents\AMDhackkey" -N `
  -L 8001:127.0.0.1:8001 `
  -L 8002:127.0.0.1:8002 `
  root@<droplet-ip>
```

然后在本地配置 nullstate：

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
python -m nullstate run examples/aws-public-s3 --target localstack-aws --scenario aws-public-s3 --red-model nullstate-qwen3-4b --blue-model nullstate-gemma4-e4b
```

仅需静态 IaC 解析且无 Terraform apply 时用 `--offline`；仅需无模型调用时用 `--mock-agents`。

托管备用示例：

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
python -m nullstate run examples/aws-public-s3 --offline --red-model gemini-3.5-flash --blue-model gemini-3.5-flash
```

<a id="evidence-collection"></a>
## 证据收集

在 droplet：

```bash
bash /path/to/nullstate-cli/scripts/droplet/collect-endpoint-evidence.sh http://127.0.0.1:8001 nullstate-qwen3-4b
bash /path/to/nullstate-cli/scripts/droplet/collect-endpoint-evidence.sh http://127.0.0.1:8002 nullstate-gemma4-e4b
```

保存生成证据目录和 nullstate 运行产物：

- `models.json`
- `metrics.prom`
- `chat-completion.json`
- `host-snapshot.txt`
- `runs/<id>/metrics.json`
- `runs/<id>/vllm-metrics-red-*.prom`
- `runs/<id>/vllm-metrics-blue-*.prom`
