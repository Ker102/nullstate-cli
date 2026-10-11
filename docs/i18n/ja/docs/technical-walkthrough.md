<a id="technical-walkthrough"></a>
# 技術解説

この文書は、最初の CLI コマンドから最終的なレポート成果物まで、`nullstate` がどのように動作するかを説明します。実装の流れ、セキュリティ境界、現在の拡張ポイントを理解したいレビュー担当者向けに書かれています。

<a id="what-nullstate-runs"></a>
## Nullstate が実行するもの

`nullstate` は、Infrastructure as Code を対象とするローカル優先のパープルチームループです。現在の実装は、Terraform によるストレージ公開のシナリオを中心としています。

- AWS S3 のパブリックアクセスブロックが無効
- Azure Blob コンテナーへのパブリックアクセス

また、Kubernetes、Docker Compose、オンプレミスのデジタルツイン、汎用的なプランレビュー向けのオフラインシナリオのひな形も含まれています。

CLI は次の三つの層を組み合わせます。

1. 検出結果、修復、合否検証のための決定論的なセキュリティロジック。
2. LocalStack などのローカル実行対象に対応するサンドボックスアダプター。
3. OpenAI 互換エンドポイントを通じた、モデル支援によるレッドチームとブルーチームの推論。

モデルは推論と説明を支援します。脆弱性が存在するか、修復が成功したかを判断する際の正とする情報源ではありません。

<a id="demo-command-flow"></a>
## デモコマンドの流れ

一般的なオフラインの流れ：

```powershell
nullstate
nullstate status
nullstate run examples/aws-public-s3 --offline
nullstate report
```

一般的な LocalStack AWS のライブ実行の流れ：

```powershell
nullstate sandbox up localstack-aws
nullstate sandbox status localstack-aws
nullstate run examples/aws-public-s3 --target localstack-aws
nullstate report
```

一般的な LocalStack Azure のライブ実行の流れ：

```powershell
nullstate sandbox up localstack-azure
nullstate sandbox status localstack-azure
nullstate run examples/azure-public-blob --target localstack-azure
nullstate report
```

セルフホストのモデルエンドポイントが利用できる場合は、カスタムプロバイダーを使い、共通のエンドポイントを一つ設定します。

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_LLM_BASE_URL = "http://127.0.0.1:8000"
```

または、ロールごとにエンドポイントを設定します。

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
```

