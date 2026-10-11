<a id="adr-0002-pluggable-sandbox-backends"></a>
# ADR-0002：可插拔沙箱后端

<a id="status"></a>
## 状态

已接受。

<a id="context"></a>
## 背景

未来需支持云 IaC、Kubernetes 清单、Compose 栈、本地部署配置。

<a id="decision"></a>
## 决策

适配器注册表提供三模式：

- 可执行沙箱
- 数字孪生沙箱
- 仅计划分析

<a id="consequences"></a>
## 后果

- V1 先提供强执行目标并展示未来后端。
- 建模本地部署，不假装所有提供商都有完美模拟器。
- 部分后端起步为文档脚手架，不是完整利用。
