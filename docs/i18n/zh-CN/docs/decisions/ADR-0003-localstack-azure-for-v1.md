<a id="adr-0003-localstack-azure-for-v1"></a>
# ADR-0003：V1 使用 LocalStack Azure

<a id="status"></a>
## 状态

已接受。

<a id="context"></a>
## 背景

首演目标 Terraform Azure。真实 Azure 增加凭据、成本、清理、安全风险。

<a id="decision"></a>
## 决策

首执行后端用 LocalStack Azure，仅计划备用。

<a id="consequences"></a>
## 后果

- 演示无需真实 Azure 资源。
- 实际 LocalStack Azure 仍需 Docker 和 `LOCALSTACK_AUTH_TOKEN`。
- 仓库须区分 LocalStack 集成与 vendoring。
