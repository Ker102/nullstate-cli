# Technical Walkthrough

This document explains how `nullstate` works from the first CLI command to the final report artifact. It is written for reviewers who want to understand the implementation path, security boundaries, and current extension points.

## What Nullstate Runs

`nullstate` is a local-first purple-team loop for infrastructure-as-code. The current implementation focuses on Terraform storage-exposure scenarios:

- AWS S3 public access block disabled
- Azure Blob container public access

It also includes offline scenario scaffolds for Kubernetes, Docker Compose, on-prem digital twins, and generic plan review.

The CLI combines three layers:

1. Deterministic security logic for findings, remediation, and pass/fail validation.
2. Sandbox adapters for local execution targets such as LocalStack.
3. Model-assisted red-team and blue-team reasoning through OpenAI-compatible endpoints.

The model helps with reasoning and explanation. It is not the source of truth for whether the vulnerability exists or whether remediation worked.

## Demo Command Flow

Typical offline flow:

```powershell
nullstate
nullstate status
nullstate run examples/aws-public-s3 --offline
nullstate report
```

Typical live LocalStack AWS flow:

```powershell
nullstate sandbox up localstack-aws
nullstate sandbox status localstack-aws
nullstate run examples/aws-public-s3 --target localstack-aws
nullstate report
```

Typical live LocalStack Azure flow:

```powershell
nullstate sandbox up localstack-azure
nullstate sandbox status localstack-azure
nullstate run examples/azure-public-blob --target localstack-azure
nullstate report
```

When a self-hosted model endpoint is available, set one shared endpoint:

```powershell
$env:NULLSTATE_LLM_BASE_URL = "http://127.0.0.1:8000"
```

Or set role-specific endpoints:

```powershell
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
```

## Runtime Modes

### Offline Mode

`--offline` skips Terraform runtime and cloud emulator calls. The CLI uses static IaC parsing and deterministic scenario behavior. This mode is used for repeatable demos, tests, and development without Docker, LocalStack, or a GPU.

Important detail: `--offline` does not automatically disable model calls. If model endpoint environment variables are configured, red and blue agent calls still use those endpoints. Use `--mock-agents` when the intended behavior is fully deterministic and no-model.

### Live LocalStack Mode

Live mode copies the Terraform project into a run workspace, runs Terraform automation commands, targets LocalStack, runs the red/blue loop, applies remediation in the copied workspace, and validates again.

The original Terraform directory is not mutated. Remediation happens in:

```text
runs/<run-id>/workspace/
```

### Model Endpoint Mode

The model endpoint must expose an OpenAI-compatible API. This allows the same CLI integration to work with local vLLM, SGLang, or a managed fallback.

The CLI records model token counts and latency from response `usage` fields when available. It also tries to scrape Prometheus-style `/metrics` from the endpoint and writes the raw metrics snapshots into the run directory.

## End-to-End Execution Path

### 1. Command Entry

Entry point:

```text
src/nullstate/cli.py
```

The `run` command receives:

- Terraform directory
- target backend, or `auto`
- scenario, or `auto`
- offline/mock flags
- run artifact directory
- red and blue model settings

If no command is provided, the CLI prints the branded launch screen and likely next commands.

### 2. Scenario Inference

Relevant files:

```text
src/nullstate/scenario_detection.py
src/nullstate/scenarios.py
```

When `--scenario auto` is used, the CLI inspects the IaC directory and maps the input to a known scenario. For example:

- `examples/aws-public-s3` maps to `aws-public-s3`
- `examples/azure-public-blob` maps to `azure-public-blob`

The scenario definition chooses the default sandbox backend. Users can still override this with `--target`.

### 3. Sandbox Backend Selection

Relevant file:

```text
src/nullstate/sandbox.py
```

Sandbox backends define:

- backend name
- target IaC type
- execution mode
- Docker image
- up/down commands
- runtime probes

Current backends include:

