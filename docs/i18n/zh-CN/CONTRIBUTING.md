<a id="contributing"></a>
# 贡献指南

<a id="workflow"></a>
## 工作流程

使用 GitHub flow：

1. 创建 issue 或关联已有 issue。
2. 创建分支：`feat/<short-name>`、`fix/<short-name>`、`docs/<short-name>` 或 `chore/<short-name>`。
3. 提交结构化 pull request。
4. 等待 CI 与审查。
5. 通过 squash 合并到 `main`。

禁止直接推送到 `main`。

<a id="local-setup"></a>
## 本地设置

```powershell
git clone https://github.com/Ker102/nullstate-cli.git
cd nullstate-cli
python -m pip install -e ".[dev]"
nullstate doctor --offline
```

若 `nullstate` 控制台命令不在 `PATH` 中，使用：

```powershell
python -m nullstate doctor --offline
```

<a id="local-checks"></a>
## 本地检查

```powershell
python -m pip install -e ".[dev]"
python -m ruff check src tests
python -m mypy src
python -m unittest discover -s tests -v
python -m pip_audit
```

将 `pip_audit` 视为安全信号，而非审查替代品。若报告依赖问题，应记录 `nullstate` 是否能触达漏洞路径。

<a id="commit-style"></a>
## 提交风格

使用 conventional commit 前缀：

- `feat:`
- `fix:`
- `docs:`
- `test:`
- `chore:`

<a id="pull-request-expectations"></a>
## Pull Request 要求

每个 PR 应包含：

- 摘要
- 测试证据
- 安全影响
- 文档更新
- 相关截图或运行产物

<a id="security-expectations"></a>
## 安全要求

- 不得包含真实云凭据、LocalStack 认证 token、模型 API key、`.env` 文件、Terraform state 或未脱敏运行包。
- 公开分享运行产物前使用 `nullstate scrub`。
- 攻击执行默认保持本地。未来真实云目标工作必须明确、主动选择、受策略控制并有文档。
- 若更改红队执行器、策略执行、产物脱敏、上传计划、发布 workflow 或 CI 门禁，应包含针对性测试。
