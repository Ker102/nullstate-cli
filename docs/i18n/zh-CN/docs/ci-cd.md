<a id="cicd"></a>
# CI/CD

<a id="when-nullstate-runs"></a>
## Nullstate 运行时机

目标是参与三种安全反馈循环：

1. **Pull request CI：** Terraform、CloudFormation、Bicep、Helm、策略或相关文件变更时运行。分析提议状态、比对基线，可选在一次性环境验证路径，发布 SARIF，按严重度失败。
2. **部署后验证：** 部署成功或提供商报告安全相关资源/策略事件后运行。刷新状态、检测漂移、验证受影响路径。破坏性探测不在生产执行。
3. **定期保障：** 周期性检测控制台手改、未管理资源、权限漂移、新暴露服务及 Git 外路径。

PR CI 回答是否可安全合并；部署后验证回答实际是否符合预期；定期保障回答上次审查后是否漂移。

客户 CI 可提供 AWS/Azure 只读身份和私有模型端点或托管凭据。未来 Nullstate Cloud 可接收脱敏包、托管推理、留历史、协调计划/警报。

<a id="branching-model"></a>
## 分支模型

- `main` 受保护。
- 功能分支如 `feat/sandbox-localstack`。
- 所有变更需 PR。
- 发布标签 `vMAJOR.MINOR.PATCH`。

<a id="pull-request-checks"></a>
## PR 检查

workflow 运行：

- 单元测试
- Ruff lint
- mypy 类型检查
- pip-audit 依赖审计

<a id="nullstate-ci-export"></a>
## Nullstate CI 导出

无沙箱时使用离线确定性 PR 证据：

```powershell
python -m nullstate policy validate nullstate-policy.json --output artifacts/policy-validation.json
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --ci --fail-on-severity none --runs-dir runs/ci
python -m nullstate policy-result --runs-dir runs/ci --fail-on-severity high
python -m nullstate sarif --runs-dir runs/ci --output artifacts/nullstate.sarif
python -m nullstate evidence-manifest --runs-dir runs/ci --output artifacts/evidence-manifest.json
python -m nullstate evidence-verify --runs-dir runs/ci --manifest artifacts/evidence-manifest.json --output artifacts/evidence-verification.json
python -m nullstate bundle --runs-dir runs/ci
python -m nullstate upload --runs-dir runs/ci --dry-run
```

`--ci` 写 `ci-summary.json`，原始发现达到 `--fail-on-severity` 时以 `2` 退出。阈值 `none`、`low`、`medium`、`high`、`critical`。摘要含 `$schema` 指向 `docs/schemas/ci-summary.schema.json`，写前验证。

`nullstate policy-result` 从已有运行写 `policy-result.json`，提供独立决策 JSON，无需重跑。

`nullstate policy validate` 不运行场景；`--output` 时写 `policy-validation.json`，格式错误/无效退出 `2`。

演示/纯上传用 `--fail-on-severity none`；门禁用 `--fail-on-severity high` 或 `--fail-on-severity critical`。要失败且上传 SARIF，明确处理 `continue-on-error` 或分离导出/强制步骤。

已有接受发现时从已审查运行创建基线：

```powershell
python -m nullstate baseline --runs-dir runs/ci --output nullstate-baseline.json
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --ci --baseline-file nullstate-baseline.json --runs-dir runs/ci-next
python -m nullstate policy-result --runs-dir runs/ci-next --baseline-file nullstate-baseline.json
```

`--baseline-file` 让 `ci-summary.json` 记录已知/新发现，仅对新发现评估阈值，保持相同已验证契约。

`nullstate sarif` 默认最新或指定 ID。写 SARIF 2.1.0，每发现一结果，保留严重度、证据、修复指导和 IaC 地址作为逻辑位置。上传 `artifacts/nullstate.sarif` 到 GitHub 或其他 SARIF 工具。

`nullstate evidence-manifest` 为共享证据写 SHA-256 清单，用于工单、支持或案例完整性。含 `$schema` 指向 `docs/schemas/evidence-manifest.schema.json`，本地写前验证。加 `--signing-key-env NULLSTATE_EVIDENCE_SIGNING_KEY` 用 CI secret 作 HMAC-SHA256，密钥不写产物。`nullstate evidence-verify` 检查当前文件、提供环境密钥时验签，写 `evidence-verification.json`；缺失、改变、其他运行复制或签名无效时退出 `2`。

