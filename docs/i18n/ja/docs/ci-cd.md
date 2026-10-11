<a id="cicd"></a>
# CI/CD

<a id="when-nullstate-runs"></a>
## 実行時機

三つの安全性フィードバックを目指します。

1. **PR CI：** Terraform、CloudFormation、Bicep、Helm、ポリシー等変更時。提案分析、基準比較、任意の使い捨て検証、SARIF 公開、重大度で失敗。
2. **デプロイ後検証：** 成功後や提供者の関連変更イベント時。状態更新、ドリフト検出、影響経路検証。破壊プローブは本番外。
3. **定期保証：** 手動変更、未管理リソース、権限ドリフト、新公開サービス、Git 外経路を検出。

PR は安全にマージ可能か、デプロイ後は期待状態か、定期は前回レビュー後の変化を問います。

顧客 CI は読み取り AWS/Azure ID と私設モデル/管理資格を用意できます。将来 Cloud は処理済みバンドル、管理推論、履歴、予定、警報に対応可能。

<a id="branching-model"></a>
## ブランチ

- `main` は保護。
- `feat/sandbox-localstack` 等で開発。
- 全変更に PR。
- `vMAJOR.MINOR.PATCH` タグ。

<a id="pull-request-checks"></a>
## PR 確認

実行項目：

- 単体テスト
- Ruff lint
- mypy 型
- pip-audit

<a id="nullstate-ci-export"></a>
## CI 出力

サンドボックスなしなら決定論的オフライン：

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

`--ci` は `ci-summary.json`、原検出が `--fail-on-severity` 以上なら `2`。`none`、`low`、`medium`、`high`、`critical` に対応。`$schema` は `docs/schemas/ci-summary.schema.json`、書込前検証。

`nullstate policy-result` は既存実行の `policy-result.json` を生成し再実行不要。

`nullstate policy validate` は実行なし確認。`--output` で `policy-validation.json`、不正は `2`。

デモ/送信のみは `--fail-on-severity none`、ゲートは `--fail-on-severity high` または `--fail-on-severity critical`。失敗しつつ SARIF 送信には `continue-on-error` または出力/判定を分離。

既知受容結果はレビュー済み実行から基準作成：

```powershell
python -m nullstate baseline --runs-dir runs/ci --output nullstate-baseline.json
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --ci --baseline-file nullstate-baseline.json --runs-dir runs/ci-next
python -m nullstate policy-result --runs-dir runs/ci-next --baseline-file nullstate-baseline.json
```

`--baseline-file` は `ci-summary.json` に既知/新規数、しきい値は新規のみ、契約は同じ。

`nullstate sarif` は最新/指定 ID、SARIF 2.1.0 に検出ごと一件、重大度、証拠、修正、論理 IaC 住所を保存。`artifacts/nullstate.sarif` を GitHub 等へ。

`nullstate evidence-manifest` は SHA-256 一覧をサポート/ケース前に作成。`$schema` は `docs/schemas/evidence-manifest.schema.json`、ローカル検証。`--signing-key-env NULLSTATE_EVIDENCE_SIGNING_KEY` で CI 秘密の HMAC-SHA256、鍵を出力しない。`nullstate evidence-verify` はファイル/指定鍵署名を検証し `evidence-verification.json`、欠落/変更/他実行/不正署名は `2`。

`.github/workflows/nullstate-sarif.yml` は AWS S3 オフラインを `--ci --fail-on-severity none` で実行し脆弱デモも `github/codeql-action/upload-sarif` で送信し保存。実 IaC ゲートは `high`/`critical`。

厳しい workflow は初期化推奨：

```bash
nullstate init-ci github --scenario aws-public-s3 --iac-path examples/aws-public-s3
```

`.github/workflows/nullstate.yml` と `nullstate-policy.json` を生成。`docs/templates/github-actions/nullstate-enforcing.yml` ベースで `nullstate run --ci --fail-on-severity high`、`continue-on-error: true` で SARIF/判定/証拠/バンドル/dry-run を保持、最後にゲート失敗なら job 失敗。コミット前に `--iac-path`、`--scenario`、`--fail-on-severity` 調整。

公開/サポート/ケース前に `nullstate scrub`。

`nullstate upload --dry-run` は `upload-plan.json` を隣接出力、将来取り込み構造を準備しネットワーク/トークン値なし。`$schema` は `docs/schemas/upload-plan.schema.json`、検証/事前確認、`scrub-report.json` なしで警告。

<a id="security-checks"></a>
## 安全性チェック

- CodeQL は PR、main、週次の Python。
- Dependency Review は PR 変更。
- Dependabot は Python/Actions。

<a id="release-flow"></a>
## 公開フロー

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

タグ後 GitHub CLI で来歴/SBOM を確認：

```powershell
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli --predicate-type https://spdx.dev/Document/v2.3
```

`release-manifest.json` は wheel、sdist、`sbom.spdx.json` 隣でチェックサム一覧。GitHub 証明が来歴/SPDX を結合。クリーン `.sbom-venv` の wheel から実依存版を取得。SPDX、必須項目、根、関係を確認し `spdx-tools==0.8.5` の `pyspdxtools` をマニフェスト/証明前に実行。

GitHub OIDC の鍵不要 Sigstore で wheel、sdist、SBOM、manifest を署名。隣接 `.sigstore.json` がなければ公開前に失敗。

タグ前に手動 `Release` の `dry_run=true`。構築/検証のみで `gh release create` なし、公開はタグ push のみ。

Cosign 確認時 `--certificate-identity` のタグを対象へ：

```powershell
$wheel = Get-ChildItem dist\nullstate-*.whl | Select-Object -First 1
cosign verify-blob $wheel.FullName --bundle "$($wheel.FullName).sigstore.json" --certificate-identity "https://github.com/Ker102/nullstate-cli/.github/workflows/release.yml@refs/tags/v0.1.0" --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

<a id="required-repository-settings"></a>
## 必須設定

公開後 GitHub で：

- `main` 保護
- PR レビュー必須
- PR Checks と CodeQL 必須
- force push 禁止
- 可能なら署名コミット
- secret scanning/push protection 有効
