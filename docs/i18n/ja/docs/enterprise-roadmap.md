<a id="enterprise-and-monetization-roadmap"></a>
# 企業と収益化ロードマップ

`nullstate` をハッカソン CLI だけでなく将来の企業 DevSecOps と位置付けます。

<a id="product-positioning"></a>
## 位置付け

`nullstate` は証拠付きクラウド経路検証です。IaC と AWS/Azure を相関し ID ごとのデータ/能力を判断、管理下で証明、決定論的修正、証拠を保存。

中心メッセージ：

> スキャナーは可能な問題を示します。Nullstate は経路を証明、修正、遮断検証します。

全アカウントの完全 IaC 不要。意図と読み取り探索の資源、ID、ネットワーク、ログ、変化を正規化し必要最小限だけ再構築。

AI を主要主体に：専用 ID、IAM、サービスプリンシパル、管理/workload、gateway、委任。エージェント、prompt、記憶、連携、MCP、plugin、下流資格侵害の影響を算出。

外部態勢は有料機会。ID 結合、来歴、digest、証明、patch/脆弱性、network、tool、鮮度、log、失効を継続検証。到達データ/権限と結び、黒箱点数にしない。

<a id="target-customers"></a>
## 顧客

<a id="primary"></a>
### 主

- Terraform 中心 DevSecOps
- 安全既定 IaC プラットフォーム
- 修正 SLA 検証チーム
- 証拠付き相談

<a id="secondary"></a>
### 副

- SaaS にインフラを送れない規制企業
- 私有 AI 安全企業
- MSP/移行パートナー

<a id="core-value-propositions"></a>
## 価値

<a id="1-evidence-over-alerts"></a>
### 1. 警報より証拠

検出で止まらず `nullstate` は時系列：

1. 検出
2. レッド推論
3. sandbox 命令証拠
4. patch
5. 修正後検証
6. 報告

<a id="2-local-first-and-private"></a>
### 2. ローカルと私有

機密 IaC、計画、log を顧客内、private OpenAI 互換。

<a id="3-deterministic-security-core"></a>
### 3. 決定論的核

モデルは合否を決めず検出/修正/検証が信頼性を担います。

<a id="4-devsecops-native-cli"></a>
### 4. DevSecOps CLI

ローカル、CI、一時検証で実行。

<a id="enterprise-product-tiers"></a>
## 製品階層

<a id="open-source-cli"></a>
### 公開 CLI

目的：開発者採用/信頼。

機能：

- local/offline
- 限定シナリオ
- 報告
- 制約 runner
- LocalStack 基本
- コミュニティ文書

<a id="team-edition"></a>
### Team

目的：小チーム/相談。

機能：

- 拡張 pack
- HTML/PDF
- サニタイズ
- baseline
- Actions/GitLab CI
- 履歴 export
- private model 設定

候補価格：

- 席 19-49 EUR/月
- または repo 49-199 EUR/月

<a id="enterprise-edition"></a>
### Enterprise

目的：遵守/私有インフラ企業。

機能：

- tool policy-as-code
- SSO/SAML/OIDC
- 監査
- 中央証拠
- role/team
- private 配置支援
- custom scenario
- SLA
- Jira、ServiceNow、Slack、SIEM、GRC

候補価格：

- 年約 15k-50k EUR/年から
- scenario/support は追加

<a id="monetization-paths"></a>
## 収益経路

<a id="path-a-open-core-devsecops-cli"></a>
### A：Open-core CLI

核は公開、有料：

- 企業 pack
- cloud 画面
- hosted 証拠
- private 支援
- 遵守 export

利点：

- 開発採用
- GitHub 信頼
- community 信頼

欠点：

- 無料/有料境界
- 支援負担

<a id="path-b-security-consultancy-tooling"></a>
### B：相談ツール

`nullstate` を有料評価の差別化に。

提供：

- IaC 紫チーム評価
- Terraform 強化
- 修正 PR
- 監査証拠

利点：

- 初収益が容易
- 完全 SaaS 不要
- 顧客事例

欠点：

- サービス拡張難

<a id="path-c-enterprise-private-ai-security-platform"></a>
### C：私有 AI 企業

IaC/cloud 制御の私有検証層。

利点：

- MI300X/private 一致
- 大予算

欠点：

- 長販売
- 強化/連携

<a id="recommended-near-term-strategy"></a>
## 短期戦略

A+B 混合：

1. CLI 公開。
2. 強い IaC 証拠ブランド。
3. portfolio/事例で注目。
4. 有料評価/導入を先に。
5. 反復需要を Team/Enterprise 機能へ。

<a id="product-architecture-cli-local-gui-and-paid-platform"></a>
## CLI、ローカル GUI、有料

CLI は公開 engine、local/CI、成果物、portable bundle。

無料 GUI は単独 viewer/operator、`runs/`、dashboard、run/report/bundle/sandbox。cloud login、team、遵守、alert、管理 model なし。

有料 cloud/self-hosted は bundle 取込、team、model、履歴、support、定期、alert、連携、RBAC、audit、遵守。

`run-bundle.json` は CLI/無料画面/CI/support/将来契約。`docs/schemas/run-bundle.schema.json` v1 を書込前検証。

`nullstate upload --dry-run` は no-network 計画：URL、checksum、数、token 有無、scrub 状態、送信/値保存なし。`docs/schemas/upload-plan.schema.json` v1 検証。

