<a id="adr-0003-localstack-azure-for-v1"></a>
# ADR-0003：V1 に LocalStack Azure

<a id="status"></a>
## 状態

採用。

<a id="context"></a>
## 背景

初デモ Terraform Azure。実 Azure は認証、費用、清掃、安全リスク増。

<a id="decision"></a>
## 判断

初実行を LocalStack Azure、プランのみを代替に。

<a id="consequences"></a>
## 結果

- 実 Azure 資源不要。
- 実行には Docker と `LOCALSTACK_AUTH_TOKEN`。
- 連携と LocalStack 同梱は区別。
