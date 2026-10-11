<a id="product-and-validation-model"></a>
# 产品与验证模型

<a id="product-purpose"></a>
## 产品目的

Nullstate 是一个以证据为支撑的云攻击路径验证平台。它将基础设施即代码与观察到的 AWS 和 Azure 状态关联起来，跨网络、身份、服务和数据关系进行推理，在受控环境内验证选定的攻击路径，应用修复措施，并重放攻击。

产品并不打算要求用 Terraform 完美表示整个云账户。IaC 描述预期和受管理的配置，而只读发现描述已部署的实际情况。Nullstate 应将两者合并为规范化的环境图，并保留每条关系的来源和置信度。

开源产品应首先作为面向人类、CI 作业和编程代理的本地 DevSecOps 验证框架。`nullstate summary --json` 为代理提供紧凑的运行结果，而不是迫使它们解析 Markdown 报告；`nullstate context validate` 和 `nullstate context summary --json` 则在加入实时采集器之前，定义安全的只读云上下文契约。

<a id="environment-graph"></a>
## 环境图

环境图应接受：

- Terraform、CloudFormation、CDK 导出、Bicep、ARM 以及提供商的计划/状态数据。
- AWS 和 Azure 的只读资源清单。
- IAM 角色、Azure RBAC 分配、托管身份、信任关系和工作负载身份。
- AI 代理身份、代理身份蓝图、代理工作负载身份、委托用户上下文、工具身份以及下游凭据关系。
- 公共端点、虚拟网络、安全组、NSG、路由、网关、私有端点和对等互连。
- 存储、数据库、秘密管理、计算、无服务器、容器和 Kubernetes 配置。
- 原生安全发现、活动日志、流日志、审计日志以及选定的运行时元数据。
- 用户提供的可选数据分类，或从安全元数据和合成测试数据推断的数据分类。

图不需要克隆每个资源。它必须识别与安全相关的路径，并创建最小攻击路径孪生体，仅包含测试假设所需的关系。

当前上下文清单预览有意仅在本地运行：

```bash
nullstate context validate examples/cloud-context/aws-readonly-context.json
nullstate context summary examples/cloud-context/aws-readonly-context.json --json
```

它验证提供商、账户、身份、资源、公共暴露和数据分类元数据的结构，不请求云凭据。未来的采集器应使用短期只读云身份输出符合此契约的数据。

<a id="evaluation-and-product-metrics"></a>
## 评估与产品指标

Nullstate 的案例研究价值应通过测量确定，而不只是描述。当前评估框架从可重复的内部基准测试开始：

```bash
nullstate eval run examples/eval/iac-security-regression.json --output-dir eval-runs/iac-security-regression
```

该框架记录持续时间、发现数量、最高严重程度、攻击前/后状态、token 总量、产物数量以及预期通过/失败状态。这是将 Nullstate 与仅使用扫描器的审查、人工审查和通用编程代理审查进行比较的第一步。在这些基线建立之前，声明应限于已测量的 Nullstate 行为，而不是泛泛宣称准确率或节省时间。

<a id="identity-aware-attack-analysis"></a>
## 身份感知攻击分析

开放端口或公共容器并不是发现的全部。Nullstate 应评估每个经授权的攻击者视角能访问什么：

| 视角 | 示例 |
|---|---|
| 外部 | 匿名互联网客户端 |
| 租户用户 | 已认证但低权限的云用户 |
| 开发者 | 具有部署或读取权限的人类身份 |
| CI 工作负载 | GitHub Actions、GitLab 或构建系统身份 |
| 已失陷工作负载 | VM、容器、函数或应用身份 |
| 云角色 | AWS IAM 角色、Azure 服务主体或托管身份 |
| AI 代理 | 专用代理身份、代理工作负载身份或代理运行时角色 |
| 委托代理 | 使用从人类用户传递而来的权限执行操作的代理 |
| 横向攻击者 | 通过攻击路径的较早步骤获得的主体 |

每个观察结果应记录主体、假定权限、认证方式、目标、触达的数据或能力、命令证据和置信度。

<a id="ai-agents-as-cloud-principals"></a>
## AI 代理作为云主体

