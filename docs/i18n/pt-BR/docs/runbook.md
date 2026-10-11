<a id="runbook"></a>
# Manual de operação

<a id="local-offline-demo"></a>
## Demo local offline

```powershell
python -m pip install -e .
python -m nullstate doctor --offline
python -m nullstate status
python -m nullstate run examples/azure-public-blob --offline
python -m nullstate report
```

Execute todos os cenários antes de gravar:

```powershell
python -m nullstate run examples/aws-public-s3 --offline
python -m nullstate run examples/k8s-privileged-pod --offline
python -m nullstate run examples/compose-exposed-admin --offline
python -m nullstate run examples/onprem-ssh-password --offline
python -m nullstate run examples/generic-plan-review --offline
```

`run` usa `--scenario auto` e `--target auto`. Mantenha `--scenario` e `--target` explícitos para gravar adaptador específico.

<a id="sandbox-discovery"></a>
## Descoberta de sandboxes

```powershell
python -m nullstate status
python -m nullstate sandbox list
python -m nullstate sandbox status localstack-azure
python -m nullstate sandbox up localstack-azure --dry-run
```

A maioria mostra `Next`. Use `python -m nullstate status` para configuração, alcance da sondagem e relatório mais novo.

<a id="localstack-azure-setup"></a>
## Configurar LocalStack Azure

Defina:

```powershell
$env:LOCALSTACK_AUTH_TOKEN = "<token>"
```

Depois:

```powershell
python -m nullstate sandbox up localstack-azure
python -m nullstate sandbox status localstack-azure
```

Se `sandbox up localstack-azure` informar parada do contêiner, inspecione:

```powershell
docker logs localstack-azure
```

Se Azure Emulator não estiver habilitado, pare e resolva acesso antes de tentar. A imagem grande pode consumir disco em repetidas tentativas.

Mantenha env do token não versionado. Descobre `.env.local` primeiro, `.env` depois:

```powershell
python -m nullstate sandbox up localstack-azure
python -m nullstate sandbox up localstack-aws
```

Use `--env-file` só para outro local:

```powershell
python -m nullstate sandbox up localstack-aws --env-file .env.local
```

Alternativa Docker Compose:

```powershell
$env:LOCALSTACK_AUTH_TOKEN = "<token>"
docker compose -f docker-compose.localstack-azure.yml up
```

Compose lê `${LOCALSTACK_AUTH_TOKEN}` do shell ou `.env` ao lado de `docker-compose.localstack-azure.yml`:

```env
LOCALSTACK_AUTH_TOKEN=your-token-here
```

Git ignora `.env`. Nunca commite o token. Pode guardar em outro lugar e passar explicitamente:

```powershell
docker compose --env-file .env.local -f docker-compose.localstack-azure.yml up
```

`env_file:` no serviço injeta variáveis no contêiner; aqui precisa interpolação Compose de `${LOCALSTACK_AUTH_TOKEN}` antes de iniciar.

<a id="reports-and-run-lookup"></a>
## Relatórios e busca

Mais novo em `runs/`:

```powershell
python -m nullstate report
```

Mais novo em pasta de evidências nomeada:

```powershell
python -m nullstate report --runs-dir runs/live-aws-model
```

ID conhecido mesmo em pasta aninhada:

```powershell
python -m nullstate report 20260509-200601 --runs-dir runs
```

Crie cópia sanitizada antes de publicar, suporte ou caso público:

```powershell
python -m nullstate scrub --runs-dir runs
python -m nullstate scrub 20260509-200601 --runs-dir runs --output-dir scrubbed-runs
```

`scrub` copia para `scrubbed-runs/` sem alterar original e recusa sobrescrever cópia existente. Revise `scrub-report.json`.

<a id="first-tagged-release-checklist"></a>
## Primeiro release com tag

Use antes da primeira tag. O congelamento foi levantado em 2026-06-18, mas tags/publicação ainda exigem aprovação explícita do dono. Alterações normais em branches e PR protegido.

Verifique checks do candidato:

```powershell
gh pr checks 24
```

Ensaie sem criar release GitHub:

```powershell
gh workflow run Release --field dry_run=true
gh run list --workflow Release --limit 1
```

Verifique instalação local de `nullstate` pelo wheel:

```powershell
python scripts/release/install_smoke.py
```

Após merge/tag aprovados, inspecione release:

```powershell
gh release view v0.1.0
gh release download v0.1.0 --dir dist
```

Verifique proveniência e SBOM:

```powershell
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli --predicate-type https://spdx.dev/Document/v2.3
```

Verifique pacote Sigstore:

```powershell
$wheel = Get-ChildItem dist\nullstate-*.whl | Select-Object -First 1
cosign verify-blob $wheel.FullName --bundle "$($wheel.FullName).sigstore.json" --certificate-identity "https://github.com/Ker102/nullstate-cli/.github/workflows/release.yml@refs/tags/v0.1.0" --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

Confirme artefatos:

- wheel e distribuição fonte
- `release-manifest.json`
- `sbom.spdx.json`
- pacotes `.sigstore.json` adjacentes aos principais

<a id="model-endpoint-setup"></a>
## Endpoint de modelo

Para vLLM/SGLang ou proxy privado OpenAI servindo ambos os papéis:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_LLM_BASE_URL = "http://localhost:8000"
$env:NULLSTATE_LLM_API_KEY = "<optional>"
```

Execute normalmente depois.

Gemini: preset e key; CLI preenche URL compatível:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
python -m nullstate run examples/azure-public-blob --red-model gemini-3.5-flash --blue-model gemini-3.5-flash
```

`claude` usa camada SDK OpenAI da Anthropic:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "claude"
$env:NULLSTATE_LLM_API_KEY = "<anthropic-api-key>"
python -m nullstate run examples/azure-public-blob --red-model claude-sonnet-4-6 --blue-model claude-sonnet-4-6
```

Compatibilidade experimental. Para recursos próprios Claude, adicione adaptador Anthropic nativo, não force wrapper.

Dois contêineres/túneis: endpoints por papel:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
$env:NULLSTATE_RED_LLM_API_KEY = "<optional-red-token>"
$env:NULLSTATE_BLUE_LLM_API_KEY = "<optional-blue-token>"
python -m nullstate run examples/azure-public-blob --red-model nullstate-red --blue-model nullstate-blue
```

Por execução também `--llm-provider`, `--red-provider`, `--blue-provider`, `--red-base-url`, `--blue-base-url`. Sem valor específico usa `NULLSTATE_LLM_PROVIDER`, `NULLSTATE_LLM_BASE_URL`, `NULLSTATE_LLM_API_KEY`. URL explícita supera preset para gateways/fixtures.

Sem endpoint de papel usa mock determinístico. LocalStack pode ser desenvolvido antes de AMD; modelo serve à evidência MI300X e métricas tokens/throughput, não ao ciclo determinístico.

`--offline` controla Terraform/cloud, não modelos. Endpoint configurado ainda é chamado com análise estática:

```powershell
$env:NULLSTATE_LLM_BASE_URL = "http://127.0.0.1:8001"
python -m nullstate run examples/azure-public-blob --offline --blue-model nullstate-qwen3-4b --red-model nullstate-qwen3-4b
```

Use `--mock-agents` para nenhuma chamada:

```powershell
python -m nullstate run examples/azure-public-blob --offline --mock-agents
```

<a id="amd-developer-cloud--digitalocean-path"></a>
## AMD Developer Cloud / DigitalOcean

Siga [Estratégia AMD](compute-strategy.md). Primeiro baseline sem GPU, depois MI300X quando disponível.

Dois contêineres Qwen3.5/Gemma 4 em [Serving de modelos](model-serving.md).

<a id="fireworks-fallback"></a>
## Fallback Fireworks

Se AMD atrasar, aponte `NULLSTATE_LLM_BASE_URL` ao endpoint gerenciado. Rotule evidência como inferência gerenciada, não GPU privada.

<a id="metrics-evidence"></a>
## Evidências métricas

Com endpoint, tenta coletar:

```text
<NULLSTATE_LLM_BASE_URL>/metrics
<NULLSTATE_RED_LLM_BASE_URL>/metrics
<NULLSTATE_BLUE_LLM_BASE_URL>/metrics
```

Se expõe vLLM Prometheus, grava:

- `vllm-metrics-before.prom`
- `vllm-metrics-after.prom`
- `vllm-metrics-red-before.prom` e snapshots por papel quando endpoints diferem
- contadores analisados em `metrics.json`

GPU local via `amd-smi`, depois `rocm-smi`. Sem ambos, `metrics.json` registra `status: unavailable`, sem falhar.

<a id="work-you-can-do-before-amd-gpu-access"></a>
## Trabalho antes de AMD

Enquanto aguarda suporte, prepare:

- projeto DigitalOcean/firewall
- SSH keys/menor privilégio
- droplet sem GPU para smoke tests
- Docker/política de atualização
- nomes secrets/ambientes GitHub
- `.env` local baseado em `.env.example`
- capturas sanitizadas workflow/PR/demo
- token/acesso Azure LocalStack se disponível

<a id="artifact-review-before-publishing"></a>
## Revisão antes de publicar

Verifique:

- `runs/<id>/report.md`
- `runs/<id>/findings.json`
- `runs/<id>/events.jsonl`
- `runs/<id>/remediation.json`
- `runs/<id>/metrics.json`
- `runs/<id>/vllm-metrics-before.prom`
- `runs/<id>/vllm-metrics-after.prom`
- `runs/<id>/remediation.patch`

Não publique segredos, IDs reais de tenants/assinaturas, endpoints privados ou estado Terraform.