首个示例 `.github/workflows/nullstate-sarif.yml` 跑离线 AWS S3，`--ci --fail-on-severity none` 让故意漏洞 demo 仍以 `github/codeql-action/upload-sarif` 上传并留产物。真实 IaC 门禁改为 `high` 或 `critical`。

更严格流程优先初始化：

```bash
nullstate init-ci github --scenario aws-public-s3 --iac-path examples/aws-public-s3
```

写 `.github/workflows/nullstate.yml` 和场景策略 `nullstate-policy.json`。基于 `docs/templates/github-actions/nullstate-enforcing.yml`，运行 `nullstate run --ci --fail-on-severity high`，保留 `continue-on-error: true` 以生成 SARIF、决策、清单、包、dry-run 计划，最后门禁失败则作业失败。提交前调整 `--iac-path`、`--scenario`、`--fail-on-severity`。

公开 issue、支持、案例附报告/包前运行 `nullstate scrub`。

`nullstate upload --dry-run` 在包旁写 `upload-plan.json`，为未来云接收准备请求结构，不联网不保存 token 值。含 `$schema` 指向 `docs/schemas/upload-plan.schema.json`，本地验证、记录脱敏预检，缺少 `scrub-report.json` 时警告。

<a id="security-checks"></a>
## 安全检查

- CodeQL 在 PR、main 推送、每周扫描 Python。
- Dependency Review 检查 PR 依赖变更。
- Dependabot 监控 Python 和 Actions 依赖。

<a id="release-flow"></a>
## 发布流程

```text
manual workflow_dispatch dry_run=true
-> release workflow rehearses package build, SBOM validation, attestations, signing, and signature checks
-> no GitHub release is created
merge to main
-> update CHANGELOG.md
-> tag v0.1.0
-> release workflow builds package
-> release workflow smoke-installs the built wheel and runs nullstate doctor --offline
-> sbom.spdx.json records the installed wheel and runtime dependency versions
-> SBOM validation checks required package fields and root-package relationships
-> SPDX tools validate the generated SBOM document
-> release-manifest.json records SHA-256 digests and sizes
-> GitHub artifact attestations bind provenance and SBOM data to dist/*
-> Sigstore keyless signing writes .sigstore.json bundles beside primary release assets
-> GitHub release created with generated notes
```

标签发布后，用 GitHub CLI 验证来源和 SBOM predicate：

```powershell
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli --predicate-type https://spdx.dev/Document/v2.3
```

`release-manifest.json` 与 wheel、sdist、`sbom.spdx.json` 一起上传，作为校验和索引；GitHub 证明将来源/SPDX SBOM 绑定资源。SBOM 从干净 `.sbom-venv` 中 wheel 生成，捕获实际 runtime 版本。workflow 验 SPDX 版本、字段、根包、关系，清单/证明前运行 `spdx-tools==0.8.5` 的 `pyspdxtools`。

证明后通过 GitHub OIDC 做 Sigstore 无密钥签名，涵盖 wheel、sdist、SBOM、清单；缺任何相邻 `.sigstore.json` 则发布前失败。

打标签前手动 `Release`，`dry_run=true`：构建验证但不 `gh release create`；发布仅允许标签推送。

用 Cosign 验下载 wheel，将 `--certificate-identity` 标签换为被验版本：

```powershell
$wheel = Get-ChildItem dist\nullstate-*.whl | Select-Object -First 1
cosign verify-blob $wheel.FullName --bundle "$($wheel.FullName).sigstore.json" --certificate-identity "https://github.com/Ker102/nullstate-cli/.github/workflows/release.yml@refs/tags/v0.1.0" --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

<a id="required-repository-settings"></a>
## 必需仓库设置

发布后配置 GitHub：

- 保护 `main`
- 要求 PR 审查
- 要求 PR Checks 和 CodeQL
- 阻止强制推送
- 可行时要求签名提交
- 启用 secret scanning 和 push protection
