# First 10 Minutes

This quickstart is the safest path for a new open-source user. It uses the offline AWS S3 scenario, mock agents, and local artifact generation.

No Docker required. No LocalStack required. No model endpoint required. No real cloud credentials required.

## 1. Install from a checkout

```powershell
git clone https://github.com/Ker102/nullstate-cli.git
cd nullstate-cli
python -m pip install -e .
```

If the `nullstate` command is not on your `PATH`, use `python -m nullstate` for the same commands.

## 2. Check the local environment

```powershell
nullstate doctor --offline
nullstate status
```

Expected result:

- the CLI prints the Nullstate launch/status output
- missing Docker, Terraform, LocalStack, or model endpoints are acceptable for this offline path

## 3. Run a deterministic offline scan

```powershell
nullstate run examples/aws-public-s3 --offline --mock-agents
```

Expected result:

- one high-severity S3 public-access finding
- red before: success
- red after: blocked
- run artifacts written under `runs/<run-id>/`

## 4. Open the report

```powershell
nullstate report
```

Look for:

- finding summary
- attack reasoning
- remediation patch
- validation result
- runtime evidence classification

## 5. Build shareable local artifacts

```powershell
nullstate bundle
nullstate dashboard --open
nullstate sarif
nullstate evidence-manifest
nullstate evidence-verify
```

Generated artifacts include:

- `run-bundle.json`
- `dashboard.html`
- `nullstate.sarif`
- `evidence-manifest.json`
- `evidence-verification.json`

## 6. Scrub before sharing

```powershell
nullstate scrub
```

Share the scrubbed copy under `scrubbed-runs/`, not the raw `runs/` directory.

## 7. Optional GitHub Actions gate

```powershell
nullstate init-ci github --scenario aws-public-s3 --iac-path examples/aws-public-s3
```

Generated files:

- `.github/workflows/nullstate.yml`
- `nullstate-policy.json`

Commit both files to run the offline Nullstate gate on pull requests. Adjust `--iac-path` to your Terraform directory before using this in a real repository.

## 8. Optional live AWS LocalStack path

Use this only after Docker and LocalStack are configured:

```powershell
nullstate sandbox up localstack-aws
nullstate sandbox status localstack-aws
nullstate run examples/aws-public-s3 --target localstack-aws --mock-agents
nullstate report
nullstate sandbox down localstack-aws
```

The live AWS path is the currently proven local runtime scenario. It deploys the vulnerable fixture into LocalStack AWS, runs the constrained anonymous object-read probe, applies deterministic remediation, and reruns the probe after remediation.

## Current Azure Note

The Azure Blob scenario is available for offline deterministic validation, but live LocalStack Azure validation requires the LocalStack workspace/user to have Azure Emulator entitlement. If `localstack/localstack-azure-alpha` exits with code `55`, check `docker logs localstack-azure`; the likely cause is that the Azure Emulator is not enabled for the account.
