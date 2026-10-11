<a id="cost-report"></a>
# コスト報告

<a id="summary"></a>
## 概要

既定でクラウド費用をほぼゼロに。オフラインはローカル、LocalStack は Docker、AMD はハッカソン証拠収集のみ。

<a id="cost-items"></a>
## 項目

| 項目 | 予想費用 | 注記 |
|---|---:|---|
| CLI | 0 | ローカル Python |
| オフライン | 0 | クラウド/モデルなし |
| LocalStack Azure | アクセス次第 | トークン必要 |
| AMD Developer Cloud | ハッカソン枠 | MI300X |
| Fireworks | 提供者次第 | GPU 待ち代替 |
| GitHub Actions | 無料/低額枠次第 | 軽いテスト |

<a id="controls"></a>
## 制御

- 既定で実 Azure なし。
- 長期クラウド資源作成なし。
- `nullstate sandbox down` で停止。

<a id="future-tracking"></a>
## 将来記録

ケース公開前に実提供時間、GPU 時間、LocalStack/クラウド費用を記録。

各実行のオフライン/管理/AMD を記録し、待機中の代替利用を正確に示す。
