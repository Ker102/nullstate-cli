<a id="security-model"></a>
# 安全模型

<a id="assets"></a>
## 资产

| 资产 | 重要性 | 敏感度 |
|---|---|---|
| Terraform 输入 | 描述基础设施及可能的秘密 | 中/高 |
| 运行产物 | 包含发现、日志、补丁和模型证据 | 中 |
| 模型端点密钥 | 提供 LLM 访问 | 高 |
| LocalStack 认证 token | 启动 LocalStack Azure 模拟器 | 高 |
| Terraform state | 可能包含敏感基础设施数据 | 高 |

<a id="trust-boundaries"></a>
## 信任边界

- 操作者 shell 到 nullstate CLI。
- CLI 到沙箱后端。
- CLI 到模型端点。
- 代理指令到允许工具执行。
- 本地产物到公开仓库文档。

<a id="identities"></a>
## 身份

- 操作者：运行 CLI 的可信人类。
- 红队代理：部分可信攻击角色，限本地沙箱。
- 蓝队代理：部分可信修复角色。
- 外部模型服务器：仅信任配置端点行为。
- CI 执行器：最低权限临时自动化身份。
- 客户 AI 代理：部分可信非人类主体，可用专用代理身份、工作负载身份、服务主体、IAM 角色、托管身份或用户委托权限。
- 代理工具/运行时身份：由代理宿主、网关、连接器、插件、MCP 服务器或下游工具使用的独立主体。

身份分析必须保留以下区别：

- 代理自身身份和权限
- 请求操作的人类用户或工作负载
- 委托/代表他人的权限
- 运行时和工具身份
- 下游凭据及 token audience
- 最终资源和操作

两种身份共同授权时，报告不得只将委托操作归因于人类或代理。

外部代理的有效联合身份是必要但不充分条件。高影响授权应在可用时依赖运行时证据：

- 工作负载身份绑定预期运行时属性
- 部署摘要匹配已批准签名产物
- 构建来源和签发者已验证
- 要求时运行时/硬件证明新鲜且有效
- 网络和工具策略匹配批准配置
- 撤销和审计控制可运行

证据须分类为密码学验证、提供商观察、操作者证明、推断或未知。不得悄悄把未知态势提升为可信。

<a id="network-controls"></a>
## 网络控制

V1 默认离线模式或 LocalStack 风格本地端点，真实云执行默认不在范围内。

攻击探测默认仅针对 `offline://...`、`local://...`、`127.0.0.1`、`localhost`、`localhost.localstack.cloud` 等本地沙箱 URL。非本地 HTTP(S) 需明确 `--allow-live-cloud` 并记录批准。使用 `run --policy-file` 时，`allowed_target_hosts` 可进一步要求精确主机名或 `*.domain` 通配后缀。添加真实云适配器前内置场景仍为本地/离线；除非目标和事件证明对应模式，报告不得称其为真实云验证。

<a id="secret-handling"></a>
## 秘密处理

- 从环境变量读取秘密。
- 忽略 `.env` 和 Terraform state。
- `.env.example` 仅记录必要名称，不含值。
- 发布案例、支持包、截图或演示归档前必须审查产物。
- 上传、支持分享、公开案例前由 `nullstate scrub` 创建脱敏副本。

<a id="container-security"></a>
## 容器安全

LocalStack 等是运行时依赖，不是 vendored 二进制。操作者应拉取可信镜像，不在生成工作区外运行任意红队代码。

<a id="red-team-command-execution"></a>
## 红队命令执行

V1 红队执行器按设计受限：

- 只执行生成的 `attack.py`。
- `attack.py` 必须直接位于运行目录。
- 若使用清单，`attack-manifest.json` 也须直接位于运行目录。
- 用当前 Python 解释器启动，不用任意 shell。
- 动态输入仅 `--target-url`、`--stage` 和生成清单路径。
- 记录命令、stdout、stderr、返回码、URL、阶段、开始/结束时间和时长。
- 场景探测按模板允许，不由模型实时生成。
- 探测超时应短；企业上传或长期保存前限制 stdout/stderr 捕获。

这样可展示本地沙箱真实命令执行，而不授予模型无限工具访问。

企业加固应添加：

- 每个场景/后端组合的明确允许策略
- 实际云 HTTP(S) 适配器的主机允许清单
- 发布时采用组织特定规则的产物脱敏器
- 默认关闭的 `--allow-live-cloud` 门禁

<a id="cicd-security"></a>
## CI/CD 安全

- PR 检查测试、lint、类型和依赖审计。
- CodeQL 在 PR、推送及每周运行。
- PR 执行依赖审查。
- 发布 workflow 仅由 semver 标签触发，为构建发行包和 `sbom.spdx.json` 创建 GitHub 证明。
- workflow 使用最小权限。

<a id="data-protection"></a>
## 数据保护

发布前审查产物。不得发布 token、真实租户/订阅 ID、私有 IP 映射或云 state。

<a id="known-risks"></a>
## 已知风险

- 一些适配器仅为脚手架，非完整执行后端。
- LocalStack Azure 需要外部设置和认证 token。
- 离线指标报告零 token，因为未调用模型。
- 生成脚本刻意是窄探测；更丰富利用脚本仍应明确允许且限沙箱。

<a id="future-improvements"></a>
## 未来改进

- 从 lockfile 生成更完整的已解析依赖 SBOM。
- 更广的组织特定脱敏规则。
- 代理工具的 policy-as-code 护栏。
- 带可审计操作者意图的实际云批准门禁。
- 为 AI 代理身份、委托上下文、工具身份、代理间信任提供提供商特定清单和路径控制。