マネージドプロバイダーのプリセットを使うと、自分のキーを持ち込むユーザーはエンドポイントの設定を省略できます。

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
```

`claude` プリセットも Anthropic の OpenAI SDK 互換レイヤーを通じて利用できますが、ネイティブの Claude アダプターができるまでは実験的なものとして扱う必要があります。

<a id="runtime-modes"></a>
## 実行モード

<a id="offline-mode"></a>
### オフラインモード

`--offline` は Terraform の実行とクラウドエミュレーターへの呼び出しを省略します。CLI は静的な IaC 解析と決定論的なシナリオ動作を使用します。このモードは、Docker、LocalStack、GPU がなくても再現可能なデモ、テスト、開発を行うために使います。

重要な点：`--offline` はモデル呼び出しを自動的には無効にしません。モデルエンドポイントの環境変数が設定されていると、レッドとブルーのエージェント呼び出しは引き続きそれらのエンドポイントを使います。完全に決定論的でモデルを使わない動作が必要な場合は、`--mock-agents` を使用してください。

<a id="live-localstack-mode"></a>
### LocalStack ライブモード

ライブモードは Terraform プロジェクトを実行用ワークスペースにコピーし、Terraform の自動化コマンドを実行し、LocalStack を対象にレッド/ブルーループを実行し、コピー先のワークスペースに修復を適用して、再度検証します。

元の Terraform ディレクトリは変更されません。修復は次の場所で行われます。

```text
runs/<run-id>/workspace/
```

<a id="model-endpoint-mode"></a>
### モデルエンドポイントモード

モデルエンドポイントは OpenAI 互換 API を公開する必要があります。これにより、同じ CLI 統合をローカルの vLLM、SGLang、マネージドプロバイダーのプリセット、カスタムプロキシで使用できます。

プロバイダーの解決は次の順序で行います。

1. ロール固有の CLI フラグまたは環境変数の値
2. 共通の CLI フラグまたは環境変数の値
3. プロバイダープリセットの既定 URL
4. エンドポイントが設定されていない場合は決定論的なモックエージェントにフォールバック

`google` プリセットは Gemini の OpenAI 互換エンドポイントに解決されます。`claude` プリセットは Anthropic の OpenAI SDK 互換エンドポイントに解決されます。`custom` モードと `openai-compatible` モードは、ロール固有の URL が提供されていない限り、ベース URL が必要です。

CLI は、応答に `usage` フィールドがある場合、そこからモデルのトークン数とレイテンシーを記録します。また、エンドポイントから Prometheus 形式の `/metrics` を取得しようとし、生のメトリクススナップショットを実行ディレクトリに書き込みます。

<a id="end-to-end-execution-path"></a>
## エンドツーエンドの実行経路

<a id="1-command-entry"></a>
### 1. コマンドの入口

エントリーポイント：

```text
src/nullstate/cli.py
```

`run` コマンドは次を受け取ります。

- Terraform ディレクトリ
- 対象バックエンド、または `auto`
- シナリオ、または `auto`
- オフライン/モックのフラグ
- 実行成果物のディレクトリ
- レッドとブルーのモデル設定

コマンドが指定されない場合、CLI はブランド表示付きの起動画面と、次に使う可能性のあるコマンドを出力します。

<a id="2-scenario-inference"></a>
### 2. シナリオの推定

関連ファイル：

```text
src/nullstate/scenario_detection.py
src/nullstate/scenarios.py
```

`--scenario auto` を使うと、CLI は IaC ディレクトリを調べ、入力を既知のシナリオに対応付けます。例：

- `examples/aws-public-s3` は `aws-public-s3` に対応
- `examples/azure-public-blob` は `azure-public-blob` に対応

シナリオ定義が既定のサンドボックスバックエンドを選びます。ユーザーは `--target` で引き続きこれを上書きできます。

<a id="3-sandbox-backend-selection"></a>
### 3. サンドボックスバックエンドの選択

関連ファイル：

```text
src/nullstate/sandbox.py
```

サンドボックスバックエンドは次を定義します。

- バックエンド名
- 対象の IaC の種類
- 実行モード
- Docker イメージ
- 起動/停止コマンド
- 実行時プローブ

現在のバックエンドには次があります。

| バックエンド | 用途 |
|---|---|
| `localstack-aws` | AWS 形式のストレージシナリオのライブ実行 |
| `localstack-azure` | Azure 形式のストレージシナリオのライブ実行 |
| `kind-kubernetes` | Kubernetes シナリオのひな形 |
| `docker-compose` | Docker Compose デジタルツインのひな形 |
| `microvm-onprem` | オンプレミスのデジタルツインのひな形 |
| `plan-only` | 実行環境を使わない解析モード |

`nullstate sandbox up` はバックエンドを起動します。`nullstate sandbox status` は、該当する場合に Docker と HTTP の到達性を確認します。

<a id="4-run-workspace-creation"></a>
### 4. 実行ワークスペースの作成

CLI は新しい実行ディレクトリを作成します。

```text
runs/<run-id>/
```

入力の Terraform ディレクトリを次の場所にコピーします。

```text
runs/<run-id>/workspace/
```

これにより、元のプロジェクトをそのまま維持します。Terraform の状態、`.terraform`、キャッシュされたプラン、実行ディレクトリはコピー対象から除外されます。

<a id="5-terraform-plan-loading"></a>
### 5. Terraform プランの読み込み

関連ファイル：

```text
src/nullstate/terraform.py
```

ライブモードでは、Terraform の処理は自動化に適したコマンドに従います。

```text
terraform init -input=false
terraform plan -out=tfplan -input=false
terraform show -json tfplan
```

オフラインモードでは、CLI は対応するデモ用フィクスチャに対して静的な Terraform パーサーを使います。これにより、外部の実行時依存関係がなくても、テストとデモの再現性を維持します。

Terraform コマンドの結果は次の場所に書き込まれます。

```text
runs/<run-id>/events.jsonl
```

<a id="6-finding-detection"></a>
### 6. 検出結果の識別

関連ファイル：

```text
src/nullstate/findings.py
```

決定論的な検出器は、対応している危険な設定を識別します。例：

- Azure Blob コンテナーに `container_access_type = "blob"` または `"container"` が設定されている
- Azure ストレージアカウントが入れ子の公開項目を許可している
- AWS S3 のパブリックアクセスブロックの制御が無効になっている

検出結果は構造化 JSON として書き込まれます。

```text
runs/<run-id>/findings.json
```

この決定論的な検出結果データが、その後の実行で正とする情報源です。

<a id="7-red-team-model-reasoning"></a>
### 7. レッドチームモデルの推論

関連ファイル：

```text
src/nullstate/agents.py
```

レッドエージェントは内部指示とシナリオの証拠を受け取ります。ユーザーが実行中にモデルへ手動でプロンプトを送ることはありません。

レッドモデルは攻撃に関する推論を返します。例：

- S3 オブジェクトを匿名で読み取る経路
- Azure Blob コンテナーを匿名で読み取る経路
- 収集すべきと考えられる証拠

エンドポイントが設定されていない場合、そのロールは決定論的なモック出力にフォールバックします。

<a id="8-constrained-attack-script-execution"></a>
### 8. 制約付き攻撃スクリプトの実行

関連ファイル：

```text
src/nullstate/attack.py
src/nullstate/attack_runner.py
```

`nullstate` は生成された攻撃成果物を書き込みます。

```text
runs/<run-id>/attack.py
runs/<run-id>/attack-manifest.json
```

マニフェストはシナリオ、バックエンド、対象 URL、リソースのヒントを記録します。これらはシナリオのプローブで利用でき、モデルに任意のコマンドを組み立てる権限を与えません。`docs/schemas/attack-manifest.schema.json` への `$schema` ポインターを含み、`nullstate run` は制約付きプローブの実行前にマニフェストを検証します。

その後、制約付きランナーはその生成済みスクリプトだけを実行します。次の境界を強制します。

- スクリプト名は正確に `attack.py` でなければならない
- スクリプトは現在の実行ディレクトリ直下になければならない
- 実行には現在の Python インタープリターを使う
- 任意のシェルコマンドは受け付けない
- 動的入力は `--target-url`、`--stage`、実行ディレクトリで生成された `attack-manifest.json` に限定する

ランナーは修復の前後でコマンドの証拠を記録します。

```json
{
  "phase": "red-tool",
  "message": "Allowlisted attack command completed",
  "data": {
    "command": ["python", "attack.py", "--target-url", "...", "--stage", "before", "--manifest", "..."],
    "target_url": "...",
    "stage": "before",
    "returncode": 0,
    "stdout": "...",
    "stderr": "",
    "started_at": "...",
    "ended_at": "...",
    "duration_seconds": 0.123
  }
}
```

これにより、レッドエージェントに無制限のツールアクセスを与えずに、実際のコマンドの証拠をレポートに提供できます。

この層のエンタープライズ向けガードレール：

- コマンドポリシーはシナリオテンプレートに基づきます。モデルは攻撃経路について推論できますが、任意のシェルコマンドは選べません。
- `nullstate policy init` はスキーマを参照するポリシーファイルを作成し、書き込み前に検証します。`policy init --scenario <name>` は一つのシナリオ/バックエンドの組み合わせに限定したプリセットを作成します。`run --policy-file` は実行前に、許可されるシナリオ、バックエンド、段階、生成された `attack.py` のフラグ、対象分類、対象ホストの許可リスト、コマンドポリシー ID、タイムアウト上限、出力サイズ上限を強制します。
- `nullstate policy validate` はシナリオを実行せずにポリシーファイルを確認し、CI の証拠として `policy-validation.json` を書き込めます。
- `--allow-live-cloud` が明示的に指定され記録されない限り、実行対象はローカルサンドボックスのエンドポイントのままです。
- `red-tool` イベントにはコマンドスキーマのバージョンと、生成された `attack.py` およびマニフェストの再現性ハッシュが含まれます。
- プローブの標準出力と標準エラーは、アップロード、チケットへの添付、証拠の長期保存の前にサイズを制限する必要があります。
- レポートでは、観測された実行時の証拠、決定論的なシミュレーション、エミュレーター上で結論が出ないプローブを区別しなければなりません。

<a id="9-deterministic-remediation"></a>
### 9. 決定論的な修復

関連ファイル：

```text
src/nullstate/remediation.py
```

ブルーモデルは修復を説明しますが、パッチそのものは決定論的な修復ロジックが生成します。

Azure Blob の公開に対しては、修復で次を設定します。

```hcl
allow_nested_items_to_be_public = false
container_access_type           = "private"
```

AWS S3 の公開に対しては、修復でパブリックアクセスブロックの制御を `true` に設定します。

```hcl
block_public_acls       = true
block_public_policy     = true
ignore_public_acls      = true
restrict_public_buckets = true
```

差分は次の場所に書き込まれます。

```text
runs/<run-id>/remediation.patch
```

<a id="10-re-plan-and-validation"></a>
### 10. 再プランと検証

修復後、CLI は修復済みワークスペースを再度読み込みます。ライブモードでは、コピー先のワークスペースに対して Terraform のプラン/適用の手順を実行します。オフラインモードでは、更新されたファイルを再解析します。

検出器が再度実行されます。検出結果がなくなっていれば、決定論的な攻撃シミュレーションは次を返します。

```text
Red after: blocked
```

制約付き攻撃スクリプトも、次を指定して二度目の実行を行います。

```text
--stage after
```

その修復後のコマンド出力は、別の `red-tool` イベントとして記録されます。

<a id="11-report-and-metrics"></a>
### 11. レポートとメトリクス

関連ファイル：

```text
src/nullstate/report.py
src/nullstate/metrics.py
```

各実行で次を書き込みます。

| 成果物 | 用途 |
|---|---|
| `events.jsonl` | イベントの完全な時系列 |
| `findings.json` | 構造化された脆弱性検出結果 |
| `attack.py` | 生成された制約付き攻撃成果物 |
| `attack-manifest.json` | 制約付きプローブ用の、スキーマ検証済みのシナリオ、バックエンド、対象 URL、リソースのヒント |
| `remediation.patch` | Terraform の修復差分 |
| `remediation.json` | スキーマ検証済みの決定論的な修復ルールセットのメタデータ |
| `metrics.json` | モデル呼び出し、トークン数、レイテンシー、エンドポイントメトリクス |
| `ci-summary.json` | `--ci` 使用時の、スキーマ検証済みで機械可読な CI 判定 |
| `policy-result.json` | 既存の実行に対する独立した JSON ポリシー判断 |
| `report.md` | 人が読める要約 |
| `evidence-manifest.json` | `nullstate evidence-manifest` 使用時の、共有可能な実行証拠の SHA-256 一覧 |
| `evidence-verification.json` | `nullstate evidence-verify` 使用時のマニフェスト検証結果 |
| `upload-plan.json` | `nullstate upload --dry-run` 使用時の、通信を行わないアップロード計画 |
| `workspace/` | コピーされ修復された IaC ワークスペース |

`nullstate report` は既定で最新のレポートを開きます。名前付き実行ディレクトリの配下に入れ子になったレポートも対象です。

`remediation.json` は `docs/schemas/remediation-metadata.schema.json` への `$schema` ポインターを含み、生成された修復メタデータは、レポート、バンドル、実行成果物で使用される前に検証されます。

`nullstate bundle` は `run-bundle.json` を書き込みます。これはローカルダッシュボード、CI アップロード、サポートバンドル、将来の Nullstate Cloud への取り込みに使う、移植可能な証拠の契約です。バンドルは `docs/schemas/run-bundle.schema.json` への `$schema` ポインターを含み、CLI は書き込み前にバンドルの構造を検証します。利用可能な場合は `remediation.json` のメタデータも含むため、後続のツールは修復ルールセットのバージョンとルール ID を表示できます。

`nullstate dashboard` は `dashboard.html` を書き込みます。これはクラウドへのログインなしで開ける、無料の単一実行用ローカルダッシュボードです。検出結果、修復メタデータ、バンドルスキーマのメタデータ、成果物一覧、証拠の時系列、レポートの抜粋をまとめます。

`nullstate sarif` は `nullstate.sarif` を書き込みます。これは CI やコードスキャンへのアップロード用の SARIF 2.1.0 エクスポートで、検出結果ごとに一つの結果を含みます。

`nullstate run --ci` は `ci-summary.json` を書き込み、実行の元の検出結果が `--fail-on-severity` 以上の場合にコード `2` で終了します。要約は `docs/schemas/ci-summary.schema.json` への `$schema` ポインターを含み、書き込み前に検証されるため、人向けレポートを変えずに CI に安定したポリシーゲートを提供します。

`nullstate baseline` は検出結果の識別情報を JSON ベースラインとして書き込みます。`nullstate run --ci --baseline-file` を使用すると、既知のベースラインの検出結果は引き続き表示されますが、CI の失敗しきい値は新しい検出結果だけを対象に評価されます。

`nullstate policy-result` はシナリオを再実行せず、既存の実行に対して同じ形式のしきい値とベースラインの判断を書き込みます。

`nullstate evidence-manifest` は `evidence-manifest.json` を書き込みます。これは共有可能な実行成果物の決定論的な完全性一覧です。マニフェストは `docs/schemas/evidence-manifest.schema.json` への `$schema` ポインターを含み、CLI は書き込み前に構造を検証します。コピーされたワークスペース、Terraform 内部ファイル、Python キャッシュ、マニフェストファイル自身、検証出力は除外されます。`--signing-key-env` を使うと、環境変数の秘密情報から共有鍵 HMAC-SHA256 の証拠署名を付加できます。これは実行証拠への署名であり、公開鍵によるパッケージの来歴証明ではありません。

`nullstate evidence-verify` は記録された成果物のハッシュとファイルサイズを再計算した後、`evidence-verification.json` を書き込みます。マニフェストに列挙された成果物だけを確認し、無関係な新しいファイルは無視し、`--signing-key-env` が指定されていれば HMAC 署名を検証します。記録された成果物が欠落、変更、別の実行からコピー、または署名不正の場合は、コード `2` で終了します。

`nullstate upload --dry-run` は `upload-plan.json` を書き込み、`run-bundle.json` を更新し、予定されるエンドポイントとトークンの環境変数を記録し、トークンの値を保存せずに存在を確認します。計画は `docs/schemas/upload-plan.schema.json` への `$schema` ポインターを含み、CLI は書き込み前に構造を検証します。また、機密情報除去の事前チェック状態を記録します。未処理の実行は `upload_recommended: false` で警告され、`scrub-report.json` を含む機密情報除去済みのコピーは、将来の取り込み経路に向けてアップロード準備済みとマークされます。

`nullstate scrub` は `scrubbed-runs/` 配下に実行の機密情報除去済みコピーを作成し、`scrub-report.json` を書き込みます。元の実行は変更せず、既存の機密情報除去済みコピーの上書きは拒否します。

<a id="security-boundaries"></a>
## セキュリティ境界

重要な境界は次のとおりです。

- 既定では実際のクラウドを対象にしません。
- Terraform の変更はコピーされたワークスペースで行います。
- レッドモデルにシェルアクセスを与えません。
- 攻撃ランナーは実行ディレクトリで生成された `attack.py` だけを実行します。
- 秘密情報は環境変数または無視対象のローカル env ファイルから読み込みます。
- 実行成果物は公開前にレビューしなければなりません。
- 公開ケーススタディの発表、CI アップロード、サポートバンドルの共有の前に、`nullstate scrub` を実行すべきです。
- ローカルでないクラウドエンドポイントを対象にする前には、必ず `--allow-live-cloud` が必要です。

<a id="extension-points"></a>
## 拡張ポイント

<a id="new-scenario"></a>
### 新しいシナリオ

追加または更新します。

```text
src/nullstate/scenarios.py
src/nullstate/scenario_detection.py
src/nullstate/findings.py
src/nullstate/remediation.py
src/nullstate/attack.py
examples/<scenario-name>/
tests/
```

<a id="new-sandbox-backend"></a>
### 新しいサンドボックスバックエンド

次のファイルにバックエンドのメタデータとコマンドを追加します。

```text
src/nullstate/sandbox.py
```

その後、次のテストを追加します。

- `sandbox list`
- `sandbox status`
- `sandbox up --dry-run`
- `sandbox down`

<a id="richer-red-tooling"></a>
### レッドチームツールの充実

次の安全な拡張は、自由形式のシェルアクセスではありません。シナリオごとの許可リストにするべきです。

- 生成された Python プローブ
- 固定のコマンドテンプレート
- ローカル限定の対象 URL
- 厳格なタイムアウト
- 完全なイベント記録
- 実際のクラウド認証情報を継承しない

実行時プローブをチームや企業向けの証拠として位置付ける前に完了すべき制御チェックリストは、[エンタープライズ対応の準備](enterprise-readiness.md)を参照してください。

<a id="test-coverage"></a>
## テストカバレッジ

主要な検証コマンド：

```powershell
python -m unittest discover -s tests -v
python -m ruff check src tests
python -m mypy src
```

有用なスモークテスト：

```powershell
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --runs-dir runs/red-tool-smoke
python -m nullstate report --runs-dir runs/red-tool-smoke
```

スモーク実行では次が表示されるはずです。

- 修復前に一つの検出結果
- `Red before: success`
- `Red after: blocked`
- `events.jsonl` に二つの `red-tool` イベント
