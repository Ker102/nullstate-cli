<a id="runbook"></a>
# 运维手册

<a id="local-offline-demo"></a>
## 本地离线演示

```powershell
python -m pip install -e .
python -m nullstate doctor --offline
python -m nullstate status
python -m nullstate run examples/azure-public-blob --offline
python -m nullstate report
```

录制前运行所有离线场景：

```powershell
python -m nullstate run examples/aws-public-s3 --offline
python -m nullstate run examples/k8s-privileged-pod --offline
python -m nullstate run examples/compose-exposed-admin --offline
python -m nullstate run examples/onprem-ssh-password --offline
python -m nullstate run examples/generic-plan-review --offline
```

`run` 默认 `--scenario auto` 和 `--target auto`。录制特定适配器路径时保留明确 `--scenario`、`--target`。

<a id="sandbox-discovery"></a>
## 沙箱发现

```powershell
python -m nullstate status
python -m nullstate sandbox list
python -m nullstate sandbox status localstack-azure
python -m nullstate sandbox up localstack-azure --dry-run
```

多数命令输出 `Next` 表。不确定配置、沙箱探测可达性或最新报告时用 `python -m nullstate status`。

<a id="localstack-azure-setup"></a>
## LocalStack Azure 设置

设置：

```powershell
$env:LOCALSTACK_AUTH_TOKEN = "<token>"
```

然后：

```powershell
python -m nullstate sandbox up localstack-azure
python -m nullstate sandbox status localstack-azure
```

若 `sandbox up localstack-azure` 报告容器未保持运行，检查：

```powershell
docker logs localstack-azure
```

若日志说账户未启用 Azure Emulator，停止并解决授权再重试。Azure 镜像大，反复重试可能耗用大量磁盘。

token 保存在本地 env 时保持未跟踪。先自动发现 `.env.local`，再 `.env`：

```powershell
python -m nullstate sandbox up localstack-azure
python -m nullstate sandbox up localstack-aws
```

仅 env 在别处时用 `--env-file`：

```powershell
python -m nullstate sandbox up localstack-aws --env-file .env.local
```

Docker Compose 替代：

```powershell
$env:LOCALSTACK_AUTH_TOKEN = "<token>"
docker compose -f docker-compose.localstack-azure.yml up
```

Compose 可从 shell 或 `docker-compose.localstack-azure.yml` 旁本地 `.env` 读取 `${LOCALSTACK_AUTH_TOKEN}`：

```env
LOCALSTACK_AUTH_TOKEN=your-token-here
```

Git 忽略 `.env`。绝不提交 token；也可存别处并明确传入：

```powershell
docker compose --env-file .env.local -f docker-compose.localstack-azure.yml up
```

服务内 `env_file:` 是向容器注入变量，与此不同。这里需要 Compose 插值，在启动前替换 `${LOCALSTACK_AUTH_TOKEN}`。

<a id="reports-and-run-lookup"></a>
## 报告与运行查找

打开默认 `runs/` 最新报告：

```powershell
python -m nullstate report
```

打开命名证据文件夹最新报告：

```powershell
python -m nullstate report --runs-dir runs/live-aws-model
```

即使嵌套在命名文件夹也可用已知 ID：

```powershell
python -m nullstate report 20260509-200601 --runs-dir runs
```

发布、支持或公开案例前创建脱敏副本：

```powershell
python -m nullstate scrub --runs-dir runs
python -m nullstate scrub 20260509-200601 --runs-dir runs --output-dir scrubbed-runs
```

`scrub` 在 `scrubbed-runs/` 写副本，不改原始；拒绝覆盖已有副本。分享前审查 `scrub-report.json`。

<a id="first-tagged-release-checklist"></a>
## 首个标签发布清单

首个产品标签前使用。合并冻结已在 2026-06-18 解除，但标签/发布仍需所有者明确批准。常规修改走功能分支和受保护 PR。

确认候选 PR 检查通过：

```powershell
gh pr checks 24
```

不创建 GitHub 发布的演练：

```powershell
gh workflow run Release --field dry_run=true
gh run list --workflow Release --limit 1
```

验证 wheel 本地安装后提供 `nullstate`：

```powershell
python scripts/release/install_smoke.py
```

获批合并/标签后检查发布：

```powershell
gh release view v0.1.0
gh release download v0.1.0 --dir dist
```

验证来源与 SBOM 证明：

```powershell
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli --predicate-type https://spdx.dev/Document/v2.3
```

验证 wheel Sigstore 包：

