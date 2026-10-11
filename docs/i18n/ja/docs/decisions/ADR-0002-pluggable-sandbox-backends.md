<a id="adr-0002-pluggable-sandbox-backends"></a>
# ADR-0002：交換可能サンドボックス

<a id="status"></a>
## 状態

採用。

<a id="context"></a>
## 背景

将来クラウド IaC、Kubernetes、Compose、オンプレミスに対応が必要。

<a id="decision"></a>
## 判断

三モードのアダプター登録：

- 実行可能
- デジタルツイン
- プランのみ

<a id="consequences"></a>
## 結果

- V1 は強い対象一つと将来対応を提供。
- 万能エミュレーターを装わずオンプレミスをモデル化。
- 一部は完全悪用でなく文書付き雛形。
