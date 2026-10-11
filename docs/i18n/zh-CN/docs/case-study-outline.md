<a id="case-study-outline"></a>
# 案例研究提纲

<a id="problem"></a>
## 问题

云团队交付 Terraform 的速度超过安全团队持续验证可利用性的速度。静态扫描器指出潜在风险，不能证明攻击者可利用或修复能阻断。

<a id="solution"></a>
## 方案

`nullstate` 在 Terraform IaC 上运行本地紫队循环：

- 分析计划基础设施。
- 尝试红队利用。
- 生成蓝队修复。
- 补丁后重验。
- 输出证据报告。

<a id="demo-scenario"></a>
## 演示场景

实际验证路径用 LocalStack 公共 AWS S3 fixture：`nullstate` 检测暴露、受限匿名读取、修补 Terraform、验证阻断。Azure Blob 有同样确定性检测/修复，但实际 Azure 验证仍等授权或 Azurite 等纯存储备用。

<a id="why-amd-mi300x"></a>
## 为什么 AMD MI300X

架构面向长上下文安全证据，可将计划 JSON、日志、利用输出、修复差异送本地端点，无外部 API 延迟或数据暴露。

<a id="next-steps"></a>
## 后续

- 更多 Azure 规则：共享 key、公共网络、公共 Key Vault。
- 解决 Azure LocalStack 授权或 Blob Azurite 备用。
- 同产物模型下添加实际 Kubernetes、Compose、本地部署适配器。
- 用 vLLM `/metrics` 和 `amd-smi` 或 `rocm-smi` 快照收集 AMD 模型证据。