```powershell
$wheel = Get-ChildItem dist\nullstate-*.whl | Select-Object -First 1
cosign verify-blob $wheel.FullName --bundle "$($wheel.FullName).sigstore.json" --certificate-identity "https://github.com/Ker102/nullstate-cli/.github/workflows/release.yml@refs/tags/v0.1.0" --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

确认资源包括：

- wheel 与源码发行包
- `release-manifest.json`
- `sbom.spdx.json`
- 主要产物相邻 `.sigstore.json` 包

<a id="model-endpoint-setup"></a>
## 模型端点设置

自托管 vLLM/SGLang 或服务两个角色的私有 OpenAI 兼容代理设置：

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_LLM_BASE_URL = "http://localhost:8000"
$env:NULLSTATE_LLM_API_KEY = "<optional>"
```

然后正常运行。

Google AI Studio / Gemini 设置预设和 key；CLI 补全兼容 base URL：

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
python -m nullstate run examples/azure-public-blob --red-model gemini-3.5-flash --blue-model gemini-3.5-flash
```

Claude 的 `claude` 预设使用 Anthropic OpenAI SDK 兼容层：

```powershell
$env:NULLSTATE_LLM_PROVIDER = "claude"
$env:NULLSTATE_LLM_API_KEY = "<anthropic-api-key>"
python -m nullstate run examples/azure-public-blob --red-model claude-sonnet-4-6 --blue-model claude-sonnet-4-6
```

Claude 兼容是实验性；未来需专属功能时添加原生 Anthropic 适配器，不勉强扩展兼容包装。

两个容器/隧道设置角色端点：

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
$env:NULLSTATE_RED_LLM_API_KEY = "<optional-red-token>"
$env:NULLSTATE_BLUE_LLM_API_KEY = "<optional-blue-token>"
python -m nullstate run examples/azure-public-blob --red-model nullstate-red --blue-model nullstate-blue
```

单次也可用 `--llm-provider`、`--red-provider`、`--blue-provider`、`--red-base-url`、`--blue-base-url`。角色未设回退 `NULLSTATE_LLM_PROVIDER`、`NULLSTATE_LLM_BASE_URL`、`NULLSTATE_LLM_API_KEY`。显式 URL 覆盖预设以支持自定义网关/fixture。

无角色端点时回退确定性模拟。可在 AMD GPU 访问前开发 LocalStack；模型用于 MI300X 证据和 token/吞吐指标，非确定性利用/修复的必要条件。

`--offline` 控制 Terraform/云执行而非模型。共享/角色端点已设时仍调用它并静态解析 IaC：

```powershell
$env:NULLSTATE_LLM_BASE_URL = "http://127.0.0.1:8001"
python -m nullstate run examples/azure-public-blob --offline --blue-model nullstate-qwen3-4b --red-model nullstate-qwen3-4b
```

明确不要模型调用时用 `--mock-agents`：

```powershell
python -m nullstate run examples/azure-public-blob --offline --mock-agents
```

<a id="amd-developer-cloud--digitalocean-path"></a>
## AMD Developer Cloud / DigitalOcean 路径

用[AMD 计算策略](compute-strategy.md)作部署清单。先建无 GPU 基线，有权限再接 MI300X。

当前双容器 Qwen3.5/Gemma 4 见[模型服务](model-serving.md)。

<a id="fireworks-fallback"></a>
## Fireworks 备用

AMD 访问延迟时将 `NULLSTATE_LLM_BASE_URL` 指向托管端点，保留流程。证据标为托管推理，非私有 GPU 推理。

<a id="metrics-evidence"></a>
## 指标证据

配置端点后尝试抓取：

```text
<NULLSTATE_LLM_BASE_URL>/metrics
<NULLSTATE_RED_LLM_BASE_URL>/metrics
<NULLSTATE_BLUE_LLM_BASE_URL>/metrics
```

若有 vLLM Prometheus 指标，写入：

- `vllm-metrics-before.prom`
- `vllm-metrics-after.prom`
- 红/蓝端点不同时的 `vllm-metrics-red-before.prom` 及角色快照
- `metrics.json` 中解析计数器

本地 GPU 快照先用 `amd-smi` 后 `rocm-smi`。都无则 `metrics.json` 记 `status: unavailable`，不让运行失败。

<a id="work-you-can-do-before-amd-gpu-access"></a>
## AMD GPU 访问前的工作

等待支持时准备：

- DigitalOcean 项目和防火墙
- SSH key 与最小权限
- 无 GPU droplet 冒烟测试
- Docker 安装/更新策略
- GitHub secret/环境名称
- 基于 `.env.example` 的本地 `.env`
- 脱敏 workflow、PR 检查、离线演示截图
- 可用的 LocalStack Azure token/访问

<a id="artifact-review-before-publishing"></a>
## 发布前产物审查

检查：

- `runs/<id>/report.md`
- `runs/<id>/findings.json`
- `runs/<id>/events.jsonl`
- `runs/<id>/remediation.json`
- `runs/<id>/metrics.json`
- `runs/<id>/vllm-metrics-before.prom`
- `runs/<id>/vllm-metrics-after.prom`
- `runs/<id>/remediation.patch`

不得发布秘密、真实租户/订阅 ID、私有端点或 Terraform state。
