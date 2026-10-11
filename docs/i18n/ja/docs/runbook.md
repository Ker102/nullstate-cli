<a id="runbook"></a>
# 運用手順

<a id="local-offline-demo"></a>
## ローカルオフラインデモ

```powershell
python -m pip install -e .
python -m nullstate doctor --offline
python -m nullstate status
python -m nullstate run examples/azure-public-blob --offline
python -m nullstate report
```

録画前に全オフラインシナリオを実行：

```powershell
python -m nullstate run examples/aws-public-s3 --offline
python -m nullstate run examples/k8s-privileged-pod --offline
python -m nullstate run examples/compose-exposed-admin --offline
python -m nullstate run examples/onprem-ssh-password --offline
python -m nullstate run examples/generic-plan-review --offline
```

`run` は `--scenario auto` と `--target auto` が既定。特定アダプター録画では `--scenario`、`--target` を明示します。

<a id="sandbox-discovery"></a>
## サンドボックス探索

```powershell
python -m nullstate status
python -m nullstate sandbox list
python -m nullstate sandbox status localstack-azure
python -m nullstate sandbox up localstack-azure --dry-run
```

多くの操作は `Next` を表示します。設定、到達性、最新報告不明時は `python -m nullstate status`。

<a id="localstack-azure-setup"></a>
## LocalStack Azure 設定

設定：

```powershell
$env:LOCALSTACK_AUTH_TOKEN = "<token>"
```

次に：

```powershell
python -m nullstate sandbox up localstack-azure
python -m nullstate sandbox status localstack-azure
```

`sandbox up localstack-azure` で停止報告時は確認：

```powershell
docker logs localstack-azure
```

Azure Emulator 未有効なら停止し利用権を解決してから再試行。大きなイメージの反復はディスクを消費します。

ローカル env は未追跡に。`.env.local`、`.env` の順で探索：

```powershell
python -m nullstate sandbox up localstack-azure
python -m nullstate sandbox up localstack-aws
```

別の場所だけ `--env-file`：

```powershell
python -m nullstate sandbox up localstack-aws --env-file .env.local
```

Docker Compose 代替：

```powershell
$env:LOCALSTACK_AUTH_TOKEN = "<token>"
docker compose -f docker-compose.localstack-azure.yml up
```

`${LOCALSTACK_AUTH_TOKEN}` はシェルまたは `docker-compose.localstack-azure.yml` 隣の `.env` から読めます。

```env
LOCALSTACK_AUTH_TOKEN=your-token-here
```

`.env` は Git 除外。トークンは絶対コミットしません。別の場所から明示渡しも可能：

```powershell
docker compose --env-file .env.local -f docker-compose.localstack-azure.yml up
```

サービス内 `env_file:` はコンテナ注入で別物。ここでは起動前に `${LOCALSTACK_AUTH_TOKEN}` を置換する Compose 補間が必要です。

<a id="reports-and-run-lookup"></a>
## 報告と実行検索

既定 `runs/` の最新報告：

```powershell
python -m nullstate report
```

名前付き証拠フォルダーの最新：

```powershell
python -m nullstate report --runs-dir runs/live-aws-model
```

ネストしていても既知 ID を開く：

```powershell
python -m nullstate report 20260509-200601 --runs-dir runs
```

公開/サポート/ケース前にサニタイズコピー：

```powershell
python -m nullstate scrub --runs-dir runs
python -m nullstate scrub 20260509-200601 --runs-dir runs --output-dir scrubbed-runs
```

`scrub` は `scrubbed-runs/` にコピーし原本は不変、既存コピー上書きを拒否。共有前に `scrub-report.json` を確認。

<a id="first-tagged-release-checklist"></a>
## 初回タグ公開確認

最初のタグ前に使用。ハッカソン凍結は 2026-06-18 解除、ただし製品タグ/公開は所有者の明示承認が必要。通常は機能ブランチと保護 PR。

候補 PR の成功を確認：

```powershell
gh pr checks 24
```

リリースを作らず予行：

```powershell
gh workflow run Release --field dry_run=true
gh run list --workflow Release --limit 1
```

wheel の `nullstate` ローカル導入を確認：

```powershell
python scripts/release/install_smoke.py
```

承認マージ/タグ後に公開版確認：

```powershell
gh release view v0.1.0
gh release download v0.1.0 --dir dist
```

来歴と SBOM 証明確認：

```powershell
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli --predicate-type https://spdx.dev/Document/v2.3
```

wheel Sigstore バンドル確認：

