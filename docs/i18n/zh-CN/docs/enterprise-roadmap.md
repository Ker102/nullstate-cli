<a id="enterprise-and-monetization-roadmap"></a>
# 企业与变现路线图

将 `nullstate` 定位为未来企业 DevSecOps，而不仅黑客松 CLI。

<a id="product-positioning"></a>
## 产品定位

`nullstate` 是证据支持云路径验证平台。关联 IaC 与 AWS/Azure 状态，帮助云/平台/安全判断身份可达数据与能力，受控证明、确定性修复、保留证据。

核心信息：

> 静态扫描指出可能问题。Nullstate 证明路径、修复、验证阻断。

无需完整账户 IaC。IaC 提供意图，只读发现提供部署、身份、网络、日志、漂移。规范图只重建利用验证所需最小路径。

AI 代理应为一等主体：专用身份、IAM、服务主体、托管/工作负载、工具网关、委托。计算代理、提示、记忆、连接器、MCP、插件或下游凭据入侵的影响范围。

外部态势是独立付费机会：持续收集验证绑定、来源、摘要、证明、漏洞补丁、网络、工具、新鲜度、日志、撤销。结合可达数据/权限，不藏在黑箱分数。

<a id="target-customers"></a>
## 客户

<a id="primary"></a>
### 主要

- Terraform 密集 DevSecOps
- 安全默认 IaC 平台团队
- 验证修复 SLA 的云安全
- 证据报告咨询

<a id="secondary"></a>
### 次要

- 需审计但不能送基础设施到 SaaS 的受监管创业公司
- 私有 AI 安全企业
- MSP/迁移伙伴

<a id="core-value-propositions"></a>
## 价值

<a id="1-evidence-over-alerts"></a>
### 1. 证据优于警报

多数停在发现；`nullstate` 提供时间线：

1. 发现
2. 红队推理
3. 沙箱命令证据
4. 补丁
5. 修复后验证
6. 报告

<a id="2-local-first-and-private"></a>
### 2. 本地优先/私有

敏感 IaC、计划、日志可留客户环境，模型用私有兼容端点。

<a id="3-deterministic-security-core"></a>
### 3. 确定性核心

模型不判通过/失败，确定性检测/修复/验证可靠。

<a id="4-devsecops-native-cli"></a>
### 4. DevSecOps CLI

首先 CLI，可本地、CI、临时验证。

<a id="enterprise-product-tiers"></a>
## 产品层级

<a id="open-source-cli"></a>
### 开源 CLI

用途：开发者采用/信任。

功能：

- 本地/离线
- 有限场景库
- 报告
- 受限红队
- 基本 LocalStack
- 社区文档

<a id="team-edition"></a>
### Team

用途：小团队/咨询。

功能：

- 更多场景
- HTML/PDF
- 脱敏
- 基线比较
- GitHub Actions/GitLab CI
- 历史导出
- 私有模型预设

可能价格：

- 每席 19-49 EUR/月
- 或每库 49-199 EUR/月

<a id="enterprise-edition"></a>
### Enterprise

用途：合规和私有设施的大公司。

功能：

- 工具 policy-as-code
- SSO/SAML/OIDC
- 审计
- 集中证据
- 团队/角色
- 私有部署支持
- 定制场景
- 企业 SLA
- Jira、ServiceNow、Slack、SIEM、GRC

可能价格：

- 年约约 15k-50k EUR/年起
- 定制场景/支持额外付费

<a id="monetization-paths"></a>
## 变现路径

<a id="path-a-open-core-devsecops-cli"></a>
### A：Open-core CLI

核心开源，收费：

- 企业场景
- 云仪表板
- 托管证据
- 私有部署
- 合规导出

优点：

- 开发者采用
- GitHub 信誉
- 社区信任

缺点：

- 免费/付费边界
- 支持负担

<a id="path-b-security-consultancy-tooling"></a>
### B：安全咨询工具

`nullstate` 用于付费评估差异化。

提供：

- IaC 紫队评估
- Terraform 加固
- 修复 PR
- 审计证据

优点：

- 首收入容易
- 无需完整 SaaS
- 客户案例证明

缺点：

- 服务收入难扩展

<a id="path-c-enterprise-private-ai-security-platform"></a>
### C：企业私有 AI 安全

私有 AI IaC/云控制验证层。

优点：

- MI300X/私有叙述
- 企业预算

缺点：

- 销售周期
- 更多加固/集成

<a id="recommended-near-term-strategy"></a>
## 近期策略

A+B 混合：

1. CLI 开源。
2. 强证据 IaC 技术品牌。
3. 作品/案例吸引关注。
4. 先付费评估/实施。
5. 重复需求转为 Team/Enterprise。

<a id="product-architecture-cli-local-gui-and-paid-platform"></a>
## 架构：CLI、本地 GUI、付费

CLI 保持开源引擎，本地/CI、产物、可移植包。

免费 GUI 单用户，读 `runs/`、生成仪表板、触发 run/report/bundle/sandbox；不需云登录，无团队/合规/警报/托管模型。

付费云/自托管摄取包，提供团队、模型、历史、支持、定期、警报、集成、RBAC、审计、合规。

`run-bundle.json` 是 CLI、免费画面、CI、支持、未来平台契约。`docs/schemas/run-bundle.schema.json` 定义 v1，写前验证。

`nullstate upload --dry-run` 无网计划记录端点、校验、产物数、token 有无、脱敏状态，不送数据不存值。`docs/schemas/upload-plan.schema.json` 定义 v1，写前验证。

<a id="ci-and-managed-model-inference"></a>
## CI/托管推理

两模式：

