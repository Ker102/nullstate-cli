<a id="enterprise-readiness"></a>
# 企业就绪性

从本地黑客松原型到企业 DevSecOps 的控制清单，区分已强制和团队付费、云、自托管前待添加项。`nullstate` 仍按此边界评估。

<a id="current-controls"></a>
## 当前控制

| 控制 | 状态 | 证据 |
|---|---|---|
| 确定性权威发现 | 已实现 | `src/nullstate/findings.py` |
| 确定性修复 | 已实现 | `src/nullstate/remediation.py` |
| 复制工作区 | 已实现 | 原 IaC 不变 |
| 受限红队 | 已实现 | 仅运行目录 `attack.py` |
| 清单限定探测 | 已实现 | `attack-manifest.json` 含已验证场景、后端、URL、资源提示 |
| 运行时日志 | 已实现 | `red-tool` 输出/时间 |
| 本地目标强制 | 已实现 | 默认拒绝非本地 HTTP |
| 攻击产物哈希 | 已实现 | `red-tool` 含脚本/清单 SHA-256 |
| 截断元数据 | 已实现 | `red-tool` 标记 stdout/stderr 截断 |
| 非破坏脱敏 | 已实现 | `nullstate scrub` 复制并脱敏 |
| 上传预检 | 已实现 | `nullstate upload --dry-run` 记录准备状态并警告原始运行 |
| 上传计划契约 | 已实现 | `docs/schemas/upload-plan.schema.json` 描述且 CLI 验证 |
| 证据分类 | 已实现 | 区分实际、不确定、离线模拟 |
| 本地仪表板/包 | 已实现 | `nullstate dashboard`、`nullstate bundle`、`docs/schemas/run-bundle.schema.json` |
| 红队策略脚手架 | 已实现 | `nullstate policy init`、预设、`run --policy-file` 强制已验证场景、后端、阶段、参数、分类、host、命令、超时、输出 |
| 策略验证产物 | 已实现 | `nullstate policy validate` 可写 `policy-validation.json` |
| 证据完整性 | 已实现 | `nullstate evidence-manifest` 验证 SHA-256 清单，可 HMAC 签名 |
| 清单验证 | 已实现 | `nullstate evidence-verify` 检测缺失/变化、复制、不正确 HMAC |
| 发布来源 | 已实现 | 标签 workflow 写 `release-manifest.json`，证明 `dist/*` |
| 发布 SBOM | 已实现 | 干净安装 wheel，本地/SPDX 验 `sbom.spdx.json`，GitHub 证明 |
| 无密钥签名 | 已实现 | Sigstore/GitHub OIDC |
| 发布演练 | 已实现 | 手动 `workflow_dispatch` 验证，不发布 |
| 修复规则版本 | 已实现 | `remediation.json` 含版本、场景、文件、规则 ID，v1 验证 |

<a id="required-before-enterprise-claims"></a>
## 企业声明前要求

<a id="local-only-enforcement"></a>
### 仅本地强制

默认运行目标仍本地：

- `offline://...`
- `local://...`
- `127.0.0.1`
- `localhost`
- `localhost.localstack.cloud`

默认拒绝非本地 HTTP；真实云需默认关闭的明确 `--allow-live-cloud`。`events.jsonl` 记录批准，红队事件记命令是否开启门禁。`allowed_target_hosts` 可进一步限制精确 host 或 `*.domain`。

<a id="command-allowlist-policy"></a>
### 命令允许策略

保持模板式执行。策略应定义：

- 允许场景
- 允许后端
- 允许生成脚本名
- 允许 CLI 参数
- 最大超时
- stdout/stderr 最大字节
- 允许分类/host 模式

模型可解释路径，不应生成任意 shell 命令。

`nullstate policy init` 创建 JSON，`$schema` 指向 `docs/schemas/nullstate-policy.schema.json`，写前验证。`nullstate policy init --scenario <name>` 为已知组合建窄预设，适合不放行全部脚手架的 CI。`nullstate policy validate` 在执行前检查。`nullstate run --policy-file` 在 `attack.py` 前强制场景、后端、阶段、生成 `attack.py` 参数、分类、host、命令策略、超时和输出上限。非完整策略引擎，但定义未来契约。

