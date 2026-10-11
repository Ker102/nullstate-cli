<a id="model-serving-runbook"></a>
# モデル提供運用手順

OpenAI 互換エンドポイントを使い、ローカル vLLM/SGLang、管理プロバイダープリセット、カスタムプロキシに接続します。

自前 AMD GPU には `NULLSTATE_LLM_PROVIDER=custom`。利用者にベース URL を求めず管理 Gemini へフォールバックする場合、Google AI Studio キーと `NULLSTATE_LLM_PROVIDER=google` を使います。`NULLSTATE_LLM_PROVIDER=claude` は実験的 Anthropic/OpenAI 互換経路に限り、Claude 固有の本番機能へ依存する前にネイティブアダプターを追加します。

<a id="recommended-mi300x-split"></a>
## 推奨 MI300X 分割

レッド/ブルーを個別に試す場合、二つのコンテナを使います。

| ロール | 提供基盤 | 最初のモデル | 理由 |
|---|---|---|---|
| レッド | vLLM ROCm 代替 | `Qwen/Qwen3-4B-Instruct-2507` | MI300X droplet で vLLM 起動成功済みで、安定したエンドポイントを提供。 |
| 実験レッド | SGLang ROCm | `Qwen/Qwen3.5-9B` または `Qwen/Qwen3.5-35B-A3B` | 拡張目標として保持。現行 SGLang イメージは不適合 `aiter` をインポート。 |
| ブルー | vLLM ROCm | 最初に `google/gemma-4-E4B-it`、次に `google/gemma-4-26B-A4B-it` または `google/gemma-4-31B-it` | Gemma 4 には新しい vLLM ROCm イメージが必要。小さく開始し拡張。 |

単一 1x MI300X droplet で Nemotron 3 Super から始めないでください。公開 BF16/FP8 モデルカードの必要ハードウェアは単一 MI300X より大幅に大きいため、将来の複数 GPU 対象や管理エンドポイント比較として残します。

<a id="start-stable-red-qwen-endpoint"></a>
## 安定レッド Qwen を起動

この vLLM 経路を先に使います。DigitalOcean ROCm で観測された SGLang/Quark/AITER インポート失敗を避けます。

```bash
MODEL_ID=Qwen/Qwen3-4B-Instruct-2507 \
SERVED_MODEL_NAME=nullstate-qwen3-4b \
HOST_PORT=8001 \
GPU_MEMORY_UTILIZATION=0.40 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen-vllm-rocm.sh
```

<a id="start-experimental-red-qwen35-sglang-endpoint"></a>
## 実験レッド Qwen3.5 SGLang を起動

droplet で実行：

```bash
cd /opt/nullstate

MODEL_ID=Qwen/Qwen3.5-9B \
SERVED_MODEL_NAME=nullstate-qwen35-9b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

Qwen SGLang スクリプトの既定は `SGLANG_USE_AITER=0`。DigitalOcean ROCm では `ImportError: aiter is required when SGLANG_USE_AITER is set to True` で起動終了する場合があります。スモークテストは AITER 専用カーネルより安定起動を優先します。整数として解析するため `0` または `1` を使い、`false`、`true` は使いません。対応 `aiter` ビルドを確認してから再有効化します。

```bash
SGLANG_USE_AITER=1 \
MODEL_ID=Qwen/Qwen3.5-9B \
SERVED_MODEL_NAME=nullstate-qwen35-9b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

最初のスモークテスト後により強いレッドモデルを使うには：

```bash
MODEL_ID=Qwen/Qwen3.5-35B-A3B \
SERVED_MODEL_NAME=nullstate-qwen35-35b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

<a id="start-blue-gemma-4-endpoint"></a>
## ブルー Gemma 4 を起動

droplet で実行：

```bash
MODEL_ID=google/gemma-4-E4B-it \
SERVED_MODEL_NAME=nullstate-gemma4-e4b \
HOST_PORT=8002 \
bash /path/to/nullstate-cli/scripts/droplet/serve-gemma4-vllm-rocm.sh
```

E4B 安定後、より大きなブルーチーム分析を行うには：

```bash
MODEL_ID=google/gemma-4-26B-A4B-it \
SERVED_MODEL_NAME=nullstate-gemma4-26b-a4b \
HOST_PORT=8002 \
MAX_MODEL_LEN=32768 \
bash /path/to/nullstate-cli/scripts/droplet/serve-gemma4-vllm-rocm.sh
```

<a id="tunnel-to-local-windows"></a>
## ローカル Windows へトンネル

Windows PowerShell から：

```powershell
ssh -i "$env:USERPROFILE\Documents\AMDhackkey" -N `
  -L 8001:127.0.0.1:8001 `
  -L 8002:127.0.0.1:8002 `
  root@<droplet-ip>
```

次にローカルで nullstate を設定：

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
python -m nullstate run examples/aws-public-s3 --target localstack-aws --scenario aws-public-s3 --red-model nullstate-qwen3-4b --blue-model nullstate-gemma4-e4b
```

Terraform apply なしの静的 IaC 解析には `--offline`、モデル呼び出しなしには `--mock-agents` を使います。

管理サービス代替例：

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
python -m nullstate run examples/aws-public-s3 --offline --red-model gemini-3.5-flash --blue-model gemini-3.5-flash
```

<a id="evidence-collection"></a>
## 証拠収集

droplet 上で：

```bash
bash /path/to/nullstate-cli/scripts/droplet/collect-endpoint-evidence.sh http://127.0.0.1:8001 nullstate-qwen3-4b
bash /path/to/nullstate-cli/scripts/droplet/collect-endpoint-evidence.sh http://127.0.0.1:8002 nullstate-gemma4-e4b
```

生成証拠ディレクトリと nullstate 実行成果物を保持します。

- `models.json`
- `metrics.prom`
- `chat-completion.json`
- `host-snapshot.txt`
- `runs/<id>/metrics.json`
- `runs/<id>/vllm-metrics-red-*.prom`
- `runs/<id>/vllm-metrics-blue-*.prom`
