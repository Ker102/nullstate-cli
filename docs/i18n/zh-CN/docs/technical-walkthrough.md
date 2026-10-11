<a id="technical-walkthrough"></a>
# 技术详解

本文说明 `nullstate` 从第一个 CLI 命令到最终报告产物的工作过程。本文面向希望了解实现流程、安全边界和当前扩展点的审查人员。

<a id="what-nullstate-runs"></a>
## Nullstate 运行什么

`nullstate` 是一个本地优先的基础设施即代码紫队循环。当前实现主要针对 Terraform 存储暴露场景：

- AWS S3 公共访问阻止功能被禁用
- Azure Blob 容器允许公共访问

它还包含 Kubernetes、Docker Compose、本地部署数字孪生和通用计划审查的离线场景脚手架。

CLI 结合了三个层次：

1. 用于发现项、修复和通过/失败验证的确定性安全逻辑。
2. 用于 LocalStack 等本地执行目标的沙箱适配器。
3. 通过 OpenAI 兼容端点进行模型辅助的红队和蓝队推理。

模型辅助推理和解释。它不是判断漏洞是否存在或修复是否有效的权威依据。

<a id="demo-command-flow"></a>
## 演示命令流程

典型离线流程：

```powershell
nullstate
nullstate status
nullstate run examples/aws-public-s3 --offline
nullstate report
```

典型的 LocalStack AWS 实时执行流程：

```powershell
nullstate sandbox up localstack-aws
nullstate sandbox status localstack-aws
nullstate run examples/aws-public-s3 --target localstack-aws
nullstate report
```

典型的 LocalStack Azure 实时执行流程：

```powershell
nullstate sandbox up localstack-azure
nullstate sandbox status localstack-azure
nullstate run examples/azure-public-blob --target localstack-azure
nullstate report
```

有可用的自托管模型端点时，使用自定义提供商并设置一个共享端点：

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_LLM_BASE_URL = "http://127.0.0.1:8000"
```

或者设置角色专用端点：

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
```

