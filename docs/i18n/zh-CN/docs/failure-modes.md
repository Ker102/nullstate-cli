<a id="failure-modes"></a>
# 故障模式

<a id="localstack-azure-unavailable"></a>
## LocalStack Azure 不可用

影响：实际沙箱无法运行。

备用：`--offline` 或 `--target plan-only`。

<a id="missing-docker"></a>
## 无 Docker

影响：可执行沙箱无法启动。

备用：仅计划仍解析并报告。

<a id="missing-model-endpoint"></a>
## 无模型端点

影响：无法真实红/蓝调用。

备用：离线模拟代理保持完整演示。

<a id="unknown-model-provider"></a>
## 未知提供商

影响：无法推断兼容 URL。

备用：`NULLSTATE_LLM_PROVIDER` 设 `custom`、`google`、`claude`；自托管还设 `NULLSTATE_LLM_BASE_URL` 或分角色 URL。

<a id="terraform-provider-mismatch"></a>
## Terraform 提供商不匹配

影响：`terraform init` 或 `plan` 失败。

备用：静态解析 fixture。

<a id="model-output-is-wrong"></a>
## 错误模型输出

影响：解释/修复文字误导。

控制：确定性检测与修复为 V1 权威。

<a id="report-includes-sensitive-data"></a>
## 报告敏感数据

影响：公开案例泄密。

控制：先审查；运行 `nullstate scrub`，查看 `scrub-report.json`。