AI 代理越来越多地与基础设施、云 API、内部服务、数据存储、工单系统、源代码仓库和部署工具交互。它们可能通过以下方式运行：

- 专门为该代理创建的专用身份
- 常规服务主体、托管身份、IAM 角色或工作负载身份
- 多个代理共享的运行时或工具身份
- 从人类用户传递而来的委托权限
- 为下游工具或第三方服务获取的凭据

不得将这些模式合并为一个通用服务账户。Nullstate 应将代理、运行时、工具、委托用户、凭据和目标服务表示为独立的图节点。这保留了谁发起操作、由谁的权限授权，以及哪个组件可能遭到入侵的信息。

代理特有的攻击路径包括：

- 提示注入导致代理滥用合法云权限
- 已失陷的工具、插件、MCP 服务器、记忆或检索内容影响操作
- 过度自主性允许执行超出预定任务的破坏性操作或权限变更
- 混淆代理路径，即不可信用户诱使高权限代理代其执行操作
- 委托用户权限触达代理自身身份无法访问的资源
- 共享运行时身份导致归因和最小权限失效
- 代理间信任使横向移动成为可能
- 长期或范围过宽的下游凭据扩大影响范围

Nullstate 应至少评估三个独立的权限视图：

1. **代理原生权限：**使用代理自身身份可访问的资源。
2. **委托权限：**代表特定用户或用户类别执行操作时可访问的资源。
3. **工具链权限：**通过运行时身份、插件、网关、连接器和下游凭据可访问的资源。

报告应解释实际生效的权限链，并识别当代理、其指令、记忆或某个工具遭到入侵时暴露的数据和操作。安全验证应使用合成提示、合成数据、受控工具和一次性环境，而不是尝试针对生产代理进行不受控的提示注入。

对于外部托管代理，仅进行身份分析并不足够。Nullstate 还应评估运行时态势：工作负载与身份的绑定、产物来源、部署摘要、主机和运行时完整性、网络暴露、工具控制、日志记录、撤销，以及支持证据的新鲜度和强度。详细设计见[外部代理信任与运行时态势](plans/2026-06-22-external-agent-trust-design.md)。

当前 CLI 包含此模型的初步确定性预览：

```bash
nullstate agent posture verify examples/agent-trust/external-agent-manifest.json
nullstate agent blast-radius examples/agent-trust/external-agent-manifest.json
```

这些命令操作本地清单，而不是实时提供商采集器。它们旨在先强化数据契约：缺失、过期或未知的态势证据必须保持可见，委托用户权限必须与代理自身身份分开。

<a id="exposed-data-and-impact"></a>
## 暴露的数据与影响

云管理员可能因为认为某个可访问服务不包含关键内容，而有意接受它。Nullstate 仍应识别该路径是否暴露：

- 对象名称、目录列表、账户 ID、租户 ID、主机名或内部拓扑
- 应用日志、备份、诊断信息、构建产物、源映射或部署包
- 凭据、token、连接字符串、配置或秘密引用
- 个人、财务、受监管、客户或专有数据
- 写入、删除、身份冒充、执行或策略变更能力
- 可用于凭据攻击、横向移动、权限提升或定向社会工程的信息

报告必须区分：

- 配置表明可能存在暴露
- 已观察到安全元数据
- 已获取合成证据数据
- 已证明某项高权限能力
- 有意未访问生产敏感内容

<a id="why-not-attack-production-directly"></a>
## 为什么不直接攻击生产环境？

只读发现和获得严格限定批准的非破坏性验证可以针对生产环境运行。自主漏洞利用应默认在受控环境中进行，因为：

1. 漏洞利用可能修改、删除、损坏或暴露真实数据。
2. 探测可能导致限流、中断、账户锁定、隔离或激活事件响应。
3. IAM 测试可能创建持久凭据、信任关系或权限变更。
4. 数据外传测试可能违反隐私、合同、监管和数据驻留要求。
5. 生产依赖可能影响批准范围之外的客户和第三方。
6. 清理无法保证精确恢复之前的状态。
7. 重复的 CI 验证必须具有确定性，并且足够安全，无需渗透测试人员监督每次执行。

