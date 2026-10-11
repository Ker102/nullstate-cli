<a id="open-source-readiness-milestones"></a>
# 开源就绪里程碑

记录将 `nullstate` 从 alpha 提升为稳定开源 CLI 前的实践里程碑。

GitHub 跟踪：

- 里程碑 1：<https://github.com/Ker102/nullstate-cli/milestone/1>
- 里程碑 2：<https://github.com/Ker102/nullstate-cli/milestone/3>
- 里程碑 3：<https://github.com/Ker102/nullstate-cli/milestone/2>

<a id="current-status"></a>
## 当前状态

`nullstate` 面向理解实验后端的 alpha 用户。AWS 已有实际验证与受限命令证据；Azure Blob 有确定性检测、修复、清单探测、离线覆盖，但实际执行需 workspace/用户 Azure Emulator 授权。

<a id="milestone-1-alpha-publication-readiness"></a>
## 里程碑 1：Alpha 发布就绪

目标：早期评估者能理解并使用仓库。

状态：基本完成。

接受标准：

- [x] README 清晰源码/预发布安装。
- [x] `nullstate` 入口和 `python -m nullstate` 备用。
- [x] 许可、贡献、行为、安全策略。
- [x] issue 模板收安全上下文，不要求秘密。
- [x] 离线入门无需 LocalStack、Terraform 云凭据或模型设施。
- [x] 如实说明红队执行边界。
- [x] 报告区分观察、确定性模拟、不确定探测。
- [x] 提供脱敏示例无需 Docker。issue #29。

<a id="milestone-2-stable-local-sandbox-validation"></a>
## 里程碑 2：稳定本地验证

目标：可靠本地证明路径。

状态：AWS 就绪；Azure 外部授权阻碍。

接受标准：

- [x] LocalStack AWS 部署漏洞 S3。
- [x] 生成 AWS `attack.py` 修复前后匿名读取。
- [x] 实命令证明前可利用、后阻断。
- [x] 容器启动后退出时 `sandbox up` 拒绝虚假成功。
- [x] Azure 授权失败有清晰提示。
- [ ] 解决授权或换支持存储模拟器。
- [ ] 实际 Azure Blob 验证前匿名读、后阻断。
- [ ] Azure 不可用则为纯存储 `azure-public-blob` 加 Azurite。issue #30。

<a id="milestone-3-open-source-stable-cli"></a>
## 里程碑 3：稳定开源 CLI

目标：外部能安装、运行、信任文档范围。

状态：未完成。

接受标准：

- [ ] 无需克隆的发布产物。
- [ ] 页面含 wheel、sdist、SBOM、清单、证明、签名验证。
- [x] 干净检出的最初 10 分钟指南。
- [x] 脱敏 demo 包/仪表板。
- [x] 非实际场景明确标离线/脚手架。
- [x] 依赖审计/接受风险文档。
- [ ] 标签前确认 Actions dry-run。
- [ ] 最新标签 `pip install` 在 Windows/Linux 提供 `nullstate`。

说明：

- Windows 本地已在 2026-07-03 通过 `python scripts/release/install_smoke.py --tag v0.1.0-alpha.2`。
- Linux 仍须 runner 或 dry-run 确认才能完成接受项。

<a id="azure-emulator-decision"></a>
## Azure Emulator 决策

当前 token 能激活缓存/试用许可，但 workspace/用户无 Azure Emulator 镜像授权。不是 Azure 云权限，是 LocalStack 产品许可。

选项：

1. 请求支持为 `LOCALSTACK_AUTH_TOKEN` 所属用户/workspace 开通。
2. V1 Blob 用 Azurite，只覆盖公开读取，不含广泛 ARM 控制平面。
3. 内部小模拟器仅 demo：依赖风险最低、维护最高，须标场景模拟非 Azure。
4. Azure 保持离线，优先 AWS 实验证。

推荐：

可快速授权就用 Azure LocalStack，否则纯 Blob 用 Azurite，ARM 模拟留未来。
