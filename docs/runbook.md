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

## Artifact review before publishing

Check:

- `runs/<id>/report.md`
- `runs/<id>/findings.json`
- `runs/<id>/events.jsonl`
- `runs/<id>/metrics.json`
- `runs/<id>/remediation.patch`

Do not publish secrets, real tenant IDs, real subscription IDs, private endpoints, or Terraform state.