安全运行模型为：

1. 通过只读提供商 API 发现生产环境。
2. 构建攻击假设并确定优先级。
3. 仅在策略允许时，针对生产环境执行允许列表中的非破坏性检查。
4. 在一次性环境中使用合成数据重建最小相关路径。
5. 针对该环境执行受约束的攻击。
6. 应用修复措施并重放同一攻击。
7. 保留证据，并将已证明的路径转化为回归测试。

<a id="aws-and-azure-first"></a>
## 优先支持 AWS 和 Azure

AWS 和 Azure 应作为首批云提供商，因为它们覆盖了企业基础设施的很大一部分，并且都有成熟的 IaC 生态系统。Terraform 仍是一等输入，而不是竞争目标：面向 AWS 的 Terraform 和面向 Azure 的 Terraform 提供预期拓扑和配置，而提供商发现提供实时状态和非受管理的漂移。

提供商适配器还应清点新兴的代理身份系统。Microsoft Entra Agent ID 提供专门的代理身份和身份蓝图，而 Amazon Bedrock AgentCore Identity 通过代理/工作负载身份机制表示代理。Nullstate 应将这些关系与常规服务主体、托管身份和 IAM 角色一同摄取，而不假设所有组织都使用提供商原生的代理平台。

对提供商行为的准确性应分级并明确说明：

| 级别 | 证据来源 | 目的 |
|---|---|---|
| 静态 | IaC、计划、策略和导出的配置 | 快速部署前分析 |
| 观察 | 只读提供商清单和日志 | 理解实际部署状态 |
| 模拟 | LocalStack、服务模拟器、容器或数字孪生 | 在已知保真度限制下进行安全、可重复的验证 |
| 真实沙箱 | 一次性 AWS 账户或 Azure 订阅 | 最高保真度的漏洞利用验证 |

每份报告应标明所使用的级别。模拟器证据绝不能被当作提供商行为完全相同的证明。

<a id="ci-cloud-event-and-scheduled-execution"></a>
## CI、云事件与定时执行

Nullstate 应支持三种互补的触发方式。

<a id="pull-request-and-iac-ci"></a>
### 拉取请求与 IaC CI

当 Terraform、CloudFormation、Bicep、Helm、策略或相关基础设施文件发生变化时触发。

流水线：

1. 在部署前分析拟议配置。
2. 将发现与已批准的基线比较。
3. 可选择为高风险变更创建一次性验证环境。
4. 运行选定的攻击路径回归测试。
5. 导出 SARIF、机器可读的策略结果和证据产物。
6. 当策略阈值检查失败时阻止合并。

这是最快的反馈循环，可以防止易受攻击的配置进入云环境。

<a id="post-deployment-validation"></a>
### 部署后验证

在部署工作流成功完成或发生提供商事件后触发。

示例包括 Terraform apply 作业、CloudFormation 部署、Azure 部署，或表明与安全相关的资源或策略发生变化的云事件。Nullstate 刷新观察到的环境图，检查漂移，并仅运行受影响的安全验证。可能具有破坏性的验证会被转至一次性沙箱，而不是已更新的生产环境。

<a id="scheduled-assurance"></a>
### 定时保障

每小时、每天或每周运行，以检测手动控制台更改、非受管理资源、权限漂移、新增公共端点、已过时的风险接受，以及由 Git 之外的更改产生的攻击路径。

这些模式解决不同的问题：

- PR CI 在部署前验证预期更改。
- 部署后验证确认观察到的状态符合预期。
- 定时保障捕获漂移和带外更改。

成熟的付费平台可以协调这三种模式，保留历史记录，通知团队，并提供托管模型推理。开源 CLI 仍可使用客户提供的凭据和模型端点进行本地和 CI 执行。

<a id="provider-references"></a>
## 提供商参考资料

- [Microsoft Entra Agent ID](https://learn.microsoft.com/en-us/entra/agent-id/)
- [Microsoft Foundry 中的代理身份概念](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-identity)
- [Amazon Bedrock AgentCore Identity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity-overview.html)
- [AWS 代理身份与权限管理指南](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentsec03.html)
