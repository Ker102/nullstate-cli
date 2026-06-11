# Nullstate Project Handoff

Last updated: 2026-06-09

## Read this first

This file is written for a fresh agent with no conversation history and no MCP tools. Everything needed to continue should be discoverable from local repo files and normal terminal commands.

The repository is currently under a hackathon freeze rule:

- Do not merge anything into `main`.
- Do not push new work unless the user explicitly asks.
- It is safe to keep working locally on feature branches and make local commits.
- Current active branch: `feature/red-agent-runner`.
- Current local state at handoff: active work continues on this feature branch; run `git status --short --branch` and `git log --oneline -8` for exact local ahead/uncommitted state.

Recent local-only commits:

```text
feat: add Azure blob runtime probe foundation
ccc613e fix: block AWS evidence read after remediation
0c26efe feat: add AWS runtime evidence probe
baa782b docs: add project handoff
7117340 feat: add run bundles and local dashboard
55775a7 feat: add attack manifest foundation
```

These commits have not been pushed at the time of this handoff. Confirm with:

```powershell
git status --short --branch
git log --oneline -8
```

Do not rely on MCP state, chat memory, or remote PR metadata. Use local files and Git only unless the user explicitly provides other tooling.

## Project goal

`nullstate` is becoming an open-core DevSecOps product:

- open-source CLI for local IaC purple-team validation
- free single-user local dashboard/viewer
- paid Team/Enterprise cloud or self-hosted platform for dashboards, managed model calls, evidence history, CI ingestion, support, scheduled scans, alerts, RBAC, audit logs, and compliance exports

Core positioning:

```text
Prove, patch, and validate IaC risk.
```

## Current technical state

Working features:

- Python Typer/Rich CLI.
- Terraform/IaC scenario detection.
- Offline deterministic runs.
- Live LocalStack AWS/Azure scenario path.
- Deterministic finding detection and remediation.
- Red/blue model wrappers for OpenAI-compatible endpoints.
- Constrained red command runner:
  - only generated `attack.py`
  - no arbitrary shell
  - command evidence logged to `events.jsonl`
- Generated `attack-manifest.json`:
  - scenario
  - backend
  - target URL
  - resource hints
- Azure Blob runtime probe foundation:
  - Azure demo now creates `azurerm_storage_blob.evidence`
  - generated Azure `attack.py` parses `attack-manifest.json`
  - generated Azure `attack.py` attempts anonymous HTTP GET against candidate blob URLs
  - before-remediation probe failures are marked inconclusive rather than treated as proof
  - offline Azure runs are labeled deterministic simulation in reports
- Portable run bundle:
  - `nullstate bundle`
  - writes `runs/<id>/run-bundle.json`
- Free local HTML dashboard:
  - `nullstate dashboard`
  - writes `runs/<id>/dashboard.html`
- Enterprise readiness documentation:
  - `docs/enterprise-readiness.md`
  - local-only target expectations
  - future `--allow-live-cloud` gate
  - command allowlist and artifact scrubber requirements
  - first-pass event schema and reproducibility hash metadata
- Code-level enterprise guardrails:
  - attack runner rejects non-local HTTP targets by default
  - allowed targets are offline, local, loopback, localhost, and LocalStack-scoped HTTP(S)
  - `red-tool` payloads include schema version, command policy ID, target classification, SHA-256 hashes, and stdout/stderr truncation flags
  - `nullstate scrub` creates non-destructive scrubbed run copies and `scrub-report.json`
- Sandbox startup hardening:
  - `sandbox up` now verifies that a named Docker container remains running after `docker run -d`
  - exited containers are reported as failed starts instead of false success
- AWS S3 runtime probe foundation:
  - AWS demo now creates an `aws_s3_object` evidence object
  - AWS demo includes a public read bucket policy for `evidence.txt`
  - generated AWS `attack.py` parses `attack-manifest.json`
  - generated AWS `attack.py` attempts anonymous HTTP GET against candidate S3 object URLs
  - AWS remediation removes the public bucket policy and the demo-only evidence object
  - `report.md` includes a `Runtime Command Evidence` section
  - live LocalStack AWS validation succeeded:
    - before remediation: HTTP 200 with `nullstate public S3 evidence`
    - after remediation: HTTP 404 with `runtime_exploit_observed=false`

Important limitation:

- The constrained red runner is real. AWS now has a live-validated object-read probe path. Azure now has a manifest-backed blob-read probe, but live LocalStack Azure validation is still pending.
- The before/after success verdict is still mostly deterministic via `simulate_attack()`.
- Enterprise-grade exploit validation still requires live Azure emulator confirmation and possible URL/API tuning if LocalStack Azure semantics differ.

## Important docs

Start here:

- `README.md`
- `docs/technical-walkthrough.md`
- `docs/case-study.md`
- `docs/enterprise-roadmap.md`
- `docs/enterprise-readiness.md`
- `docs/plans/2026-06-01-real-sandbox-red-team-commands.md`

The implementation plan for the next core security feature is:

```text
docs/plans/2026-06-01-real-sandbox-red-team-commands.md
```

## Last verification run

The last full verification passed:

```powershell
python -m ruff check src tests
python -m mypy src
python -m unittest discover -s tests -v
```

Result:

```text
Ruff passed
mypy passed
69 tests OK
```

Smoke run also passed:

```powershell
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --runs-dir runs/platform-smoke
python -m nullstate bundle --runs-dir runs/platform-smoke
python -m nullstate dashboard --runs-dir runs/platform-smoke
```

Generated:

- `run-bundle.json`
- `dashboard.html`

Live LocalStack AWS validation also passed locally:

```powershell
python -m nullstate sandbox up localstack-aws
python -m nullstate run examples/aws-public-s3 --target localstack-aws --scenario aws-public-s3 --runs-dir runs/live-real-red-aws-blocked
python -m nullstate sandbox down localstack-aws
```

Observed result:

```text
Before remediation:
- HTTP 200
- body_excerpt=nullstate public S3 evidence
- runtime_exploit_observed=true

After remediation:
- HTTP 404
- runtime_exploit_observed=false
```

Run artifacts are under `runs/` and may be ignored by Git. If this repository is opened on another device, reproduce the validation with the commands above instead of assuming the run directory exists.

Live LocalStack Azure validation attempt on 2026-06-11 did not reach Terraform execution. The container started and exited with LocalStack reporting that the Azure Emulator is not enabled for the account/license. Do not keep retrying until the LocalStack account has Azure Emulator entitlement; each retry pulls a large image and can exhaust disk.

## Where to continue

Next highest-value feature:

```text
Live LocalStack Azure validation for the Azure Blob runtime probe
```

The AWS implementation now has the Terraform evidence object, public-read policy, manifest-backed candidate URL generation, report runtime evidence section, and live LocalStack confirmation. The Azure implementation now has the Terraform evidence blob, manifest-backed candidate URL generation, and report classification language, but has not yet been validated against a live LocalStack Azure container.

Next implementation should:

1. Run live LocalStack Azure validation for `examples/azure-public-blob`.
2. Inspect `events.jsonl` and `report.md` for before/after Azure runtime classifications.
3. Tune candidate Azure blob URLs only if LocalStack Azure uses a different route.
4. Keep report language honest:
   - observed runtime exploit evidence
   - deterministic simulation
   - inconclusive emulator result
5. Keep safety boundaries:
   - local endpoints only
   - no arbitrary shell
   - no real cloud credentials
   - strict timeout

Recommended next tests:

- Live LocalStack Azure run where available.
- Offline run still passes.
- Report classifies runtime evidence as observed/inconclusive/simulated.
- Remaining enterprise hardening: future live-cloud approval gate and live Azure emulator validation after LocalStack Azure entitlement is available.

If Azure LocalStack support is unavailable or unreliable, do not overclaim Azure runtime exploitation. Prefer clear report language such as `runtime probe inconclusive; deterministic IaC validation still blocked the configured exposure`.

## Product direction

The product strategy is open-core:

- CLI stays open source.
- Local dashboard/viewer is free and single-user.
- Paid platform includes team dashboards, managed model calls, support, scheduled scans, alerts, RBAC, audit logs, integrations, compliance exports, and self-hosted deployment.

Run bundle is the key contract between:

- CLI
- local GUI
- CI
- cloud upload
- support tickets
- future enterprise dashboards

Do not jump straight to full SaaS before stabilizing:

1. run bundle schema
2. local dashboard
3. CI mode and SARIF/JSON export
4. upload dry-run/cloud token scaffold
5. real cloud ingestion service

## Branch and release guidance

Until the user says the freeze is over:

- Do not merge PR #24.
- Do not push local commits unless asked.
- Do not tag releases.
- Do not update `main`.

If the next agent needs to preserve work before switching devices, ask the user whether to push the current branch. Do not assume.
