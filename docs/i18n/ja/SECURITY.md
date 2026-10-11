<a id="security-policy"></a>
# セキュリティポリシー

<a id="supported-versions"></a>
## 対応バージョン

`nullstate` は 1.0 未満です。安全性修正は最新 `main` と、評価者向け公開が必要な場合の最新プレリリースタグを対象にします。

| バージョン | サポート |
|---|---|
| `main` | あり |
| 最新プレリリース | あり |
| 以前のプレリリース | 可能な範囲 |

<a id="reporting-a-vulnerability"></a>
## 脆弱性の報告

nullstate 自体の悪用可能な脆弱性について公開 issue を開かないでください。保守者へ非公開で連絡するか、有効なら GitHub の非公開脆弱性報告を使ってください。修正または緩和策の提供後にのみ詳細を公開してください。

<a id="security-boundaries"></a>
## セキュリティ境界

nullstate は意図的に脆弱なローカルサンドボックスのテスト用です。操作者が環境を所有しリスクを理解している場合以外、本番インフラへ向けてはいけません。

V1 の既定：

- 実 Azure は既定で実行しない
- LocalStack/Docker サンドボックスは明示的な起動時のみ
- 実行成果物はローカルファイル
- 秘密はコミットされたファイルではなく環境変数で提供
- 制約付きレッドプローブは実行ディレクトリの生成 `attack.py` のみ実行
- 非ローカル HTTP プローブは明示的操作者承認とポリシー制御が必要

<a id="secret-handling"></a>
## 秘密の扱い

絶対にコミットしないもの：

- `LOCALSTACK_AUTH_TOKEN`
- モデル API キー
- クラウド認証情報
- Terraform state
- `.env`
- 実際の `.tfvars`

設定の文書化には `.env.example` を使います。

issue、チケット、ケーススタディ、サポート依頼へ成果物を添付する前に：

```powershell
nullstate scrub
```

未処理の `runs/` ではなく `scrubbed-runs/` のサニタイズ済みコピーを添付してください。
