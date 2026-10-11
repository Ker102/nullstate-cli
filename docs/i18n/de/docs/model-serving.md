<a id="model-serving-runbook"></a>
# Modellbereitstellung

Das Projekt verwendet OpenAI-kompatible Endpunkte für lokales vLLM/SGLang, Managed-Provider-Presets oder eigene Proxies.

Für selbst gehostete AMD-GPU-Endpunkte `NULLSTATE_LLM_PROVIDER=custom` verwenden. Für Managed-Gemini-Fallback ohne vom Nutzer verlangte Basis-URL Google-AI-Studio-Key und `NULLSTATE_LLM_PROVIDER=google` nutzen. `NULLSTATE_LLM_PROVIDER=claude` ist nur experimentelle Anthropic/OpenAI-Kompatibilität; vor Claude-spezifischen Produktionsfunktionen einen nativen Adapter hinzufügen.

<a id="recommended-mi300x-split"></a>
## Empfohlene MI300X-Aufteilung

Zwei Container für unabhängige Red-/Blue-Tests verwenden:

| Rolle | Serving-Stack | Erstes Modell | Grund |
|---|---|---|---|
| Rot | vLLM-ROCm-Fallback | `Qwen/Qwen3-4B-Instruct-2507` | Dieses Modell startete bereits erfolgreich mit vLLM auf dem MI300X-Droplet und liefert einen stabilen Endpunkt. |
| Rot experimentell | SGLang ROCm | `Qwen/Qwen3.5-9B` oder `Qwen/Qwen3.5-35B-A3B` | Erweiterungsziel; aktuelles SGLang-Image importiert inkompatible `aiter`-Module. |
| Blau | vLLM ROCm | zuerst `google/gemma-4-E4B-it`, dann `google/gemma-4-26B-A4B-it` oder `google/gemma-4-31B-it` | Gemma 4 benötigt aktuelles vLLM-ROCm-Image; klein starten, dann skalieren. |

Auf einem einzelnen 1x-MI300X-Droplet nicht mit Nemotron 3 Super starten. Öffentliche BF16-/FP8-Modellkarten nennen wesentlich höhere Anforderungen. Als künftiges Multi-GPU-Ziel oder Managed-Endpunkt-Vergleich in der Fallstudie behalten.

<a id="start-stable-red-qwen-endpoint"></a>
## Stabilen roten Qwen-Endpunkt starten

Zuerst vLLM verwenden. Dieser Pfad vermeidet den auf DigitalOcean ROCm beobachteten SGLang-/Quark-/AITER-Importfehler.

```bash
MODEL_ID=Qwen/Qwen3-4B-Instruct-2507 \
SERVED_MODEL_NAME=nullstate-qwen3-4b \
HOST_PORT=8001 \
GPU_MEMORY_UTILIZATION=0.40 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen-vllm-rocm.sh
```

<a id="start-experimental-red-qwen35-sglang-endpoint"></a>
## Experimentellen roten Qwen3.5-SGLang-Endpunkt starten

Auf dem Droplet ausführen:

```bash
cd /opt/nullstate

MODEL_ID=Qwen/Qwen3.5-9B \
SERVED_MODEL_NAME=nullstate-qwen35-9b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

Qwen-SGLang setzt standardmäßig `SGLANG_USE_AITER=0`. Auf DigitalOcean ROCm kann der Container beim Start mit `ImportError: aiter is required when SGLANG_USE_AITER is set to True` enden; der Smoke-Test priorisiert stabilen Start vor AITER-Kernels. SGLang liest Ganzzahlen: `0` oder `1`, nicht `false` oder `true`. Erst nach bestätigtem passendem `aiter`-Build wieder aktivieren:

```bash
SGLANG_USE_AITER=1 \
MODEL_ID=Qwen/Qwen3.5-9B \
SERVED_MODEL_NAME=nullstate-qwen35-9b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

Nach erstem Smoke-Test ein stärkeres rotes Modell verwenden:

```bash
MODEL_ID=Qwen/Qwen3.5-35B-A3B \
SERVED_MODEL_NAME=nullstate-qwen35-35b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

<a id="start-blue-gemma-4-endpoint"></a>
## Blauen Gemma-4-Endpunkt starten

Auf dem Droplet ausführen:

```bash
MODEL_ID=google/gemma-4-E4B-it \
SERVED_MODEL_NAME=nullstate-gemma4-e4b \
HOST_PORT=8002 \
bash /path/to/nullstate-cli/scripts/droplet/serve-gemma4-vllm-rocm.sh
```

Nach stabilem E4B größere Blue-Analysen durchführen:

```bash
MODEL_ID=google/gemma-4-26B-A4B-it \
SERVED_MODEL_NAME=nullstate-gemma4-26b-a4b \
HOST_PORT=8002 \
MAX_MODEL_LEN=32768 \
bash /path/to/nullstate-cli/scripts/droplet/serve-gemma4-vllm-rocm.sh
```

<a id="tunnel-to-local-windows"></a>
## Tunnel zum lokalen Windows

Aus Windows PowerShell:

```powershell
ssh -i "$env:USERPROFILE\Documents\AMDhackkey" -N `
  -L 8001:127.0.0.1:8001 `
  -L 8002:127.0.0.1:8002 `
  root@<droplet-ip>
```

Dann nullstate lokal konfigurieren:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
python -m nullstate run examples/aws-public-s3 --target localstack-aws --scenario aws-public-s3 --red-model nullstate-qwen3-4b --blue-model nullstate-gemma4-e4b
```

`--offline` nur für statisches IaC ohne Terraform apply; `--mock-agents` nur für keinerlei Modellaufrufe.

Managed-Fallback-Beispiel:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
python -m nullstate run examples/aws-public-s3 --offline --red-model gemini-3.5-flash --blue-model gemini-3.5-flash
```

<a id="evidence-collection"></a>
## Evidenzsammlung

Auf dem Droplet:

```bash
bash /path/to/nullstate-cli/scripts/droplet/collect-endpoint-evidence.sh http://127.0.0.1:8001 nullstate-qwen3-4b
bash /path/to/nullstate-cli/scripts/droplet/collect-endpoint-evidence.sh http://127.0.0.1:8002 nullstate-gemma4-e4b
```

Generiertes Evidenzverzeichnis und nullstate-Artefakte behalten:

- `models.json`
- `metrics.prom`
- `chat-completion.json`
- `host-snapshot.txt`
- `runs/<id>/metrics.json`
- `runs/<id>/vllm-metrics-red-*.prom`
- `runs/<id>/vllm-metrics-blue-*.prom`
