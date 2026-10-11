<a id="open-source-readiness-milestones"></a>
# オープンソース準備マイルストーン

`nullstate` をアルファから安定 CLI にする実務目標を追跡します。

GitHub：

- 目標 1：<https://github.com/Ker102/nullstate-cli/milestone/1>
- 目標 2：<https://github.com/Ker102/nullstate-cli/milestone/3>
- 目標 3：<https://github.com/Ker102/nullstate-cli/milestone/2>

<a id="current-status"></a>
## 現状

`nullstate` は実験的バックエンドを理解するアルファ利用者向け。AWS は実行/制約証拠あり。Azure は検出、修正、マニフェスト、オフラインあり、実行は Azure Emulator 利用権待ち。

<a id="milestone-1-alpha-publication-readiness"></a>
## 目標 1：アルファ公開

目的：早期評価者に理解/利用可能。

状態：ほぼ完了。

基準：

- [x] ソース/現タグ導入 README。
- [x] `nullstate` と `python -m nullstate`。
- [x] ライセンス、貢献、行動、安全。
- [x] 秘密を求めない安全な issue。
- [x] LocalStack、Terraform 資格、モデルなし入門。
- [x] レッド境界の正直な記載。
- [x] 観測/模擬/不確定の区別。
- [x] Docker 不要処理済み例。issue #29。

<a id="milestone-2-stable-local-sandbox-validation"></a>
## 目標 2：安定ローカル検証

目的：対応経路の信頼できる証明。

状態：AWS 完了、Azure 外部権利待ち。

基準：

- [x] ローカル AWS 脆弱 S3。
- [x] AWS `attack.py` の前後匿名読取。
- [x] 実証拠で前成功/後遮断。
- [x] 起動後停止なら `sandbox up` は成功とせず失敗。
- [x] Azure 権利失敗の明瞭な案内。
- [ ] 権利解決または対応 Azure ストレージ模倣。
- [ ] Blob 前読取/後遮断を実証。
- [ ] 不可なら `azure-public-blob` に Azurite。issue #30。

<a id="milestone-3-open-source-stable-cli"></a>
## 目標 3：安定 CLI

目的：外部が導入/実行/文書範囲を信頼。

状態：未完。

基準：

- [ ] clone 不要成果物。
- [ ] wheel、sdist、SBOM、manifest、証明、検証案内。
- [x] クリーン環境の 10 分案内。
- [x] 処理済み bundle/dashboard。
- [x] 非実行を offline/雛形と表示。
- [x] 依存監査/受容リスク。
- [ ] 次タグ前 Actions dry-run。
- [ ] 最新 `pip install` の `nullstate` Windows/Linux。

注：

- Windows は 2026-07-03 ローカル成功：`python scripts/release/install_smoke.py --tag v0.1.0-alpha.2`。
- Linux は runner/dry-run で未確認。

<a id="azure-emulator-decision"></a>
## Azure Emulator 判断

トークンはキャッシュ/試用許可を有効化できても利用者にイメージ権がありません。Azure 権限でなく LocalStack 製品ライセンスです。

選択肢：

1. `LOCALSTACK_AUTH_TOKEN` の利用者権をサポートに依頼。
2. Blob V1 の Azurite、公開読取のみで ARM 全体なし。
3. デモ専用内部模倣、依存最低/維持最大、Azure でなくシミュレーターと表示。
4. Azure はオフラインのまま、AWS 実証優先。

推奨：

迅速権利なら LocalStack、不可なら Blob のみ Azurite、ARM は将来。