<a id="ci-and-managed-model-inference"></a>
## CI と管理モデル

二つのモード：

- 顧客：`NULLSTATE_LLM_BASE_URL`、`NULLSTATE_LLM_API_KEY` を secret。
- Nullstate：`NULLSTATE_CLOUD_TOKEN` と Cloud 赤青。

管理 mode は組織、project、run、model、token、遅延、費用で計量でき有料。

三 trigger：

1. IaC/policy PR：提案、baseline、任意高リスク使捨検証、policy gate。
2. Terraform/CloudFormation/Bicep 等後：inventory、変化、経路。
3. 定期：console、未管理、権限、公開、古い risk、Git 外。

本番探索は read-only、非破壊も承認。exploit は忠実度で emulator/twin/cluster/専用 AWS/Azure。

<a id="support-automation-and-alerts"></a>
## 支援/自動化/警報

有料 panel、ticket に処理済み bundle、版、ID、scenario、dashboard。

接続 repo/upload IaC 定期 scan。新 critical、観測 exploit、修正/CI 失敗、古い risk、model failure。email/webhook から Slack、Teams、Jira、GitHub Issues、SIEM。

<a id="brand-direction"></a>
## ブランド

<a id="name"></a>
### 名前

`nullstate` は安全基準へ戻す意味。

<a id="tagline-options"></a>
### 標語

- IaC risk の証明、修正、検証。
- Terraform 紫チーム。
- 検出から遮断。
- 証拠 cloud DevSecOps。
- ローカル IaC 攻撃検証。

推奨：

> cloud 攻撃経路を証明、修正、検証。

<a id="brand-personality"></a>
### 性格

- 精確
- 技術
- 信頼
- 安全優先
- 企業意識
- hype なし

深い tool 前は自律 hacker と誇張しない。推奨：

- 制約レッド
- 証拠検証
- ローカル紫チーム

<a id="enterprise-reliability-requirements"></a>
## 企業信頼性

依存前に：

1. 核心実 probe。
2. 模擬/推測/観測を区別。
3. policy allowlist。scenario、backend、stage、引数、class、host、command、timeout、output は検証済み。
4. scrub。
5. 安定 schema、生成 manifest は実行前検証。
6. machine CI、`nullstate run --ci` と `ci-summary.json` は提供済み。
7. SARIF/JSON/policy-result 提供済み。
8. `nullstate evidence-manifest` の SHA-256/HMAC、v1 と `nullstate evidence-verify`。
9. checksum、clean wheel SBOM、`sbom.spdx.json`、GitHub 証明、Sigstore、dry-run。
10. `remediation.json` の版/ファイル/規則、`$schema`、v1。
11. 明示なし実 cloud なし。

<a id="next-feature-priorities"></a>
## 優先

<a id="p0-trust-and-correctness"></a>
### P0：信頼

- S3 実読取
- runtime 報告
- scrub
- `ci-summary.json` 判定/終了

<a id="p1-cicd-adoption"></a>
### P1：CI/CD

- `nullstate run --ci`
- `nullstate sarif`
- Actions
- `nullstate baseline`、`--baseline-file`
- `nullstate upload --dry-run`
- `docs/schemas/upload-plan.schema.json`
- `docs/schemas/attack-manifest.schema.json`

<a id="p2-enterprise-controls"></a>
### P2：企業

- scenario/backend/stage/class/host/command/timeout/output policy
- `nullstate policy init` 設定
- `docs/schemas/nullstate-policy.schema.json`
- 組織 config
- `nullstate evidence-manifest`
- `docs/schemas/evidence-manifest.schema.json`
- `nullstate evidence-verify`
- HMAC 任意
- GitHub 来歴
- GitHub SBOM
- Sigstore
- 初 tag 手順
- `remediation.json` 検証
- AWS/Azure AI ID
- agent/委任/runtime/tool/下流の分離
- 合成と管理 tool で injection/excessive agency
- agent 間信頼/共有
- 外部態勢/鮮度
- 署名/digest/SLSA/SPIFFE/SPIRE/hardware
- 証拠欠落/古さで降権 gateway

<a id="p3-growth-and-brand"></a>
### P3：成長

- 事例
- 動画
- 技術記事
- scanner 比較
- CLI GIF landing

<a id="case-study-angle"></a>
## ケース角度

scanner でなく：

> ローカル CLI で Terraform を再現ループに：検出、推論、制限命令、確定修正、遮断、証拠。

正直な制限：

> ハッカソンは安全境界あり、次は health probe を sandbox exploit へ。

正直さは信頼を強めます。

<a id="success-metrics"></a>
## 指標

技術：

- 実証数
- fixture 誤報
- 修正成功
- 再現性
- command 証拠

業務：

- star/fork
- 動画完了
- 問合せ
- pilot
- 有料 lead
- CI 反復

<a id="90-day-roadmap"></a>
## 90 日

<a id="days-1-14"></a>
### 1-14 日

- S3 実 exploit
- runtime 報告
- scrub
- 技術案内改善
- 事例公開

<a id="days-15-30"></a>
### 15-30 日

- Azure 実/明示制限
- baseline/severity 超 CI
- SARIF/JSON
- Actions

<a id="days-31-60"></a>
### 31-60 日

- AWS/Azure pack
- command/class/host policy
- 整合 manifest
- 署名検証
- 事例 landing

<a id="days-61-90"></a>
### 61-90 日

- 初 design partner
- 有料評価
- team/証拠原型
- 企業配置
