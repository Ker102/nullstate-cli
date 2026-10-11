<a id="case-study-outline"></a>
# ケーススタディ構成

<a id="problem"></a>
## 問題

Terraform 提供が悪用可能性検証を上回ります。静的検出は潜在リスクであり、実攻撃や修正の遮断を証明しません。

<a id="solution"></a>
## 解決

`nullstate` はローカル紫チーム Terraform ループ：

- 予定インフラ分析。
- レッド悪用試行。
- ブルー修正生成。
- パッチ後再検証。
- 証拠報告。

<a id="demo-scenario"></a>
## デモ

実証経路は LocalStack 公開 S3：`nullstate` が検出、制約匿名読取、Terraform 修正、遮断確認。Azure Blob は同じ決定論的処理だが利用権または Azurite 等ストレージ代替待ち。

<a id="why-amd-mi300x"></a>
## AMD MI300X の理由

長文計画 JSON、ログ、悪用出力、差分をローカルへ送り、外部 API 遅延/データ露出を避ける設計。

<a id="next-steps"></a>
## 次

- Azure 共有キー、公開ネットワーク、Key Vault ルール。
- Azure 利用権解決か Azurite。
- 同じ成果物モデルで Kubernetes/Compose/オンプレ実行。
- vLLM `/metrics` と `amd-smi`、`rocm-smi` の GPU 証拠。