`nullstate run --ci` 写有模式的 `ci-summary.json`，含决策、退出码、阈值、数量、基线拆分和前后攻击状态。先按 `docs/schemas/ci-summary.schema.json` 验证，便于自动化依赖。

<a id="event-schema-hardening"></a>
### 事件模式加固

`red-tool` 含首批审计元数据：

- `schema_version`
- `command_policy_id`
- `attack_script_sha256`
- `manifest_sha256`

未来增加更丰富策略；目前已含：

- `stdout_truncated`
- `stderr_truncated`

目前还含：

- `live_cloud_allowed`
- 丰富 `target_classification`，明确开放云门禁时含 `external-http`

这些字段使证据可复现，便于 CI、支持、合规审计。

`nullstate evidence-manifest` 为支持、案例、未来接收加运行清单。记录可分享文件 SHA-256/大小，排除复制工作区、Terraform 内部、Python 缓存、自身、验证输出。`$schema` 为 `docs/schemas/evidence-manifest.schema.json`，写前验。`--signing-key-env` 用环境秘密 HMAC-SHA256，密钥不记录。`nullstate evidence-verify` 重算并写 `evidence-verification.json`；缺失、变化、运行身份不同或签名错退出 `2`。

标签发布写 `release-manifest.json` 哈希，干净安装 wheel 生成 `sbom.spdx.json`；本地结构和 `pyspdxtools` 在清单/证明前验证。GitHub 证明 `dist/*` 来源和 SPDX；Sigstore 为 wheel、sdist、SBOM、清单发布相邻 `.sigstore.json`。供应链来源不同于运行 HMAC。

手动 `dry_run=true` 演练构建、验证、证明、签名、包检查，但不创建 GitHub 发布。

`remediation.json` 在 `remediation.patch` 旁记录规则版本、场景、变化标志、文件、ID。`$schema` 指向 `docs/schemas/remediation-metadata.schema.json`，在报告/包/产物前验证以关联准确规则契约。

`run-bundle.json` 有本地验证，`$schema` 指向 `docs/schemas/run-bundle.schema.json`；`nullstate bundle` 在顶层无效时写前失败。

仪表板展示发现、规则、模式、清单、时间线、摘录。仍单用户文件式；团队历史、RBAC、定期扫描、合规属于付费平台。

<a id="artifact-scrubbing"></a>
### 产物脱敏

公开、上传、附包前 `nullstate scrub` 创建副本并移除：

- LocalStack token
- 模型 key
- 云账户 ID
- Azure 租户/订阅 ID
- 私有端点/IP 图
- Terraform state 值
- 提供商凭据
- 含客户上下文原始提示

`scrub-report.json` 记录文件和匹配规则。

`nullstate upload --dry-run` 检查 `scrub-report.json`，在 `upload-plan.json` 记 `preflight.scrub`；`$schema` 指向 `docs/schemas/upload-plan.schema.json`，写前验。原始运行可本地计划，但 `upload_recommended: false` 并警告。

<a id="evidence-classification"></a>
### 证据分类

企业报告不应夸大，使用：

- `runtime exploit observed`：命令输出证明对象/blob 访问。
- `runtime probe did not observe exploit`：到达目标，修复后阻断/不可用。
- `runtime probe inconclusive`：模拟器、路由、支持无法证明。
- `offline deterministic simulation`：未实际探测。

称已利用时提供观察命令证据，或明确离线模拟。

<a id="near-term-readiness-tasks"></a>
## 近期任务

1. 实际 Azure 验证并说明模拟器限制。
2. 真实云适配器仅有提供商允许清单与批准。

<a id="commercial-boundary"></a>
## 商业边界

开源保持本地/offline、LocalStack、报告、包、个人仪表板。付费聚焦需治理的控制：

- 集中历史
- RBAC/审计
- policy-as-code 允许命令
- 托管模型
- 支持包
- 合规导出
- 定期扫描/警报
- 私有部署支持
