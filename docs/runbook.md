# Runbook

## Local offline demo

```powershell
python -m pip install -e .
python -m nullstate doctor --offline
python -m nullstate run examples/azure-public-blob --offline
```

Run every offline scenario before recording:

```powershell
python -m nullstate run examples/aws-public-s3 --offline
python -m nullstate run examples/k8s-privileged-pod --offline
python -m nullstate run examples/compose-exposed-admin --offline
python -m nullstate run examples/onprem-ssh-password --offline
python -m nullstate run examples/generic-plan-review --offline
```

`run` defaults to `--scenario auto` and `--target auto`. Keep explicit `--scenario` and `--target` for recorded demos where you want to show a particular adapter path.

## Sandbox discovery

```powershell
python -m nullstate sandbox list
python -m nullstate sandbox status localstack-azure
python -m nullstate sandbox up localstack-azure --dry-run
```

## LocalStack Azure setup

Set:

```powershell
$env:LOCALSTACK_AUTH_TOKEN = "<token>"
```

Then:

```powershell
python -m nullstate sandbox up localstack-azure
```

Docker Compose alternative:

```powershell
$env:LOCALSTACK_AUTH_TOKEN = "<token>"
docker compose -f docker-compose.localstack-azure.yml up
```

Docker Compose can read `${LOCALSTACK_AUTH_TOKEN}` from either the current shell or a local `.env` file next to `docker-compose.localstack-azure.yml`:

```env
LOCALSTACK_AUTH_TOKEN=your-token-here
```

`.env` is ignored by Git. Never commit the token. You can also keep the token somewhere else and pass it explicitly:

```powershell
docker compose --env-file .env.local -f docker-compose.localstack-azure.yml up
```

`env_file:` inside a Compose service is different: it injects variables into a container. For this token, we need Compose interpolation so the compose file can replace `${LOCALSTACK_AUTH_TOKEN}` before starting the service.

## Model endpoint setup

For one model endpoint serving both red and blue roles, set:

```powershell
$env:NULLSTATE_LLM_BASE_URL = "http://localhost:8000"
$env:NULLSTATE_LLM_API_KEY = "<optional>"
```

Then run normally.

For two containers or two SSH tunnels, set role-specific endpoints:

```powershell
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
$env:NULLSTATE_RED_LLM_API_KEY = "<optional-red-token>"
$env:NULLSTATE_BLUE_LLM_API_KEY = "<optional-blue-token>"
python -m nullstate run examples/azure-public-blob --red-model nullstate-red --blue-model nullstate-blue
```

You can also pass `--red-base-url` and `--blue-base-url` for a single run. Role-specific settings fall back to `NULLSTATE_LLM_BASE_URL` and `NULLSTATE_LLM_API_KEY` when they are not set.

If no model endpoint is configured for a role, nullstate falls back to a deterministic mock agent response for that role. That means live LocalStack work can be developed before AMD GPU access; the model endpoint is needed for the MI300X case-study evidence and token/throughput metrics, not for the deterministic exploit/remediation loop.

`--offline` controls Terraform/cloud execution, not model usage. With a shared or role-specific endpoint set, this still calls the configured endpoint while using static IaC parsing:

```powershell
$env:NULLSTATE_LLM_BASE_URL = "http://127.0.0.1:8001"
python -m nullstate run examples/azure-public-blob --offline --blue-model nullstate-qwen3-4b --red-model nullstate-qwen3-4b
```

Use `--mock-agents` when you explicitly want no model calls:

```powershell
python -m nullstate run examples/azure-public-blob --offline --mock-agents
```

## AMD Developer Cloud / DigitalOcean path

Use [AMD Compute Strategy](compute-strategy.md) as the deployment checklist. Build the non-GPU DigitalOcean baseline first, then attach the MI300X-backed model endpoint when access is available.

## Fireworks fallback

If AMD GPU access is delayed, point `NULLSTATE_LLM_BASE_URL` at the managed endpoint and keep the same nullstate run flow. Label the evidence as managed inference, not private GPU-hosted inference.

## Metrics evidence

When a model endpoint is set, nullstate tries to scrape:

```text
<NULLSTATE_LLM_BASE_URL>/metrics
<NULLSTATE_RED_LLM_BASE_URL>/metrics
<NULLSTATE_BLUE_LLM_BASE_URL>/metrics
```

If the endpoint exposes vLLM Prometheus metrics, the run writes:

- `vllm-metrics-before.prom`
- `vllm-metrics-after.prom`
- `vllm-metrics-red-before.prom` and related role-specific snapshots when red/blue endpoints differ
- parsed counters inside `metrics.json`

The CLI also attempts a local GPU snapshot with `amd-smi` first and `rocm-smi` second. If neither tool exists, `metrics.json` records `status: unavailable` instead of failing the run.

## Work you can do before AMD GPU access

While waiting on DigitalOcean/AMD support, prepare the non-GPU pieces:

- DigitalOcean project and firewall policy
- SSH keys and least-privilege access
- non-GPU droplet for LocalStack/nullstate smoke tests
- Docker installation and update policy
- GitHub repository secrets/environment names
- local `.env` file based on `.env.example`
- sanitized screenshots of repo workflow, PR checks, and offline demo
- LocalStack Azure token/access path if available

## Artifact review before publishing

Check:

- `runs/<id>/report.md`
- `runs/<id>/findings.json`
- `runs/<id>/events.jsonl`
- `runs/<id>/metrics.json`
- `runs/<id>/vllm-metrics-before.prom`
- `runs/<id>/vllm-metrics-after.prom`
- `runs/<id>/remediation.patch`

Do not publish secrets, real tenant IDs, real subscription IDs, private endpoints, or Terraform state.