- 客户提供：CI secrets `NULLSTATE_LLM_BASE_URL`、`NULLSTATE_LLM_API_KEY`。
- Nullstate 提供：`NULLSTATE_CLOUD_TOKEN`，Cloud 红/蓝推理。

托管是付费，按组织、项目、运行、模型、token、延迟、估计成本计量。

三触发：

1. IaC/策略/清单 PR：提议、基线、可选高风险一次性验证，按策略阻合并。
2. Terraform、CloudFormation、Bicep 等部署后：刷新清单、漂移、路径。
3. 定期：控制台、未管理、权限、新端点、旧风险、Git 外变化。

生产发现只读。非破坏检查需策略明确批准。利用按保真度路由模拟器、孪生、一次集群、专用 AWS/Azure。

<a id="support-automation-and-alerts"></a>
## 支持/自动化/警报

付费应用支持反馈，工单含脱敏包、版本、ID、场景、仪表板。

定期扫连接库/上传 IaC；警报覆盖新严重、观察利用、修复/CI 失败、旧风险、模型失败。先邮件/webhook，后 Slack、Teams、Jira、GitHub Issues、SIEM。

<a id="brand-direction"></a>
## 品牌

<a id="name"></a>
### 名称

`nullstate` 暗示将基础设施风险恢复安全基线。

<a id="tagline-options"></a>
### 标语

- 证明、修补、验证 IaC 风险。
- Terraform 紫队验证。
- 从发现到阻断。
- 云证据 DevSecOps。
- IaC 本地优先攻击验证。

推荐：

> 证明、修补、验证云攻击路径。

<a id="brand-personality"></a>
### 个性

- 精确
- 技术
- 可信
- 安全优先
- 企业意识
- 不炒作

红队更成熟前别称自主黑客。优先：

- 受限红队
- 证据验证
- 本地紫队

<a id="enterprise-reliability-requirements"></a>
## 企业可靠性

业务依赖前：

1. 核心真实利用。
2. 模拟/推断/观察区分。
3. 策略允许命令；当前已有场景、后端、阶段、参数、分类、host、命令、超时、输出验证。
4. 脱敏。
5. 稳定模式：生成清单已写前验。
6. CI 机器退出：`nullstate run --ci` 与 `ci-summary.json` 已可用验证。
7. SARIF/JSON 与 policy-result 已有。
8. 可重现清单：`nullstate evidence-manifest` SHA-256/HMAC、v1 校验，`nullstate evidence-verify`。
9. 发布来源：checksum、干净 SBOM wheel、`sbom.spdx.json`、GitHub 包/SBOM、Sigstore、标签前演练。
10. `remediation.json` 规则版本、文件、ID、`$schema` 和 v1 校验。
11. 无明确开启不碰真实云。

<a id="next-feature-priorities"></a>
## 优先级

<a id="p0-trust-and-correctness"></a>
### P0：可信/正确

- 实 S3 读
- 报告运行证据
- 脱敏
- `ci-summary.json` 判定/退出

<a id="p1-cicd-adoption"></a>
### P1：CI/CD

- `nullstate run --ci`
- `nullstate sarif`
- Actions 模板
- `nullstate baseline`、`--baseline-file`
- `nullstate upload --dry-run`
- `docs/schemas/upload-plan.schema.json`
- `docs/schemas/attack-manifest.schema.json`

<a id="p2-enterprise-controls"></a>
### P2：企业

- 场景/后端/阶段/分类/host/命令/超时/输出策略
- `nullstate policy init` 基本/场景预设
- `docs/schemas/nullstate-policy.schema.json`
- 组织配置
- `nullstate evidence-manifest`
- `docs/schemas/evidence-manifest.schema.json`
- `nullstate evidence-verify`
- 可选 HMAC
- GitHub 来源
- GitHub SBOM
- Sigstore
- 首标签手册检查
- 已验 `remediation.json`
- AWS/Azure 代理身份
- 原生、委托、运行、工具、下游分开
- 合成/受控提示注入与过度代理能力
- 代理间信任/共享身份
- 外部态势/新鲜度
- 签名、digest、SLSA、SPIFFE/SPIRE、硬件
- 缺失/旧证据时降权网关

<a id="p3-growth-and-brand"></a>
### P3：增长

- 作品案例
- 视频
- 技术博客
- 扫描器比较
- CLI GIF 页面

<a id="case-study-angle"></a>
## 案例角度

不是建扫描器，而是：

> 本地 DevSecOps 将 Terraform 发现变为可复现紫队：检测、推理、受限命令、确定修复、阻断验证、保存证据。

诚实限制：

> 黑客松有安全执行边界。下次企业迭代将健康探测扩为沙箱真实利用。

诚实提升审查信誉。

<a id="success-metrics"></a>
## 指标

技术：

- 实利用场景数
- fixture 误报率
- 修复成功率
- 可重复性
- 命令证据完整

业务：

- 星/fork
- 视频完播
- 安全/平台交流
- 试点
- 付费线索
- CI 常用

<a id="90-day-roadmap"></a>
## 90 天

<a id="days-1-14"></a>
### 1-14 天

- 实 S3
- runtime 报告
- 脱敏
- 技术详解打磨
- 发布案例

<a id="days-15-30"></a>
### 15-30 天

- Azure 真探测或明确限制
- 超基线/严重度的 CI
- SARIF/JSON
- Actions 例

<a id="days-31-60"></a>
### 31-60 天

- AWS/Azure 场景包
- 命令/分类/host 策略
- 完整性清单
- 签名验证
- 案例页面

<a id="days-61-90"></a>
### 61-90 天

- 首设计伙伴联络
- 付费评估
- 团队/证据原型
- 企业部署架构
