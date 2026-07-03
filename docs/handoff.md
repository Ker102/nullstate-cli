# Nullstate Project Handoff

Last updated: 2026-06-27

## Read this first

This file is written for a fresh agent with no conversation history and no MCP tools. Everything needed to continue should be discoverable from local repo files and normal terminal commands.

The hackathon freeze rule was lifted on 2026-06-18 by the project owner. PR #24 was squash-merged into `main` after review blockers and remote checks were cleared.

- Current active branch: `docs/open-source-readiness`.
- Current local state at handoff: this branch contains unmerged open-source readiness and external-agent trust work. Run `git status --short --branch` and `git log --oneline -8` for exact local state.

Recent merged checkpoint:

```text
f621b1b docs: record PR 24 merge
1e7b1c6 feat: add constrained red attack runner
```

Confirm the current state with:

```powershell
git status --short --branch
git log --oneline -8
```

Do not rely on MCP state, chat memory, or remote PR metadata. Use local files and Git only unless the user explicitly provides other tooling.

## Fresh agent checklist

When this project is opened on the main device:

1. Confirm branch and cleanliness:

   ```powershell
   git status --short --branch
   git log --oneline -8
   ```

2. Confirm local secret files are present only locally and ignored by Git:

   ```powershell
   git check-ignore .env .env.local
   ```

3. Recreate the local Python environment if needed:

   ```powershell
   python -m pip install -e .
   ```

4. Run the verification gate before taking new work:

   ```powershell
   python -m ruff check src tests
   python -m mypy src
   python -m unittest discover -s tests -v
   ```

5. Start a new feature branch for follow-up product work. Keep `main` protected and use PR checks.

## Project goal

`nullstate` is becoming an open-core DevSecOps product:

- open-source CLI for local IaC purple-team validation
- free single-user local dashboard/viewer
- paid Team/Enterprise cloud or self-hosted platform for dashboards, managed model calls, evidence history, CI ingestion, support, scheduled scans, alerts, RBAC, audit logs, and compliance exports

Core positioning:

```text
Prove, patch, and validate cloud attack paths.
```

Expanded product direction:

- IaC remains a first-class source of intended AWS and Azure state, but it is not assumed to describe the complete environment.
- Future read-only provider discovery supplies deployed resources, identity relationships, network paths, logs, and drift.
- A normalized environment graph connects attacker identities to reachable services, exposed data, and privileged capabilities.
- AI agents are first-class principals. Preserve their own identity, delegated user, runtime/tool identity, downstream credentials, and target operation as separate graph nodes.
- Future AWS and Azure discovery should inventory provider-native agent identities as well as conventional service principals, managed identities, IAM roles, and workload identities used by agents.
- Agent security scenarios should cover compromised instructions, prompt injection, memory/tool compromise, excessive agency, confused-deputy behavior, shared runtime identities, and agent-to-agent trust.
- External agent runtime posture is designed in `docs/plans/2026-06-22-external-agent-trust-design.md`.
- Posture evidence must preserve source, issuer, verification method, freshness, confidence, and unknown assumptions.
- Do not reduce posture to a single opaque score or claim that signed artifacts/hardware attestation prove complete application safety.
- Production is observed with read-only access and only explicitly approved non-destructive checks.
- Exploit validation reconstructs the minimum relevant path in a controlled environment using synthetic evidence data.
- CI has three modes: pull-request IaC validation, post-deployment observed-state validation, and scheduled drift/assurance runs.
- `docs/product-validation-model.md` is the primary reference for this architecture and its production-safety rationale.

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
- External-agent trust posture is currently manifest-driven and deterministic. It validates a local manifest and reports posture/blast-radius risk, but it does not yet collect live provider inventory, verify third-party runtime attestation, or enforce a tenant authorization gateway.

## Important docs

Start here:

- `README.md`
- `docs/technical-walkthrough.md`
- `docs/case-study.md`
- `docs/enterprise-roadmap.md`
- `docs/enterprise-readiness.md`
- `docs/product-validation-model.md`
- `docs/plans/2026-06-22-external-agent-trust-design.md`
- `docs/plans/2026-06-01-real-sandbox-red-team-commands.md`

The implementation plan for the next core security feature is:

```text
docs/plans/2026-06-01-real-sandbox-red-team-commands.md
```

The implementation plan for the current external-agent CLI preview is:

```text
docs/superpowers/plans/2026-06-27-external-agent-trust-cli.md
```

## Last verification run

The last full verification passed on 2026-06-19 after reinstalling the project with dev extras:

```powershell
python -m pip install -e .[dev]
```

```powershell
python -m ruff check src tests
python -m mypy src
python -m unittest discover -s tests -v
```

Result:

```text
Ruff passed
mypy passed
146 tests OK
```

Smoke run also passed on 2026-06-19:

```powershell
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --runs-dir runs/handback-smoke-20260619-195333
python -m nullstate bundle --runs-dir runs/handback-smoke-20260619-195333
python -m nullstate dashboard --runs-dir runs/handback-smoke-20260619-195333
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

Current branch feature now includes:

```powershell
nullstate agent posture verify examples/agent-trust/external-agent-manifest.json
nullstate agent blast-radius examples/agent-trust/external-agent-manifest.json
nullstate summary --json
nullstate context validate examples/cloud-context/aws-readonly-context.json
nullstate context summary examples/cloud-context/aws-readonly-context.json --json
nullstate eval run examples/eval/iac-security-regression.json --output-dir eval-runs/iac-security-regression
nullstate init-ci github --scenario aws-public-s3 --iac-path examples/aws-public-s3
nullstate report --runs-dir examples/sample-runs
nullstate summary --runs-dir examples/sample-runs --json
```

The eval suite now includes a `baseline` block for a generic IaC-only review. `eval-results.json` and `eval-report.md` compare Nullstate's attack replay evidence, remediation validation, token metrics, and artifact coverage against that baseline. This is not yet an integration with Checkov, tfsec, Terrascan, or a coding-agent baseline.

The repo now includes a scrubbed sample run under `examples/sample-runs/20260702-182015` so new users can inspect report, summary, bundle, and dashboard output without running Docker, Terraform, LocalStack, or model endpoints. The sample includes checked-in `report.md`, `run-bundle.json`, and `dashboard.html`.

Dependency audit status is documented in `docs/dependency-audit.md`. Last local audit on 2026-07-02 used `python -m pip_audit . --skip-editable` with `pip-audit 2.10.0` and found no known vulnerabilities.

Local release install smoke is available through `python scripts/release/install_smoke.py`. It builds the wheel into a temp directory, installs it into a clean venv, and verifies the `nullstate` console command plus `nullstate doctor --offline`. This supports release readiness but does not replace testing install from a published tag.

The tagged release workflow also performs a `Smoke install release wheel` step after `python -m build`; it installs `dist/*.whl` into `.smoke-venv` and runs the generated `nullstate` console command before SBOM generation, attestation, signing, or release creation.

Related files:

- `src/nullstate/agent_trust.py`
- `src/nullstate/cloud_context.py`
- `src/nullstate/ci_templates.py`
- `src/nullstate/evaluation.py`
- `src/nullstate/summary.py`
- `tests/test_agent_trust.py`
- `tests/test_cloud_context.py`
- `tests/test_ci_templates.py`
- `tests/test_evaluation.py`
- `tests/test_summary.py`
- `docs/schemas/external-agent-manifest.schema.json`
- `docs/schemas/cloud-context.schema.json`
- `docs/schemas/eval-suite.schema.json`
- `docs/schemas/run-summary.schema.json`
- `examples/agent-trust/external-agent-manifest.json`
- `examples/agent-trust/README.md`
- `examples/cloud-context/aws-readonly-context.json`
- `examples/cloud-context/README.md`
- `examples/eval/iac-security-regression.json`
- `examples/eval/README.md`

The context command is a local manifest contract only. It does not call AWS, Azure, GCP, or any cloud API yet.

The eval harness measures Nullstate's own supported cases today. It does not yet compare against scanner-only tools, manual review, or generic coding-agent review.

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
- Remaining enterprise hardening: live Azure emulator validation after LocalStack Azure entitlement is available.

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

Current productization checkpoints merged into `main` include:

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

Current branch-only updates on `docs/open-source-readiness` include:

- explicit scenario evidence levels in `src/nullstate/scenarios.py`
- `nullstate scenarios list` prints a full evidence-level legend before the Rich table
- `nullstate scenarios status <name>` includes the evidence level and evidence summary
- README scenario table now distinguishes `live-validated`, `offline-deterministic`, `scaffolded`, and `plan-only`
- open-source readiness milestone for labeling non-live scenarios is marked complete
- `scripts/release/install_smoke.py` supports `--tag <tag>` and `--package-spec <spec>` in addition to local-wheel mode
- Windows latest-tag smoke passed for `v0.1.0-alpha.2`; Linux latest-tag smoke is still pending

Do not jump straight to full SaaS before stabilizing:

1. live upload implementation after a real ingestion API exists
2. real cloud ingestion service and real-cloud adapters with provider-specific endpoint policies

## Branch and release guidance

The hackathon freeze is over, but `main` remains protected:

- Start substantive work on a feature branch.
- Open PRs into `main` and wait for required checks.
- Direct pushes to `main` are blocked by branch protection.
- After applying CodeRabbit review feedback, do not push solely to trigger another CodeRabbit review loop; fold those fixes into the next substantive batch unless the user explicitly approves a review-response push.
- Do not tag releases or publish product releases without explicit owner approval.
