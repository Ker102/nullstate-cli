<a id="amd-compute-strategy"></a>
# AMD 计算策略

<a id="decision"></a>
## 决策

案例主路径用更复杂的 AMD Developer Cloud / DigitalOcean；GPU 延迟时 Fireworks AI 备用。

<a id="why-primary-path-is-digitaloceanamd-developer-cloud"></a>
## 为何主路径是 DigitalOcean/AMD

- 黑客松证据更强：模型服务、ROCm、vLLM/SGLang、GPU 可观测性、运维。
- 实际 DevOps、云访问、安全边界、推理运维带来更好个人学习。
- 支持敏感 IaC/证据的私有或自控推理理念。
- 比单调用托管 API 更有案例素材。

<a id="why-fireworks-stays-as-fallback"></a>
## Fireworks 为何备用

- AMD 延迟可解锁演示。
- 兼容端点保持红/蓝循环。
- 仍与 AMD 生态有关，但须称托管推理，不称私有自有服务。

<a id="execution-plan"></a>
## 执行计划

<a id="track-a---digitalocean-baseline-without-gpu"></a>
### 路径 A - 无 GPU DigitalOcean 基线

先准备非 GPU：

- 项目/仓库 secrets
- 加固控制 droplet/容器宿主
- Docker/Compose 基线
- Azure LocalStack 沙箱
- nullstate 安装
- GitHub Actions 环境
- 产物存储布局
- 基础监控日志

GPU 前也有价值。

<a id="track-b---amd-gpu-inference"></a>
### 路径 B - AMD GPU 推理

MI300X 可访问时：

- 配置 AMD/DigitalOcean GPU 实例
- ROCm 或提供商镜像
- vLLM/SGLang 兼容 API 服务
- 仅对操作者开放必需 API
- 记录模型、上下文、ROCm、GPU、内存、吞吐、延迟
- 保存 vLLM `/metrics` 和 `amd-smi` 或 `rocm-smi` 证据

<a id="track-c---fireworks-contingency"></a>
### 路径 C - Fireworks 应急

GPU 阻碍提交时：

- `NULLSTATE_LLM_BASE_URL` 配 Fireworks
- 同一 nullstate 演示
- 记录托管备用
- 保留 AMD/DigitalOcean 为下一里程碑，不隐瞒阻碍

<a id="demo-positioning"></a>
## 演示定位

首选叙述：

```text
nullstate runs local IaC security validation and can use a private AMD MI300X-hosted model endpoint for red/blue reasoning over security evidence.
```

备用叙述：

```text
nullstate is model-provider portable through OpenAI-compatible endpoints. The same CLI can run against managed inference while the private AMD GPU endpoint is being provisioned.
```

<a id="evidence-checklist"></a>
## 证据清单

- `runs/<id>/report.md`
- `runs/<id>/metrics.json`
- vLLM `/metrics` 前后
- `amd-smi` 或 `rocm-smi`
- ROCm 版本
- 启动命令
- 脱敏网络图
- GPU/CLI 截图
- 注明 AMD、模拟或 Fireworks

<a id="risks"></a>
## 风险

| 风险 | 影响 | 缓解 |
|---|---|---|
| AMD 访问延迟 | 高 | DO 基线、Fireworks |
| GPU/ROCm 不匹配 | 中 | 提供商镜像、精确版本 |
| 模型过大/慢 | 中 | 红蓝先共用模型 |
| 端点公开 | 高 | 限入站、token、边界文档 |
| 夸大私有推理 | 高 | 标实际类型 |