| Backend | Purpose |
|---|---|
| `localstack-aws` | Live AWS-style storage scenario execution |
| `localstack-azure` | Live Azure-style storage scenario execution |
| `kind-kubernetes` | Kubernetes scenario scaffold |
| `docker-compose` | Docker Compose digital-twin scaffold |
| `microvm-onprem` | On-prem digital-twin scaffold |
| `plan-only` | No-runtime analysis mode |

`nullstate sandbox up` starts the backend. `nullstate sandbox status` checks Docker and HTTP reachability where applicable.

### 4. Run Workspace Creation

The CLI creates a new run directory:

```text
runs/<run-id>/
```

It copies the input Terraform directory into:

```text
runs/<run-id>/workspace/
```

This keeps the original project intact. Terraform state, `.terraform`, cached plans, and run directories are excluded from the copy.

### 5. Terraform Plan Loading

Relevant file:

```text
src/nullstate/terraform.py
```

In live mode, the Terraform flow follows automation-friendly commands:

```text
terraform init -input=false
terraform plan -out=tfplan -input=false
terraform show -json tfplan
```

In offline mode, the CLI uses a static Terraform parser for the supported demo fixtures. This keeps tests and demos reproducible even without external runtime dependencies.

Terraform command results are written into:

```text
runs/<run-id>/events.jsonl
```

### 6. Finding Detection

Relevant file:

```text
src/nullstate/findings.py
```

The deterministic detector identifies supported risky configuration. Examples:

- Azure Blob container has `container_access_type = "blob"` or `"container"`
- Azure storage account allows nested public items
- AWS S3 public access block controls are disabled

Findings are written as structured JSON:

```text
runs/<run-id>/findings.json
```

This deterministic finding data is the source of truth for the rest of the run.

### 7. Red-Team Model Reasoning

Relevant file:

```text
src/nullstate/agents.py
```

The red agent receives internal instructions and scenario evidence. The user does not manually prompt the model during the run.

The red model returns attack reasoning, for example:

- anonymous S3 object read path
- anonymous Azure Blob container read path
- likely evidence to collect

If no endpoint is configured, the role falls back to deterministic mock output.

### 8. Constrained Attack Script Execution

Relevant files:

```text
src/nullstate/attack.py
src/nullstate/attack_runner.py
```

`nullstate` writes a generated attack artifact:

```text
runs/<run-id>/attack.py
runs/<run-id>/attack-manifest.json
```

The manifest records the scenario, backend, target URL, and resource hints that scenario probes can use without giving the model arbitrary command construction power.

Then the constrained runner executes only that generated script. It enforces these boundaries:

- script name must be exactly `attack.py`
- script must live directly inside the current run directory
- execution uses the current Python interpreter
- no arbitrary shell command is accepted
- dynamic inputs are limited to `--target-url`, `--stage`, and the generated run-directory `attack-manifest.json`

The runner records command evidence before and after remediation:

```json
{
  "phase": "red-tool",
  "message": "Allowlisted attack command completed",
  "data": {
    "command": ["python", "attack.py", "--target-url", "...", "--stage", "before", "--manifest", "..."],
    "target_url": "...",
    "stage": "before",
    "returncode": 0,
    "stdout": "...",
    "stderr": "",
    "started_at": "...",
    "ended_at": "...",
    "duration_seconds": 0.123
  }
}
```

This gives the report real command evidence while avoiding unrestricted red-agent tool access.

Enterprise guardrails for this layer:

- The command policy is scenario-template based. The model can reason about the attack path, but it cannot choose an arbitrary shell command.
- Runtime targets should remain local sandbox endpoints unless a future `--allow-live-cloud` flag is implemented and recorded.
- `red-tool` events should evolve to include a command schema version and a reproducibility hash for the generated `attack.py`.
- Probe stdout and stderr should be capped before upload, ticket attachment, or long-term evidence retention.
- Reports must distinguish observed runtime evidence from deterministic simulation and emulator-inconclusive probes.

