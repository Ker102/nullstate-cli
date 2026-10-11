<a id="first-10-minutes"></a>
# 最初の 10 分

新しいオープンソース利用者に最も安全な手順です。オフライン AWS S3、モック代理、ローカル成果物を使います。

Docker、LocalStack、モデルエンドポイント、実クラウド認証情報は不要です。

<a id="1-install-from-a-checkout"></a>
## 1. チェックアウトからインストール

```powershell
git clone https://github.com/Ker102/nullstate-cli.git
cd nullstate-cli
python -m pip install -e .
```

`nullstate` が `PATH` にない場合、同じ操作に `python -m nullstate` を使います。

<a id="2-check-the-local-environment"></a>
## 2. ローカル環境を確認

```powershell
nullstate doctor --offline
nullstate status
```

期待する結果：

- CLI が Nullstate 起動/状態を表示
- この手順では Docker、Terraform、LocalStack、モデルエンドポイントがなくても問題ない

<a id="3-run-a-deterministic-offline-scan"></a>
## 3. 決定論的オフラインスキャン

自分の実行を生成する前にサニタイズ済み例を確認するには：

```powershell
nullstate report --runs-dir examples/sample-runs
nullstate summary --runs-dir examples/sample-runs --json
```

例には `report.md`、`run-bundle.json`、`dashboard.html` があり、スキャン前に主要成果物を確認できます。

```powershell
nullstate run examples/aws-public-s3 --offline --mock-agents
```

期待する結果：

- 重大度 high の S3 公開アクセス検出が一件
- レッド修正前：成功
- レッド修正後：遮断
- 成果物は `runs/<run-id>/` に出力

<a id="4-open-the-report"></a>
## 4. レポートを開く

```powershell
nullstate report
```

確認するもの：

- 検出概要
- 攻撃推論
- 修正パッチ
- 検証結果
- 実行時証拠分類

<a id="5-build-shareable-local-artifacts"></a>
## 5. 共有可能なローカル成果物を作る

```powershell
nullstate bundle
nullstate dashboard --open
nullstate sarif
nullstate evidence-manifest
nullstate evidence-verify
```

生成成果物：

- `run-bundle.json`
- `dashboard.html`
- `nullstate.sarif`
- `evidence-manifest.json`
- `evidence-verification.json`

<a id="6-scrub-before-sharing"></a>
## 6. 共有前にサニタイズ

```powershell
nullstate scrub
```

未処理 `runs/` でなく `scrubbed-runs/` のコピーを共有します。

<a id="7-optional-github-actions-gate"></a>
## 7. 任意の GitHub Actions ゲート

```powershell
nullstate init-ci github --scenario aws-public-s3 --iac-path examples/aws-public-s3
```

生成ファイル：

- `.github/workflows/nullstate.yml`
- `nullstate-policy.json`

二つをコミットすると PR でオフラインゲートを実行できます。実際のリポジトリでは `--iac-path` を Terraform ディレクトリへ調整してください。

<a id="8-optional-live-aws-localstack-path"></a>
## 8. 任意の AWS LocalStack 実行経路

Docker と LocalStack の設定後にのみ使います。

```powershell
nullstate sandbox up localstack-aws
nullstate sandbox status localstack-aws
nullstate run examples/aws-public-s3 --target localstack-aws --mock-agents
nullstate report
nullstate sandbox down localstack-aws
```

AWS 実行経路は現在実証済みのローカルシナリオです。LocalStack AWS に脆弱な fixture を配置し、制約付き匿名読み取りプローブ、決定論的修正、再プローブを行います。

<a id="current-azure-note"></a>
## 現在の Azure に関する注意

Azure Blob は決定論的オフライン検証に対応しますが、LocalStack Azure 実行には workspace/利用者の Azure Emulator 利用権が必要です。`localstack/localstack-azure-alpha` がコード `55` で終了したら `docker logs localstack-azure` を確認します。アカウントで未有効の可能性があります。
