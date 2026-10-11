<a id="contributing"></a>
# 貢献ガイド

<a id="workflow"></a>
## ワークフロー

GitHub flow を使います。

1. issue を作成するか既存 issue を関連付けます。
2. ブランチを作成します：`feat/<short-name>`、`fix/<short-name>`、`docs/<short-name>`、`chore/<short-name>`。
3. 構造化された pull request を開きます。
4. CI とレビューを待ちます。
5. squash で `main` にマージします。

`main` への直接 push は禁止です。

<a id="local-setup"></a>
## ローカル設定

```powershell
git clone https://github.com/Ker102/nullstate-cli.git
cd nullstate-cli
python -m pip install -e ".[dev]"
nullstate doctor --offline
```

`nullstate` が `PATH` にない場合は次を使います。

```powershell
python -m nullstate doctor --offline
```

<a id="local-checks"></a>
## ローカルチェック

```powershell
python -m pip install -e ".[dev]"
python -m ruff check src tests
python -m mypy src
python -m unittest discover -s tests -v
python -m pip_audit
```

`pip_audit` は安全性の手がかりでありレビューの代替ではありません。依存関係の問題を報告した場合、`nullstate` から脆弱な経路に到達可能か記録してください。

<a id="commit-style"></a>
## コミット形式

conventional commit の接頭辞を使います。

- `feat:`
- `fix:`
- `docs:`
- `test:`
- `chore:`

<a id="pull-request-expectations"></a>
## Pull Request の要件

各 PR に次を含めます。

- 概要
- テスト証拠
- セキュリティへの影響
- 文書更新
- 関連するスクリーンショットや実行成果物

<a id="security-expectations"></a>
## セキュリティ要件

- 実クラウド認証情報、LocalStack トークン、モデル API キー、`.env`、Terraform state、未処理実行バンドルを含めないでください。
- 成果物の公開共有前に `nullstate scrub` を使ってください。
- 攻撃実行は既定でローカル限定です。将来の実クラウド対象は明示的なオプトインとポリシー制御、文書化が必要です。
- レッドランナー、ポリシー強制、成果物サニタイズ、アップロード計画、リリースワークフロー、CI ゲートの変更には対象を絞ったテストを含めてください。