### 9. Deterministic Remediation

Relevant file:

```text
src/nullstate/remediation.py
```

The blue model explains the remediation, but the patch itself is produced by deterministic remediation logic.

For Azure Blob exposure, remediation sets:

```hcl
allow_nested_items_to_be_public = false
container_access_type           = "private"
```

For AWS S3 exposure, remediation sets public access block controls to `true`:

```hcl
block_public_acls       = true
block_public_policy     = true
ignore_public_acls      = true
restrict_public_buckets = true
```

The diff is written to:

```text
runs/<run-id>/remediation.patch
```

### 10. Re-Plan and Validation

After remediation, the CLI loads the remediated workspace again. In live mode it runs Terraform plan/apply steps against the copied workspace. In offline mode it re-parses the updated files.

The detector runs again. If the finding is gone, the deterministic attack simulation returns:

```text
Red after: blocked
```

The constrained attack script also runs a second time with:

```text
--stage after
```

That post-remediation command output is logged as another `red-tool` event.

### 11. Report and Metrics

Relevant files:

```text
src/nullstate/report.py
src/nullstate/metrics.py
```

Each run writes:

| Artifact | Purpose |
|---|---|
| `events.jsonl` | Full event timeline |
| `findings.json` | Structured vulnerability findings |
| `attack.py` | Generated constrained attack artifact |
| `attack-manifest.json` | Scenario, backend, target URL, and resource hints for constrained probes |
| `remediation.patch` | Terraform remediation diff |
| `metrics.json` | Model calls, token counts, latency, endpoint metrics |
| `report.md` | Human-readable summary |
| `workspace/` | Copied and remediated IaC workspace |

`nullstate report` opens the latest report by default, including reports nested under named run directories.

`nullstate bundle` writes `run-bundle.json`, the portable evidence contract for local dashboards, CI upload, support bundles, and future Nullstate Cloud ingestion.

`nullstate dashboard` writes `dashboard.html`, a free single-run local dashboard that can be opened without cloud login.

## Security Boundaries

The important boundaries are:

- No real cloud target by default.
- Terraform changes happen in a copied workspace.
- The red model does not receive shell access.
- The attack runner only executes generated run-directory `attack.py`.
- Secrets are loaded from environment variables or ignored local env files.
- Run artifacts must be reviewed before publishing.
- A future artifact scrubber should run before public case-study publishing, CI upload, or support bundle sharing.
- A future `--allow-live-cloud` gate should be required before any non-local cloud endpoint is targeted.

## Extension Points

### New Scenario

Add or update:

```text
src/nullstate/scenarios.py
src/nullstate/scenario_detection.py
src/nullstate/findings.py
src/nullstate/remediation.py
src/nullstate/attack.py
examples/<scenario-name>/
tests/
```

### New Sandbox Backend

Add backend metadata and commands in:

```text
src/nullstate/sandbox.py
```

Then add tests for:

- `sandbox list`
- `sandbox status`
- `sandbox up --dry-run`
- `sandbox down`

### Richer Red Tooling

The next safe expansion is not free-form shell access. It should be a per-scenario allowlist:

- generated Python probes
- fixed command templates
- local-only target URLs
- strict timeout
- full event logging
- no inherited real cloud credentials

See [Enterprise Readiness](enterprise-readiness.md) for the control checklist that should be completed before positioning runtime probes as team or enterprise evidence.

## Test Coverage

Primary validation commands:

```powershell
python -m unittest discover -s tests -v
python -m ruff check src tests
python -m mypy src
```

Useful smoke test:

```powershell
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --runs-dir runs/red-tool-smoke
python -m nullstate report --runs-dir runs/red-tool-smoke
```

The smoke run should show:

- one finding before remediation
- `Red before: success`
- `Red after: blocked`
- two `red-tool` events in `events.jsonl`
