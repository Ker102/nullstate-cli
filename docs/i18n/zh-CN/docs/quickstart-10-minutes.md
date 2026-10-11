<a id="first-10-minutes"></a>
# 最初 10 分钟

这是新开源用户最安全的入门路径，使用离线 AWS S3 场景、模拟代理和本地产物生成。

无需 Docker、LocalStack、模型端点或真实云凭据。

<a id="1-install-from-a-checkout"></a>
## 1. 从检出源码安装

```powershell
git clone https://github.com/Ker102/nullstate-cli.git
cd nullstate-cli
python -m pip install -e .
```

若 `nullstate` 不在 `PATH` 中，用 `python -m nullstate` 运行同样命令。

<a id="2-check-the-local-environment"></a>
## 2. 检查本地环境

```powershell
nullstate doctor --offline
nullstate status
```

预期结果：

- CLI 输出 Nullstate 启动/状态信息
- 这条离线路径允许缺少 Docker、Terraform、LocalStack 或模型端点

<a id="3-run-a-deterministic-offline-scan"></a>
## 3. 运行确定性离线扫描

生成自己的运行前，可先查看已脱敏示例：

```powershell
nullstate report --runs-dir examples/sample-runs
nullstate summary --runs-dir examples/sample-runs --json
```

示例含 `report.md`、`run-bundle.json` 和 `dashboard.html`，便于扫描前查看核心产物。

```powershell
nullstate run examples/aws-public-s3 --offline --mock-agents
```

预期结果：

- 一个高严重度 S3 公共访问发现
- 红队修复前：成功
- 红队修复后：阻断
- 产物写入 `runs/<run-id>/`

<a id="4-open-the-report"></a>
## 4. 打开报告

```powershell
nullstate report
```

检查：

- 发现摘要
- 攻击推理
- 修复补丁
- 验证结果
- 运行时证据分类

<a id="5-build-shareable-local-artifacts"></a>
## 5. 构建可分享本地产物

```powershell
nullstate bundle
nullstate dashboard --open
nullstate sarif
nullstate evidence-manifest
nullstate evidence-verify
```

生成产物包括：

- `run-bundle.json`
- `dashboard.html`
- `nullstate.sarif`
- `evidence-manifest.json`
- `evidence-verification.json`

<a id="6-scrub-before-sharing"></a>
## 6. 分享前脱敏

```powershell
nullstate scrub
```

分享 `scrubbed-runs/` 中的副本，而非原始 `runs/` 目录。

<a id="7-optional-github-actions-gate"></a>
## 7. 可选 GitHub Actions 门禁

```powershell
nullstate init-ci github --scenario aws-public-s3 --iac-path examples/aws-public-s3
```

生成文件：

- `.github/workflows/nullstate.yml`
- `nullstate-policy.json`

提交两份文件，让 pull request 运行离线 Nullstate 门禁。用于真实仓库前，将 `--iac-path` 调整为 Terraform 目录。

<a id="8-optional-live-aws-localstack-path"></a>
## 8. 可选实际 AWS LocalStack 路径

仅在配置好 Docker 和 LocalStack 后使用：

```powershell
nullstate sandbox up localstack-aws
nullstate sandbox status localstack-aws
nullstate run examples/aws-public-s3 --target localstack-aws --mock-agents
nullstate report
nullstate sandbox down localstack-aws
```

实际 AWS 路径是目前已证明的本地运行时场景。它在 LocalStack AWS 部署漏洞 fixture，运行受限匿名对象读取探测，应用确定性修复，再次运行探测。

<a id="current-azure-note"></a>
## 当前 Azure 说明

Azure Blob 支持离线确定性验证，但实际 LocalStack Azure 验证需要 workspace/用户拥有 Azure Emulator 授权。若 `localstack/localstack-azure-alpha` 以代码 `55` 退出，查看 `docker logs localstack-azure`；可能是账户未启用 Azure Emulator。
