<a id="runbook"></a>
# Guía operativa

<a id="local-offline-demo"></a>
## Demo local sin conexión

```powershell
python -m pip install -e .
python -m nullstate doctor --offline
python -m nullstate status
python -m nullstate run examples/azure-public-blob --offline
python -m nullstate report
```

Ejecute todos los escenarios offline antes de grabar:

```powershell
python -m nullstate run examples/aws-public-s3 --offline
python -m nullstate run examples/k8s-privileged-pod --offline
python -m nullstate run examples/compose-exposed-admin --offline
python -m nullstate run examples/onprem-ssh-password --offline
python -m nullstate run examples/generic-plan-review --offline
```

`run` usa `--scenario auto` y `--target auto`. Conserve `--scenario` y `--target` explícitos en demos grabadas de un adaptador concreto.

<a id="sandbox-discovery"></a>
## Descubrimiento de sandboxes

```powershell
python -m nullstate status
python -m nullstate sandbox list
python -m nullstate sandbox status localstack-azure
python -m nullstate sandbox up localstack-azure --dry-run
```

La mayoría de comandos muestra tabla `Next` con siguientes pasos. Use `python -m nullstate status` si desconoce configuración, alcance del sondeo o informe más reciente.

<a id="localstack-azure-setup"></a>
## Configurar LocalStack Azure

Establezca:

```powershell
$env:LOCALSTACK_AUTH_TOKEN = "<token>"
```

Después:

```powershell
python -m nullstate sandbox up localstack-azure
python -m nullstate sandbox status localstack-azure
```

Si `sandbox up localstack-azure` indica que el contenedor no siguió ejecutándose, inspeccione:

```powershell
docker logs localstack-azure
```

Si los logs indican Azure Emulator no habilitado, deténgase y resuelva la habilitación de cuenta antes de reintentar. La imagen grande puede consumir mucho disco con reintentos.

Mantenga sin versionar el archivo env local del token. La CLI descubre primero `.env.local`, después `.env`:

```powershell
python -m nullstate sandbox up localstack-azure
python -m nullstate sandbox up localstack-aws
```

Use `--env-file` solo para otro lugar:

```powershell
python -m nullstate sandbox up localstack-aws --env-file .env.local
```

Alternativa Docker Compose:

```powershell
$env:LOCALSTACK_AUTH_TOKEN = "<token>"
docker compose -f docker-compose.localstack-azure.yml up
```

Compose lee `${LOCALSTACK_AUTH_TOKEN}` desde la shell o `.env` local junto a `docker-compose.localstack-azure.yml`:

```env
LOCALSTACK_AUTH_TOKEN=your-token-here
```

Git ignora `.env`. Nunca incluya el token en commits. También puede guardarlo en otro lugar y pasarlo explícitamente:

```powershell
docker compose --env-file .env.local -f docker-compose.localstack-azure.yml up
```

`env_file:` dentro de un servicio inyecta variables en el contenedor; es distinto. Aquí hace falta interpolación Compose de `${LOCALSTACK_AUTH_TOKEN}` antes de iniciar.

<a id="reports-and-run-lookup"></a>
## Informes y búsqueda de ejecuciones

Abra el informe más reciente de `runs/`:

```powershell
python -m nullstate report
```

Abra el informe más reciente de una carpeta de evidencias nombrada:

```powershell
python -m nullstate report --runs-dir runs/live-aws-model
```

Abra un ID conocido incluso dentro de una carpeta nombrada:

```powershell
python -m nullstate report 20260509-200601 --runs-dir runs
```

Cree copia saneada antes de publicar, adjuntar a soporte o usar en casos públicos:

```powershell
python -m nullstate scrub --runs-dir runs
python -m nullstate scrub 20260509-200601 --runs-dir runs --output-dir scrubbed-runs
```

`scrub` copia bajo `scrubbed-runs/` sin tocar original y rechaza sobrescribir una copia existente. Revise `scrub-report.json` antes de compartir.

<a id="first-tagged-release-checklist"></a>
## Lista para primera versión etiquetada

Use antes de la primera etiqueta. La congelación del hackathon se levantó el 2026-06-18; etiquetas y publicación aún requieren aprobación explícita del propietario. Trabaje en ramas y controles PR protegidos.

Confirme comprobaciones PR del candidato correctas:

```powershell
gh pr checks 24
```

Ensaye sin crear versión GitHub:

```powershell
gh workflow run Release --field dry_run=true
gh run list --workflow Release --limit 1
```

Verifique instalación local del comando `nullstate` desde wheel construido:

```powershell
python scripts/release/install_smoke.py
```

Tras integración y etiquetado aprobados, inspeccione la versión:

```powershell
gh release view v0.1.0
gh release download v0.1.0 --dir dist
```

Verifique procedencia y atestaciones SBOM:

```powershell
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli --predicate-type https://spdx.dev/Document/v2.3
```

Verifique paquete Sigstore del wheel:

```powershell
$wheel = Get-ChildItem dist\nullstate-*.whl | Select-Object -First 1
cosign verify-blob $wheel.FullName --bundle "$($wheel.FullName).sigstore.json" --certificate-identity "https://github.com/Ker102/nullstate-cli/.github/workflows/release.yml@refs/tags/v0.1.0" --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

Confirme recursos:

- wheel y distribución fuente
- `release-manifest.json`
- `sbom.spdx.json`
- paquetes `.sigstore.json` adyacentes a artefactos principales

<a id="model-endpoint-setup"></a>
## Configurar endpoint de modelo

Para vLLM/SGLang autoalojado o proxy privado compatible con OpenAI para ambos roles, establezca:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_LLM_BASE_URL = "http://localhost:8000"
$env:NULLSTATE_LLM_API_KEY = "<optional>"
```

Después ejecute normalmente.

Para Google AI Studio / Gemini establezca preset y API key; la CLI aporta URL base Gemini compatible:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
python -m nullstate run examples/azure-public-blob --red-model gemini-3.5-flash --blue-model gemini-3.5-flash
```

Para Claude, el preset `claude` usa compatibilidad OpenAI SDK de Anthropic:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "claude"
$env:NULLSTATE_LLM_API_KEY = "<anthropic-api-key>"
python -m nullstate run examples/azure-public-blob --red-model claude-sonnet-4-6 --blue-model claude-sonnet-4-6
```

La compatibilidad Claude es experimental. Añada adaptador nativo Anthropic si necesita funciones específicas en el futuro producto.

Para dos contenedores o túneles SSH, use endpoints por rol:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
$env:NULLSTATE_RED_LLM_API_KEY = "<optional-red-token>"
$env:NULLSTATE_BLUE_LLM_API_KEY = "<optional-blue-token>"
python -m nullstate run examples/azure-public-blob --red-model nullstate-red --blue-model nullstate-blue
```

También admite `--llm-provider`, `--red-provider`, `--blue-provider`, `--red-base-url`, `--blue-base-url` por ejecución. Si faltan valores por rol, usa `NULLSTATE_LLM_PROVIDER`, `NULLSTATE_LLM_BASE_URL`, `NULLSTATE_LLM_API_KEY`. URLs explícitas prevalecen sobre presets para gateways y fixtures.

Sin endpoint de un rol, usa respuesta simulada determinista. Puede desarrollar LocalStack antes de tener GPU AMD; el endpoint sirve para evidencia MI300X y métricas de tokens/throughput, no es necesario para explotación/remediación determinista.

`--offline` controla Terraform/nube, no modelos. Con endpoint compartido o por rol, sigue llamándolo y usa análisis estático:

```powershell
$env:NULLSTATE_LLM_BASE_URL = "http://127.0.0.1:8001"
python -m nullstate run examples/azure-public-blob --offline --blue-model nullstate-qwen3-4b --red-model nullstate-qwen3-4b
```

Use `--mock-agents` para no llamar modelos:

```powershell
python -m nullstate run examples/azure-public-blob --offline --mock-agents
```

<a id="amd-developer-cloud--digitalocean-path"></a>
## Vía AMD Developer Cloud / DigitalOcean

Use [Estrategia AMD](compute-strategy.md) como lista de despliegue. Primero cree baseline DigitalOcean sin GPU y luego conecte endpoint MI300X al tener acceso.

Use [Servicio de modelos](model-serving.md) para la configuración actual de dos contenedores Qwen3.5/Gemma 4.

<a id="fireworks-fallback"></a>
## Fallback Fireworks

Si se retrasa GPU AMD, dirija `NULLSTATE_LLM_BASE_URL` al endpoint administrado y mantenga el flujo. Etiquete evidencias como inferencia administrada, no GPU privada.

<a id="metrics-evidence"></a>
## Evidencias métricas

Con endpoint configurado, intenta recopilar:

```text
<NULLSTATE_LLM_BASE_URL>/metrics
<NULLSTATE_RED_LLM_BASE_URL>/metrics
<NULLSTATE_BLUE_LLM_BASE_URL>/metrics
```

Si expone métricas Prometheus vLLM, escribe:

- `vllm-metrics-before.prom`
- `vllm-metrics-after.prom`
- `vllm-metrics-red-before.prom` y capturas por rol si endpoints difieren
- contadores analizados dentro de `metrics.json`

Intenta captura GPU local primero con `amd-smi`, luego `rocm-smi`. Sin herramientas, `metrics.json` registra `status: unavailable` sin fallar.

<a id="work-you-can-do-before-amd-gpu-access"></a>
## Trabajo antes del acceso GPU AMD

Mientras espera soporte, prepare:

- proyecto DigitalOcean y firewall
- claves SSH y acceso mínimo
- droplet sin GPU para pruebas LocalStack/nullstate
- instalación Docker y política de actualización
- nombres de secretos/entornos GitHub
- `.env` local basado en `.env.example`
- capturas saneadas de workflow, PR y demo offline
- token/acceso Azure LocalStack si existe

<a id="artifact-review-before-publishing"></a>
## Revisar artefactos antes de publicar

Compruebe:

- `runs/<id>/report.md`
- `runs/<id>/findings.json`
- `runs/<id>/events.jsonl`
- `runs/<id>/remediation.json`
- `runs/<id>/metrics.json`
- `runs/<id>/vllm-metrics-before.prom`
- `runs/<id>/vllm-metrics-after.prom`
- `runs/<id>/remediation.patch`

No publique secretos, IDs reales de inquilino/suscripción, endpoints privados ni estado Terraform.