对于自备密钥的用户，托管提供商预设可以省去端点配置：

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
```

`claude` 预设也可通过 Anthropic 的 OpenAI SDK 兼容层使用，但在原生 Claude 适配器出现之前，应将其视为实验性功能。

<a id="runtime-modes"></a>
## 运行模式

<a id="offline-mode"></a>
### 离线模式

`--offline` 跳过 Terraform 运行及云模拟器调用。CLI 使用静态 IaC 解析和确定性场景行为。此模式用于在没有 Docker、LocalStack 或 GPU 的情况下进行可重复的演示、测试和开发。

重要细节：`--offline` 不会自动禁用模型调用。如果配置了模型端点环境变量，红蓝代理调用仍会使用这些端点。如果需要完全确定性且不使用模型的行为，请使用 `--mock-agents`。

<a id="live-localstack-mode"></a>
### LocalStack 实时执行模式

实时模式将 Terraform 项目复制到运行工作区，执行 Terraform 自动化命令，以 LocalStack 为目标，运行红蓝循环，在复制的工作区中应用修复，然后再次验证。

原始 Terraform 目录不会被修改。修复发生在：

```text
runs/<run-id>/workspace/
```

<a id="model-endpoint-mode"></a>
### 模型端点模式

模型端点必须提供 OpenAI 兼容 API。这样，同一 CLI 集成便可用于本地 vLLM、SGLang、托管提供商预设或自定义代理。

提供商解析遵循以下顺序：

1. 角色专用 CLI 参数或环境变量值
2. 共享 CLI 参数或环境变量值
3. 提供商预设的默认 URL
4. 未配置端点时回退到确定性模拟代理

`google` 预设解析为 Gemini 的 OpenAI 兼容端点。`claude` 预设解析为 Anthropic 的 OpenAI SDK 兼容端点。`custom` 和 `openai-compatible` 模式需要基础 URL，除非已提供角色专用 URL。

如果响应中提供了 `usage` 字段，CLI 会从中记录模型 token 数和延迟。它还尝试从端点抓取 Prometheus 风格的 `/metrics`，并将原始指标快照写入运行目录。

<a id="end-to-end-execution-path"></a>
## 端到端执行路径

<a id="1-command-entry"></a>
### 1. 命令入口

入口：

```text
src/nullstate/cli.py
```

`run` 命令接收：

- Terraform 目录
- 目标后端或 `auto`
- 场景或 `auto`
- 离线/模拟参数
- 运行产物目录
- 红蓝模型设置

如果未提供命令，CLI 会打印带品牌标识的启动界面以及可能的后续命令。

<a id="2-scenario-inference"></a>
### 2. 场景推断

相关文件：

```text
src/nullstate/scenario_detection.py
src/nullstate/scenarios.py
```

使用 `--scenario auto` 时，CLI 会检查 IaC 目录，将输入映射到已知场景。例如：

- `examples/aws-public-s3` 映射到 `aws-public-s3`
- `examples/azure-public-blob` 映射到 `azure-public-blob`

场景定义选择默认沙箱后端。用户仍可通过 `--target` 覆盖此设置。

<a id="3-sandbox-backend-selection"></a>
### 3. 沙箱后端选择

相关文件：

```text
src/nullstate/sandbox.py
```

沙箱后端定义：

- 后端名称
- 目标 IaC 类型
- 执行模式
- Docker 镜像
- 启动/停止命令
- 运行时探针

当前后端包括：

| 后端 | 用途 |
|---|---|
| `localstack-aws` | 实时执行 AWS 风格的存储场景 |
| `localstack-azure` | 实时执行 Azure 风格的存储场景 |
| `kind-kubernetes` | Kubernetes 场景脚手架 |
| `docker-compose` | Docker Compose 数字孪生脚手架 |
| `microvm-onprem` | 本地部署数字孪生脚手架 |
| `plan-only` | 无运行时的分析模式 |

`nullstate sandbox up` 启动后端。`nullstate sandbox status` 在适用时检查 Docker 和 HTTP 可达性。

<a id="4-run-workspace-creation"></a>
### 4. 创建运行工作区

CLI 创建一个新的运行目录：

```text
runs/<run-id>/
```

它将输入的 Terraform 目录复制到：

```text
runs/<run-id>/workspace/
```

这使原始项目保持完整。复制时会排除 Terraform 状态、`.terraform`、缓存的计划以及运行目录。

<a id="5-terraform-plan-loading"></a>
### 5. 加载 Terraform 计划

相关文件：

```text
src/nullstate/terraform.py
```

在实时模式下，Terraform 流程使用适合自动化的命令：

```text
terraform init -input=false
terraform plan -out=tfplan -input=false
terraform show -json tfplan
```

在离线模式下，CLI 对受支持的演示测试样例使用静态 Terraform 解析器。这使测试和演示在没有外部运行时依赖的情况下也能保持可重复性。

Terraform 命令结果写入：

```text
runs/<run-id>/events.jsonl
```

<a id="6-finding-detection"></a>
### 6. 检测发现项

相关文件：

```text
src/nullstate/findings.py
```

确定性检测器识别受支持的风险配置。例如：

- Azure Blob 容器的设置为 `container_access_type = "blob"` 或 `"container"`
- Azure 存储账户允许嵌套公共项
- AWS S3 公共访问阻止控制项被禁用

发现项以结构化 JSON 写入：

```text
runs/<run-id>/findings.json
```

这些确定性的发现项数据是后续运行过程的权威依据。

<a id="7-red-team-model-reasoning"></a>
### 7. 红队模型推理

相关文件：

```text
src/nullstate/agents.py
```

红队代理接收内部指令和场景证据。用户在运行过程中不会手动向模型发送提示。

红队模型返回攻击推理，例如：

- 匿名读取 S3 对象的路径
- 匿名读取 Azure Blob 容器的路径
- 可能需要收集的证据

如果未配置端点，该角色会回退到确定性模拟输出。

<a id="8-constrained-attack-script-execution"></a>
### 8. 受限攻击脚本执行

相关文件：

```text
src/nullstate/attack.py
src/nullstate/attack_runner.py
```

`nullstate` 写入生成的攻击产物：

```text
runs/<run-id>/attack.py
runs/<run-id>/attack-manifest.json
```

清单记录场景、后端、目标 URL 和资源提示，供场景探针使用，同时不会赋予模型构造任意命令的能力。它包含指向 `docs/schemas/attack-manifest.schema.json` 的 `$schema` 指针，`nullstate run` 会在受限探针执行前验证清单。

随后，受限执行器只执行该生成的脚本。它强制执行以下边界：

- 脚本名称必须恰好为 `attack.py`
- 脚本必须直接位于当前运行目录中
- 执行使用当前 Python 解释器
- 不接受任意 shell 命令
- 动态输入仅限于 `--target-url`、`--stage` 和运行目录中生成的 `attack-manifest.json`

执行器在修复前后记录命令证据：

```json
{
  "phase": "red-tool",
  "message": "Allowlisted attack command completed",
  "data": {
    "command": ["python", "attack.py", "--target-url", "...", "--stage", "before", "--manifest", "..."],
    "target_url": "...",
    "stage": "before",
    "returncode": 0,
    "stdout": "...",
    "stderr": "",
    "started_at": "...",
    "ended_at": "...",
    "duration_seconds": 0.123
  }
}
```

这使报告获得真实命令证据，同时避免红队代理不受限制地访问工具。

此层的企业级防护措施：

- 命令策略基于场景模板。模型可以对攻击路径进行推理，但不能选择任意 shell 命令。
- `nullstate policy init` 创建带有模式引用的策略文件，并在写入前验证；`policy init --scenario <name>` 为单个场景/后端组合创建更严格的预设。`run --policy-file` 在执行前强制检查允许的场景、后端、阶段、生成的 `attack.py` 参数、目标分类、目标主机允许列表、命令策略 ID、超时上限和输出大小上限。
- `nullstate policy validate` 在不运行场景的情况下检查策略文件，并可写入 `policy-validation.json` 作为 CI 证据。
- 除非明确提供并记录 `--allow-live-cloud`，运行时目标始终为本地沙箱端点。
- `red-tool` 事件包含命令模式版本，以及生成的 `attack.py` 和清单的可重复性哈希。
- 在上传、附加到工单或长期保留证据之前，应限制探针标准输出和标准错误输出的大小。
- 报告必须区分实际观察到的运行时证据、确定性模拟和模拟器结果不确定的探针。

<a id="9-deterministic-remediation"></a>
### 9. 确定性修复

相关文件：

```text
src/nullstate/remediation.py
```

蓝队模型解释修复，但补丁本身由确定性修复逻辑生成。

对于 Azure Blob 暴露，修复设置为：

```hcl
allow_nested_items_to_be_public = false
container_access_type           = "private"
```

对于 AWS S3 暴露，修复将公共访问阻止控制项设置为 `true`：

```hcl
block_public_acls       = true
block_public_policy     = true
ignore_public_acls      = true
restrict_public_buckets = true
```

差异写入：

```text
runs/<run-id>/remediation.patch
```

<a id="10-re-plan-and-validation"></a>
### 10. 重新生成计划并验证

修复后，CLI 再次加载已修复的工作区。在实时模式下，它针对复制的工作区执行 Terraform 计划/应用步骤。在离线模式下，它重新解析更新后的文件。

检测器再次运行。如果发现项已消失，确定性攻击模拟返回：

```text
Red after: blocked
```

受限攻击脚本也会再次运行，使用：

```text
--stage after
```

该修复后命令的输出会被记录为另一个 `red-tool` 事件。

<a id="11-report-and-metrics"></a>
### 11. 报告和指标

相关文件：

```text
src/nullstate/report.py
src/nullstate/metrics.py
```

每次运行会写入：

| 产物 | 用途 |
|---|---|
| `events.jsonl` | 完整事件时间线 |
| `findings.json` | 结构化漏洞发现项 |
| `attack.py` | 生成的受限攻击产物 |
| `attack-manifest.json` | 经模式验证的场景、后端、目标 URL 和资源提示，供受限探针使用 |
| `remediation.patch` | Terraform 修复差异 |
| `remediation.json` | 经模式验证的确定性修复规则集元数据 |
| `metrics.json` | 模型调用、token 数、延迟和端点指标 |
| `ci-summary.json` | 使用 `--ci` 时生成的经模式验证、机器可读的 CI 判定 |
| `policy-result.json` | 针对已有运行的独立 JSON 策略决策 |
| `report.md` | 人类可读的摘要 |
| `evidence-manifest.json` | 使用 `nullstate evidence-manifest` 时生成的可共享运行证据 SHA-256 清单 |
| `evidence-verification.json` | 使用 `nullstate evidence-verify` 时生成的清单验证结果 |
| `upload-plan.json` | 使用 `nullstate upload --dry-run` 时生成的不联网上传计划 |
| `workspace/` | 复制并修复后的 IaC 工作区 |

`nullstate report` 默认打开最新报告，包括嵌套在命名运行目录下的报告。

`remediation.json` 包含指向 `docs/schemas/remediation-metadata.schema.json` 的 `$schema` 指针，生成的修复元数据在被报告、证据包和运行产物使用前会先经过验证。

`nullstate bundle` 写入 `run-bundle.json`，这是用于本地仪表板、CI 上传、支持包和未来 Nullstate Cloud 摄取的可移植证据契约。证据包包含指向 `docs/schemas/run-bundle.schema.json` 的 `$schema` 指针，CLI 会在写入前验证证据包结构。如果可用，证据包还包含 `remediation.json` 元数据，使下游工具能够显示修复规则集版本和规则 ID。

`nullstate dashboard` 写入 `dashboard.html`，这是一个免费的单次运行本地仪表板，无需登录云端即可打开。它汇总发现项、修复元数据、证据包模式元数据、产物清单、证据时间线和报告摘录。

`nullstate sarif` 写入 `nullstate.sarif`，这是一个 SARIF 2.1.0 导出，每个发现项对应一个结果，用于 CI 和代码扫描上传。

`nullstate run --ci` 写入 `ci-summary.json`，当运行的原始发现项达到或超过 `--fail-on-severity` 时，以代码 `2` 退出。该摘要包含指向 `docs/schemas/ci-summary.schema.json` 的 `$schema` 指针，并在写入前验证，为 CI 提供稳定的策略关卡，同时不改变供人阅读的报告。

`nullstate baseline` 写入发现项身份标识的 JSON 基线。使用 `nullstate run --ci --baseline-file` 时，已知基线发现项仍然可见，但 CI 失败阈值仅针对新增发现项进行评估。

`nullstate policy-result` 为已有运行写入相同类型的阈值和基线决策，无需重新运行场景。

`nullstate evidence-manifest` 写入 `evidence-manifest.json`，这是可共享运行产物的确定性完整性清单。该清单包含指向 `docs/schemas/evidence-manifest.schema.json` 的 `$schema` 指针，CLI 会在写入前验证其结构。它排除复制的工作区、Terraform 内部文件、Python 缓存、清单文件本身以及验证输出。使用 `--signing-key-env` 可通过环境中的秘密值附加共享密钥 HMAC-SHA256 证据签名；这是对运行证据的签名，并非公钥软件包来源证明。

`nullstate evidence-verify` 在重新计算记录的产物哈希和文件大小后写入 `evidence-verification.json`。它只检查清单中列出的产物，忽略无关的新增文件，在提供 `--signing-key-env` 时验证 HMAC 签名，并在记录的产物缺失、发生变化、从其他运行复制而来或签名无效时，以代码 `2` 退出。

`nullstate upload --dry-run` 写入 `upload-plan.json`，更新 `run-bundle.json`，记录预定端点及 token 环境变量，并确认 token 是否存在，但不保存 token 值。计划包含指向 `docs/schemas/upload-plan.schema.json` 的 `$schema` 指针，CLI 会在写入前验证其结构。它还记录脱敏预检状态：原始运行以 `upload_recommended: false` 发出警告，而包含 `scrub-report.json` 的脱敏副本会被标记为可上传，供未来摄取流程使用。

`nullstate scrub` 在 `scrubbed-runs/` 下创建运行的脱敏副本，并写入 `scrub-report.json`。它保持原始运行不变，并拒绝覆盖已有的脱敏副本。

<a id="security-boundaries"></a>
## 安全边界

重要边界如下：

- 默认不以真实云资源为目标。
- Terraform 更改在复制的工作区中进行。
- 红队模型不会获得 shell 访问权限。
- 攻击执行器只执行运行目录中生成的 `attack.py`。
- 秘密值从环境变量或被忽略的本地 env 文件加载。
- 发布前必须审查运行产物。
- 在公开发布案例研究、CI 上传或共享支持包之前，应运行 `nullstate scrub`。
- 在以任何非本地云端点为目标之前，必须提供 `--allow-live-cloud`。

<a id="extension-points"></a>
## 扩展点

<a id="new-scenario"></a>
### 新场景

添加或更新：

```text
src/nullstate/scenarios.py
src/nullstate/scenario_detection.py
src/nullstate/findings.py
src/nullstate/remediation.py
src/nullstate/attack.py
examples/<scenario-name>/
tests/
```

<a id="new-sandbox-backend"></a>
### 新沙箱后端

在以下文件中添加后端元数据和命令：

```text
src/nullstate/sandbox.py
```

然后为以下命令添加测试：

- `sandbox list`
- `sandbox status`
- `sandbox up --dry-run`
- `sandbox down`

<a id="richer-red-tooling"></a>
### 更丰富的红队工具

下一步安全扩展不是自由形式的 shell 访问，而应是按场景设置的允许列表：

- 生成的 Python 探针
- 固定命令模板
- 仅限本地的目标 URL
- 严格超时
- 完整事件日志
- 不继承真实云凭据

请参阅[企业就绪性](enterprise-readiness.md)，了解在将运行时探针定位为团队或企业证据之前应完成的控制检查清单。

<a id="test-coverage"></a>
## 测试覆盖

主要验证命令：

```powershell
python -m unittest discover -s tests -v
python -m ruff check src tests
python -m mypy src
```

实用的冒烟测试：

```powershell
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --runs-dir runs/red-tool-smoke
python -m nullstate report --runs-dir runs/red-tool-smoke
```

冒烟运行应显示：

- 修复前有一个发现项
- `Red before: success`
- `Red after: blocked`
- 两个 `red-tool` 事件，记录在 `events.jsonl` 中
