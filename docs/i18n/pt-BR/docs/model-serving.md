<a id="model-serving-runbook"></a>
# Manual de serving de modelos

O projeto usa endpoints compatíveis com OpenAI para vLLM/SGLang local, presets gerenciados ou proxy customizado.

Use `NULLSTATE_LLM_PROVIDER=custom` para AMD GPU auto-hospedado. Use `NULLSTATE_LLM_PROVIDER=google` com chave Google AI Studio para fallback Gemini gerenciado sem pedir URL base ao usuário. `NULLSTATE_LLM_PROVIDER=claude` é apenas caminho experimental Anthropic/OpenAI; adicione adaptador nativo antes de depender de funções Claude de produção.

<a id="recommended-mi300x-split"></a>
## Divisão MI300X recomendada

Use dois contêineres para testar vermelho/azul separadamente:

| Papel | Stack | Primeiro modelo | Motivo |
|---|---|---|---|
| Vermelho | fallback vLLM ROCm | `Qwen/Qwen3-4B-Instruct-2507` | Este modelo já iniciou com sucesso no droplet MI300X com vLLM e fornece endpoint estável. |
| Vermelho experimental | SGLang ROCm | `Qwen/Qwen3.5-9B` ou `Qwen/Qwen3.5-35B-A3B` | Mantenha como expansão; a imagem atual importa módulos `aiter` incompatíveis. |
| Azul | vLLM ROCm | primeiro `google/gemma-4-E4B-it`, depois `google/gemma-4-26B-A4B-it` ou `google/gemma-4-31B-it` | Gemma 4 exige imagem vLLM ROCm atual; comece pequeno e escale. |

Não comece com Nemotron 3 Super em droplet único 1x MI300X. Model cards públicos BF16/FP8 exigem hardware muito maior. Mantenha como futuro alvo multi-GPU ou comparação de endpoint gerenciado.

<a id="start-stable-red-qwen-endpoint"></a>
## Iniciar Qwen vermelho estável

Use primeiro vLLM. Evita a falha de importação SGLang/Quark/AITER observada no DigitalOcean ROCm.

```bash
MODEL_ID=Qwen/Qwen3-4B-Instruct-2507 \
SERVED_MODEL_NAME=nullstate-qwen3-4b \
HOST_PORT=8001 \
GPU_MEMORY_UTILIZATION=0.40 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen-vllm-rocm.sh
```

<a id="start-experimental-red-qwen35-sglang-endpoint"></a>
## Iniciar Qwen3.5 SGLang vermelho experimental

Execute no droplet:

```bash
cd /opt/nullstate

MODEL_ID=Qwen/Qwen3.5-9B \
SERVED_MODEL_NAME=nullstate-qwen35-9b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

O script Qwen SGLang define `SGLANG_USE_AITER=0` por padrão. No DigitalOcean ROCm, pode encerrar ao iniciar com `ImportError: aiter is required when SGLANG_USE_AITER is set to True`; o smoke test prioriza inicialização estável, não kernels AITER. SGLang lê inteiro: use `0` ou `1`, não `false` ou `true`. Reative só após confirmar build `aiter` compatível:

```bash
SGLANG_USE_AITER=1 \
MODEL_ID=Qwen/Qwen3.5-9B \
SERVED_MODEL_NAME=nullstate-qwen35-9b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

Para modelo vermelho mais forte após o primeiro smoke test:

```bash
MODEL_ID=Qwen/Qwen3.5-35B-A3B \
SERVED_MODEL_NAME=nullstate-qwen35-35b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

<a id="start-blue-gemma-4-endpoint"></a>
## Iniciar Gemma 4 azul

Execute no droplet:

```bash
MODEL_ID=google/gemma-4-E4B-it \
SERVED_MODEL_NAME=nullstate-gemma4-e4b \
HOST_PORT=8002 \
bash /path/to/nullstate-cli/scripts/droplet/serve-gemma4-vllm-rocm.sh
```

Para análise azul maior após estabilizar E4B:

```bash
MODEL_ID=google/gemma-4-26B-A4B-it \
SERVED_MODEL_NAME=nullstate-gemma4-26b-a4b \
HOST_PORT=8002 \
MAX_MODEL_LEN=32768 \
bash /path/to/nullstate-cli/scripts/droplet/serve-gemma4-vllm-rocm.sh
```

<a id="tunnel-to-local-windows"></a>
## Túnel para Windows local

Do Windows PowerShell:

```powershell
ssh -i "$env:USERPROFILE\Documents\AMDhackkey" -N `
  -L 8001:127.0.0.1:8001 `
  -L 8002:127.0.0.1:8002 `
  root@<droplet-ip>
```

Depois configure nullstate localmente:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
python -m nullstate run examples/aws-public-s3 --target localstack-aws --scenario aws-public-s3 --red-model nullstate-qwen3-4b --blue-model nullstate-gemma4-e4b
```

Use `--offline` para análise estática IaC sem Terraform apply; `--mock-agents` para nenhuma chamada a modelos.

Exemplo de fallback gerenciado:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
python -m nullstate run examples/aws-public-s3 --offline --red-model gemini-3.5-flash --blue-model gemini-3.5-flash
```

<a id="evidence-collection"></a>
## Coleta de evidências

No droplet:

```bash
bash /path/to/nullstate-cli/scripts/droplet/collect-endpoint-evidence.sh http://127.0.0.1:8001 nullstate-qwen3-4b
bash /path/to/nullstate-cli/scripts/droplet/collect-endpoint-evidence.sh http://127.0.0.1:8002 nullstate-gemma4-e4b
```

Guarde o diretório de evidências gerado e os artefatos nullstate:

- `models.json`
- `metrics.prom`
- `chat-completion.json`
- `host-snapshot.txt`
- `runs/<id>/metrics.json`
- `runs/<id>/vllm-metrics-red-*.prom`
- `runs/<id>/vllm-metrics-blue-*.prom`
