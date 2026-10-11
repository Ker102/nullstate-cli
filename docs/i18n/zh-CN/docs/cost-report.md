<a id="cost-report"></a>
# 成本报告

<a id="summary"></a>
## 摘要

V1 默认接近零云开支。离线本地运行；LocalStack 在操作者 Docker；AMD 仅用于黑客松模型证据。

<a id="cost-items"></a>
## 项目

| 项目 | 预计成本 | 说明 |
|---|---:|---|
| nullstate CLI | 0 | 本地 Python |
| 离线演示 | 0 | 无云/模型端点 |
| LocalStack Azure | 取决于访问 | 需 token |
| AMD Developer Cloud | 黑客松额度 | MI300X 模型 |
| Fireworks | 取决于提供商 | GPU 延迟备用 |
| GitHub Actions | 取决于低价/免费档 | 轻测试 |

<a id="controls"></a>
## 控制

- 默认无真实 Azure。
- CLI 不创建长期云资源。
- `nullstate sandbox down` 停本地。

<a id="future-tracking"></a>
## 未来记录

公开案例前记录实际模型服务时长、GPU 小时、LocalStack/云成本。

记录各次离线、托管或 AMD GPU 推理，避免在等待访问时使用备用而误述。
