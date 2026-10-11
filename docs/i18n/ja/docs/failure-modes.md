<a id="failure-modes"></a>
# 障害モード

<a id="localstack-azure-unavailable"></a>
## Azure LocalStack なし

影響：実サンドボックス不可。

代替：`--offline` または `--target plan-only`。

<a id="missing-docker"></a>
## Docker なし

影響：実行環境起動不可。

代替：プラン解析/報告。

<a id="missing-model-endpoint"></a>
## モデルなし

影響：本当の赤/青呼出不可。

代替：モックで全デモ。

<a id="unknown-model-provider"></a>
## 未知提供者

影響：互換 URL 不明。

代替：`NULLSTATE_LLM_PROVIDER` は `custom`、`google`、`claude`、自前なら `NULLSTATE_LLM_BASE_URL` またはロール URL。

<a id="terraform-provider-mismatch"></a>
## Terraform 不一致

影響：`terraform init`、`plan` 失敗。

代替：fixture の静的解析。

<a id="model-output-is-wrong"></a>
## モデル誤り

影響：説明/修正が誤誘導。

制御：V1 は決定論的検出と修正が正本。

<a id="report-includes-sensitive-data"></a>
## 機密報告

影響：公開ケースで漏洩。

制御：公開前確認、`nullstate scrub` と `scrub-report.json`。
