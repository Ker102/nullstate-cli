<a id="enterprise-readiness"></a>
# 企業向け準備

`nullstate` をローカル試作品から企業 DevSecOps に進める制御一覧。現行強制と、チーム有料/クラウド/自前利用前の追加を区別します。

<a id="current-controls"></a>
## 現行制御

| 制御 | 状態 | 証拠 |
|---|---|---|
| 決定論的検出 | 実装 | `src/nullstate/findings.py` |
| 決定論的修正 | 実装 | `src/nullstate/remediation.py` |
| コピー環境 | 実装 | 原 IaC 不変 |
| 制限ランナー | 実装 | 実行内 `attack.py` のみ |
| マニフェスト入力 | 実装 | `attack-manifest.json` はシナリオ、バックエンド、URL、資源の検証済み情報 |
| 実行ログ | 実装 | `red-tool` 出力/時間 |
| ローカル強制 | 実装 | 非ローカル HTTP を既定拒否 |
| 攻撃ハッシュ | 実装 | `red-tool` の script/manifest SHA-256 |
| 切詰情報 | 実装 | `red-tool` の stdout/stderr |
| 非破壊処理 | 実装 | `nullstate scrub` コピー/除去 |
| 送信事前確認 | 実装 | `nullstate upload --dry-run` 状態/警告 |
| 送信契約 | 実装 | `docs/schemas/upload-plan.schema.json` と CLI 検証 |
| 証拠分類 | 実装 | 実行/不明/模擬 |
| 個人画面/包 | 実装 | `nullstate dashboard`、`nullstate bundle`、`docs/schemas/run-bundle.schema.json` |
| 赤ポリシー | 実装 | `nullstate policy init`、プリセット、`run --policy-file` がシナリオ、バックエンド、段階、引数、分類、ホスト、命令、時間、出力を強制 |
| ポリシー確認 | 実装 | `nullstate policy validate` と任意 `policy-validation.json` |
| 証拠整合性 | 実装 | `nullstate evidence-manifest` の SHA-256、任意 HMAC |
| 証拠確認 | 実装 | `nullstate evidence-verify` の欠落/変更/コピー/HMAC 検出 |
| 公開来歴 | 実装 | `release-manifest.json`、`dist/*` GitHub 証明 |
| SBOM | 実装 | クリーン wheel、`sbom.spdx.json` のローカル/SPDX 検証/証明 |
| 鍵不要署名 | 実装 | GitHub OIDC/Sigstore |
| 公開予行 | 実装 | `workflow_dispatch`、公開なし |
| 規則版 | 実装 | `remediation.json` の版、シナリオ、ファイル、ID、v1 契約 |

<a id="required-before-enterprise-claims"></a>
## 企業主張前

<a id="local-only-enforcement"></a>
### ローカル限定

既定対象はローカル：

- `offline://...`
- `local://...`
- `127.0.0.1`
- `localhost`
- `localhost.localstack.cloud`

非ローカル HTTP は拒否。実クラウドには既定無効の明示 `--allow-live-cloud`。`events.jsonl` が承認、赤イベントが命令ごとの有効状態を記録。`allowed_target_hosts` で完全ホスト名/`*.domain` を追加制約。

<a id="command-allowlist-policy"></a>
### 命令許可

テンプレート制。ポリシーに：

- 許可シナリオ
- 許可バックエンド
- 生成スクリプト名
- CLI 引数
- 最大時間
- stdout/stderr バイト上限
- 分類/ホストパターン

モデルは説明するが任意シェルを生成しない。

`nullstate policy init` は `$schema` を `docs/schemas/nullstate-policy.schema.json` とし検証後 JSON 出力。`nullstate policy init --scenario <name>` は既知組合せの狭い設定で、全雛形を許可しない CI 向け。`nullstate policy validate` は実行前確認。`nullstate run --policy-file` はシナリオ、バックエンド、段階、`attack.py` 引数、分類、ホスト、ID、時間、出力を `attack.py` 前に制約。完全エンジンでなく将来契約。

`nullstate run --ci` は `ci-summary.json` に判定、終了、しきい値、数、基準区分、前後を記録し `docs/schemas/ci-summary.schema.json` で検証。

<a id="event-schema-hardening"></a>
### イベント強化

`red-tool` は初期監査情報：

- `schema_version`
- `command_policy_id`
- `attack_script_sha256`
- `manifest_sha256`

将来詳細なポリシー追加。現行には：

- `stdout_truncated`
- `stderr_truncated`

さらに：

- `live_cloud_allowed`
- `target_classification`、明示クラウド有効時 `external-http`

CI/サポート/遵守で再現し監査しやすくします。

`nullstate evidence-manifest` は共有物 SHA-256/サイズ。コピー、Terraform 内部、Python cache、自分、検証出力を除外。`$schema` は `docs/schemas/evidence-manifest.schema.json`、書込前検証。`--signing-key-env` は環境秘密の HMAC-SHA256、鍵は保存しない。`nullstate evidence-verify` が再計算して `evidence-verification.json`、欠落/変更/異なる run ID/署名で `2`。

タグは `release-manifest.json` とクリーン wheel の `sbom.spdx.json`、構造と `pyspdxtools` を証明前検証。GitHub は `dist/*` 来歴/SPDX、Sigstore は wheel、sdist、SBOM、manifest の隣接 `.sigstore.json`。供給来歴は実行 HMAC と別。

`dry_run=true` は構築、検証、証明、署名、包の予行、公開なし。

`remediation.json` と `remediation.patch` は版、シナリオ、変更旗、ファイル、ID。`$schema` は `docs/schemas/remediation-metadata.schema.json`、利用前検証し正確な規則に結合。

`run-bundle.json` はローカル検証、`$schema` は `docs/schemas/run-bundle.schema.json`。`nullstate bundle` は上位契約不正で出力前失敗。

画面は検出、規則、schema、一覧、時系列、抜粋。単ユーザー/ファイル式でチーム履歴、RBAC、定期/遵守は有料。

<a id="artifact-scrubbing"></a>
### サニタイズ

公開/送信/添付前 `nullstate scrub`、コピーから除去：

- LocalStack token
- モデル key
- クラウド ID
- Azure テナント/購読 ID
- 私設 URL/IP
- Terraform state 値
- 提供者資格
- 顧客文脈入り生プロンプト

`scrub-report.json` に処理ファイル/規則。

`nullstate upload --dry-run` は `scrub-report.json` と `preflight.scrub` を `upload-plan.json` に記録。`$schema` は `docs/schemas/upload-plan.schema.json`、検証。生実行の計画は許可、`upload_recommended: false` と警告。

<a id="evidence-classification"></a>
### 証拠分類

過大主張せず：

- `runtime exploit observed`：出力で object/blob 読取証明。
- `runtime probe did not observe exploit`：到達し修正後阻断/不可。
- `runtime probe inconclusive`：模倣/経路/実行が証明を妨げた。
- `offline deterministic simulation`：実行プローブなし。

悪用成功というなら観測証拠かオフライン模擬と明記。

<a id="near-term-readiness-tasks"></a>
## 直近

1. Azure 実検証と制限。
2. 提供者許可/承認付きのみ実クラウド。

<a id="commercial-boundary"></a>
## 商業境界

公開 CLI は local/offline、LocalStack、報告、包、個人画面。有料はガバナンス：

- 中央履歴
- RBAC/監査
- policy-as-code 許可
- 管理モデル
- サポート包
- 遵守出力
- 定期/警報
- 私設配置支援
