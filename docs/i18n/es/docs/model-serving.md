<a id="model-serving-runbook"></a>
# Guía operativa de servicio de modelos

El proyecto usa endpoints compatibles con OpenAI para que la CLI funcione con vLLM/SGLang local, presets de proveedores administrados o proxies personalizados.

Use `NULLSTATE_LLM_PROVIDER=custom` para endpoints AMD GPU autoalojados. Use `NULLSTATE_LLM_PROVIDER=google` con clave Google AI Studio cuando necesite fallback Gemini administrado sin pedir URL base al usuario. Use `NULLSTATE_LLM_PROVIDER=claude` solo como vía experimental de compatibilidad Anthropic/OpenAI; añada adaptador nativo antes de depender de funciones Claude de producción.

<a id="recommended-mi300x-split"></a>
## Distribución MI300X recomendada

Use dos contenedores al probar independientemente los roles rojo y azul:

| Rol | Stack de servicio | Primer modelo | Motivo |
|---|---|---|---|
| Rojo | fallback vLLM ROCm | `Qwen/Qwen3-4B-Instruct-2507` | Este modelo ya arrancó correctamente en el droplet MI300X con vLLM y proporciona un endpoint rojo estable. |
| Rojo experimental | SGLang ROCm | `Qwen/Qwen3.5-9B` o `Qwen/Qwen3.5-35B-A3B` | Vía ampliada opcional; la imagen SGLang actual importa módulos `aiter` incompatibles en el droplet. |
| Azul | vLLM ROCm | primero `google/gemma-4-E4B-it`, después `google/gemma-4-26B-A4B-it` o `google/gemma-4-31B-it` | Gemma 4 requiere una imagen vLLM ROCm actual; empiece pequeño y escale. |

No empiece con Nemotron 3 Super en el droplet de una sola GPU 1x MI300X. Las fichas públicas BF16/FP8 indican requisitos muy superiores a una MI300X. Consérvelo en el caso de estudio como futuro objetivo multi-GPU o comparación de endpoint administrado.

<a id="start-stable-red-qwen-endpoint"></a>
## Iniciar endpoint rojo Qwen estable

Use primero esta vía vLLM. Evita el fallo de importación SGLang/Quark/AITER observado en la imagen DigitalOcean ROCm.

```bash
MODEL_ID=Qwen/Qwen3-4B-Instruct-2507 \
SERVED_MODEL_NAME=nullstate-qwen3-4b \
HOST_PORT=8001 \
GPU_MEMORY_UTILIZATION=0.40 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen-vllm-rocm.sh
```

<a id="start-experimental-red-qwen35-sglang-endpoint"></a>
## Iniciar endpoint rojo experimental Qwen3.5 SGLang

Ejecute en el droplet:

```bash
cd /opt/nullstate

MODEL_ID=Qwen/Qwen3.5-9B \
SERVED_MODEL_NAME=nullstate-qwen35-9b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

El script Qwen SGLang establece `SGLANG_USE_AITER=0` por defecto. En DigitalOcean ROCm, el contenedor puede terminar al iniciar con `ImportError: aiter is required when SGLANG_USE_AITER is set to True`; la prueba básica prioriza arranque estable frente a kernels AITER. SGLang interpreta el valor como entero: use `0` o `1`, no `false` o `true`. Reactive solo tras confirmar una compilación `aiter` compatible en la imagen:

```bash
SGLANG_USE_AITER=1 \
MODEL_ID=Qwen/Qwen3.5-9B \
SERVED_MODEL_NAME=nullstate-qwen35-9b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

Para un modelo rojo más potente tras la primera prueba básica:

```bash
MODEL_ID=Qwen/Qwen3.5-35B-A3B \
SERVED_MODEL_NAME=nullstate-qwen35-35b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

<a id="start-blue-gemma-4-endpoint"></a>
## Iniciar endpoint azul Gemma 4

Ejecute en el droplet:

```bash
MODEL_ID=google/gemma-4-E4B-it \
SERVED_MODEL_NAME=nullstate-gemma4-e4b \
HOST_PORT=8002 \
bash /path/to/nullstate-cli/scripts/droplet/serve-gemma4-vllm-rocm.sh
```

Para análisis azul más amplio después de estabilizar E4B:

```bash
MODEL_ID=google/gemma-4-26B-A4B-it \
SERVED_MODEL_NAME=nullstate-gemma4-26b-a4b \
HOST_PORT=8002 \
MAX_MODEL_LEN=32768 \
bash /path/to/nullstate-cli/scripts/droplet/serve-gemma4-vllm-rocm.sh
```

<a id="tunnel-to-local-windows"></a>
## Túnel hacia Windows local

Desde Windows PowerShell:

```powershell
ssh -i "$env:USERPROFILE\Documents\AMDhackkey" -N `
  -L 8001:127.0.0.1:8001 `
  -L 8002:127.0.0.1:8002 `
  root@<droplet-ip>
```

Después configure nullstate localmente:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
python -m nullstate run examples/aws-public-s3 --target localstack-aws --scenario aws-public-s3 --red-model nullstate-qwen3-4b --blue-model nullstate-gemma4-e4b
```

Use `--offline` solo para análisis estático IaC sin Terraform apply. Use `--mock-agents` solo si no quiere llamadas a modelos.

Ejemplo de fallback administrado:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
python -m nullstate run examples/aws-public-s3 --offline --red-model gemini-3.5-flash --blue-model gemini-3.5-flash
```

<a id="evidence-collection"></a>
## Recopilación de evidencias

En el droplet:

```bash
bash /path/to/nullstate-cli/scripts/droplet/collect-endpoint-evidence.sh http://127.0.0.1:8001 nullstate-qwen3-4b
bash /path/to/nullstate-cli/scripts/droplet/collect-endpoint-evidence.sh http://127.0.0.1:8002 nullstate-gemma4-e4b
```

Conserve el directorio de evidencias generado y los artefactos nullstate:

- `models.json`
- `metrics.prom`
- `chat-completion.json`
- `host-snapshot.txt`
- `runs/<id>/metrics.json`
- `runs/<id>/vllm-metrics-red-*.prom`
- `runs/<id>/vllm-metrics-blue-*.prom`
