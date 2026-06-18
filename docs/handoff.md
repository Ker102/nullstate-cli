# Nullstate Project Handoff

Last updated: 2026-06-18

## Read this first

This file is written for a fresh agent with no conversation history and no MCP tools. Everything needed to continue should be discoverable from local repo files and normal terminal commands.

The hackathon freeze rule was lifted on 2026-06-18 by the project owner. `feature/red-agent-runner` may be merged to `main` once PR review blockers are resolved and verification passes.

- Current active branch: `feature/red-agent-runner`.
- Current local state at handoff: active work continues on this feature branch; run `git status --short --branch` and `git log --oneline -8` for exact local ahead/uncommitted state.

Recent local-only commits:

```text
cad9f3c fix: fail sandbox up when container exits
504533e feat: add artifact scrubber command
10a4699 feat: record attack output truncation metadata
2a90716 feat: enforce local attack targets
ee6d883 docs: add enterprise readiness guardrails
2ab50f8 feat: add Azure blob runtime probe foundation
d1e419f docs: harden handoff for fresh agents
ccc613e fix: block AWS evidence read after remediation
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
- LLM provider presets:
  - `custom` / `openai-compatible` for self-hosted vLLM, SGLang, private gateways, and explicit base URLs
  - `google` for Google AI Studio / Gemini through the Gemini OpenAI-compatible endpoint
  - `claude` for Anthropic's OpenAI SDK compatibility endpoint, documented as experimental until a native Claude adapter exists
  - role-specific providers and base URLs for red/blue split testing
- Constrained red command runner:
  - only generated `attack.py`
  - no arbitrary shell
  - command evidence logged to `events.jsonl`
- Generated `attack-manifest.json`:
  - schema-addressed and validated before constrained probe execution
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
- Upload dry-run scaffold:
  - `nullstate upload --dry-run`
  - refreshes `run-bundle.json`
  - writes `runs/<id>/upload-plan.json`
  - includes a `$schema` pointer to `docs/schemas/upload-plan.schema.json`
  - validates the upload-plan shape before writing
  - records token env presence without storing token values
- SARIF export:
  - `nullstate sarif`
  - writes `runs/<id>/nullstate.sarif`
  - emits SARIF 2.1.0 findings for CI and code-scanning upload
  - `.github/workflows/nullstate-sarif.yml` runs an offline scenario and uploads SARIF to GitHub code scanning
- CI mode:
  - `nullstate run --ci`
  - writes schema-validated `runs/<id>/ci-summary.json`
  - exits with code `2` when original findings meet or exceed `--fail-on-severity`
  - supports `none`, `low`, `medium`, `high`, and `critical` thresholds
- Baseline comparison:
  - `nullstate baseline`
  - writes a JSON baseline of `rule_id|resource_address` identities
  - `nullstate run --ci --baseline-file` evaluates the severity threshold against new findings only
- JSON policy result:
  - `nullstate policy-result`
  - writes `runs/<id>/policy-result.json`
  - evaluates an existing run against severity threshold and optional baseline without re-running the scan
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
  - `nullstate policy init` creates a red-tool allowlist policy scaffold
  - `nullstate run --policy-file` enforces allowed scenarios, backends, stages, generated `attack.py` flags, target classifications, target hosts, command policy IDs, timeout ceilings, and output-size ceilings
  - `red-tool` payloads include schema version, scenario, backend, command policy ID, target classification, SHA-256 hashes, and stdout/stderr truncation flags
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

Current productization checkpoints on `feature/red-agent-runner` also include:

- provider presets for Google, Claude, custom, and generic OpenAI-compatible endpoints
- SARIF export and GitHub Actions code-scanning workflow
- SARIF physical locations for GitHub Code Scanning upload
- schema-validated CI summaries, fail-on-severity gates, and baseline comparison
- upload dry-run planning for future cloud ingestion
- upload-plan v1 schema documentation and local upload-plan validation
- upload scrub preflight warnings for raw runs
- red-tool policy scaffold and standalone `policy-result.json`
- scenario-scoped policy presets through `nullstate policy init --scenario <name>`
- scenario/backend allowlists in red-tool policy files
- target host allowlists in red-tool policy files
- command argument, stage, timeout, and output-size controls in red-tool policy files
- generated policy schema documentation and local generated-policy validation
- attack-manifest schema documentation and local attack-manifest validation
- policy validation output through `nullstate policy validate`
- evidence integrity manifests with optional HMAC signing through `nullstate evidence-manifest`
- evidence-manifest v1 schema documentation and local evidence-manifest validation
- evidence hash verification through `nullstate evidence-verify`
- review-hardening fixes for fail-closed `policy-result` inputs, copied evidence manifests, and malformed manifest CLI errors
- default-off live-cloud approval gate through `nullstate run --allow-live-cloud`
- release manifest and GitHub artifact attestations for tagged package releases
- release SBOM generation and SBOM artifact attestation for tagged package releases
- release SBOM validation before manifest generation and attestation
- SPDX tools validation for generated release SBOMs
- keyless Sigstore release signing for primary release assets
- manual release dry-run rehearsal before tagging
- first tagged release verification checklist in the runbook
- versioned remediation metadata through schema-validated `remediation.json`, report sections, and run-bundle evidence
- run-bundle v1 schema documentation and local bundle validation
- deeper local dashboard evidence view with remediation, bundle contract, and artifact inventory sections
- enforcing GitHub Actions template under `docs/templates/github-actions/nullstate-enforcing.yml`

Do not jump straight to full SaaS before stabilizing:

1. live upload implementation after a real ingestion API exists
2. real cloud ingestion service and real-cloud adapters with provider-specific endpoint policies

## Branch and release guidance

Until the user says the freeze is over:

- Do not merge PR #24.
- Do not push or merge to `main`.
- Feature branch checkpoint pushes are allowed.
- After applying CodeRabbit review feedback, do not push solely to trigger another CodeRabbit review loop; fold those fixes into the next substantive batch unless the user explicitly approves a review-response push.
- Do not tag releases.
- Do not update `main`.