```powershell
$wheel = Get-ChildItem dist\nullstate-*.whl | Select-Object -First 1
cosign verify-blob $wheel.FullName --bundle "$($wheel.FullName).sigstore.json" --certificate-identity "https://github.com/Ker102/nullstate-cli/.github/workflows/release.yml@refs/tags/v0.1.0" --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

含まれることを確認：

- wheel とソース配布
- `release-manifest.json`
- `sbom.spdx.json`
- 主成果物に隣接する `.sigstore.json`

<a id="model-endpoint-setup"></a>
## モデル設定

両ロール用の自前 vLLM/SGLang/私設 OpenAI 互換に設定：

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_LLM_BASE_URL = "http://localhost:8000"
$env:NULLSTATE_LLM_API_KEY = "<optional>"
```

通常実行します。

Gemini はプリセットとキー、CLI が互換 URL を補完：

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
python -m nullstate run examples/azure-public-blob --red-model gemini-3.5-flash --blue-model gemini-3.5-flash
```

`claude` は Anthropic OpenAI SDK 互換層：

```powershell
$env:NULLSTATE_LLM_PROVIDER = "claude"
$env:NULLSTATE_LLM_API_KEY = "<anthropic-api-key>"
python -m nullstate run examples/azure-public-blob --red-model claude-sonnet-4-6 --blue-model claude-sonnet-4-6
```

Claude 互換は実験的。専用機能が必要なら無理に包装拡張せずネイティブ Anthropic を追加。

二つのコンテナ/SSH はロール別：

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
$env:NULLSTATE_RED_LLM_API_KEY = "<optional-red-token>"
$env:NULLSTATE_BLUE_LLM_API_KEY = "<optional-blue-token>"
python -m nullstate run examples/azure-public-blob --red-model nullstate-red --blue-model nullstate-blue
```

単発に `--llm-provider`、`--red-provider`、`--blue-provider`、`--red-base-url`、`--blue-base-url`。未設定は `NULLSTATE_LLM_PROVIDER`、`NULLSTATE_LLM_BASE_URL`、`NULLSTATE_LLM_API_KEY`。明示 URL が優先しゲートウェイ/fixture に対応。

ロール URL なしなら決定論的モック。GPU 前でも LocalStack 開発可。モデルは MI300X 証拠とトークン/速度指標用で、決定論的攻撃/修正には不要。

`--offline` は Terraform/クラウドを制御しモデルではありません。設定 URL は呼びつつ静的解析：

```powershell
$env:NULLSTATE_LLM_BASE_URL = "http://127.0.0.1:8001"
python -m nullstate run examples/azure-public-blob --offline --blue-model nullstate-qwen3-4b --red-model nullstate-qwen3-4b
```

モデルなしには `--mock-agents`：

```powershell
python -m nullstate run examples/azure-public-blob --offline --mock-agents
```

<a id="amd-developer-cloud--digitalocean-path"></a>
## AMD Developer Cloud / DigitalOcean

[AMD 計算戦略](compute-strategy.md)に従い GPU なし基盤を先に構築、利用可能時 MI300X を接続。

現行 Qwen3.5/Gemma 4 二コンテナは[モデル提供手順](model-serving.md)。

<a id="fireworks-fallback"></a>
## Fireworks 代替

AMD 待ちなら `NULLSTATE_LLM_BASE_URL` を管理サービスへ。証拠は管理推論と記載し私設 GPU としません。

<a id="metrics-evidence"></a>
## 指標証拠

設定時に取得を試みるもの：

```text
<NULLSTATE_LLM_BASE_URL>/metrics
<NULLSTATE_RED_LLM_BASE_URL>/metrics
<NULLSTATE_BLUE_LLM_BASE_URL>/metrics
```

vLLM Prometheus があれば出力：

- `vllm-metrics-before.prom`
- `vllm-metrics-after.prom`
- ロール別 URL 時の `vllm-metrics-red-before.prom` と関連記録
- `metrics.json` 内解析カウンター

GPU は `amd-smi`、次に `rocm-smi`。両方なければ `metrics.json` に `status: unavailable`、失敗させません。

<a id="work-you-can-do-before-amd-gpu-access"></a>
## AMD 利用前の作業

サポート待ちに準備：

- DigitalOcean プロジェクト/防火壁
- SSH キー/最小権限
- GPU なしスモークテスト droplet
- Docker/更新ポリシー
- GitHub secrets/環境名
- `.env.example` ベースの `.env`
- 処理済み workflow/PR/オフライン画像
- 利用可能なら Azure LocalStack トークン

<a id="artifact-review-before-publishing"></a>
## 公開前確認

確認：

- `runs/<id>/report.md`
- `runs/<id>/findings.json`
- `runs/<id>/events.jsonl`
- `runs/<id>/remediation.json`
- `runs/<id>/metrics.json`
- `runs/<id>/vllm-metrics-before.prom`
- `runs/<id>/vllm-metrics-after.prom`
- `runs/<id>/remediation.patch`

秘密、実テナント/購読 ID、私設 URL、Terraform state は公開禁止。
