# Runbook

## Local offline demo

```powershell
python -m pip install -e .
python -m nullstate doctor --offline
python -m nullstate run examples/azure-public-blob --offline
```

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

## Model endpoint setup

Set:

```powershell
$env:NULLSTATE_LLM_BASE_URL = "http://localhost:8000"
$env:NULLSTATE_LLM_API_KEY = "<optional>"
```

Then run without `--offline`.

## AMD Developer Cloud / DigitalOcean path

Use [AMD Compute Strategy](compute-strategy.md) as the deployment checklist. Build the non-GPU DigitalOcean baseline first, then attach the MI300X-backed model endpoint when access is available.

## Fireworks fallback

If AMD GPU access is delayed, point `NULLSTATE_LLM_BASE_URL` at the managed endpoint and keep the same nullstate run flow. Label the evidence as managed inference, not private GPU-hosted inference.

## Metrics evidence

When `NULLSTATE_LLM_BASE_URL` is set, nullstate tries to scrape:

```text
<NULLSTATE_LLM_BASE_URL>/metrics
```

If the endpoint exposes vLLM Prometheus metrics, the run writes:

- `vllm-metrics-before.prom`
- `vllm-metrics-after.prom`
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
