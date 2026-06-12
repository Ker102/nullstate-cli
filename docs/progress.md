# Productization Progress

This file tracks roadmap progress after the hackathon freeze. Keep updates brief, factual, and tied to branch commits so the case study can reconstruct what changed and why.

## Current Branch

- Branch: `feature/red-agent-runner`
- Rule: do not merge or push changes to `main`
- Remote policy: feature-branch pushes are allowed for checkpointing

## Checkpoints

### 2026-06-11

- `43af5fc feat: add LLM provider presets`
  - Added provider presets for Google AI Studio / Gemini, Claude compatibility, custom, and generic OpenAI-compatible endpoints.
  - Kept self-hosted AMD/vLLM/SGLang endpoint support through explicit base URLs.
- `8213524 feat: add SARIF export command`
  - Added `nullstate sarif`.
  - Emits SARIF 2.1.0 from run findings for CI and code-scanning upload.
- `8f07d3f ci: add nullstate SARIF workflow`
  - Added `.github/workflows/nullstate-sarif.yml`.
  - Runs an offline scenario, exports SARIF, uploads to GitHub code scanning, and stores run artifacts.
- `33afe91 feat: add CI mode exit summary`
  - Added `nullstate run --ci`.
  - Writes `ci-summary.json`.
  - Exits with code `2` when findings meet or exceed `--fail-on-severity`.
- `feat: add upload dry-run plan` (this checkpoint)
  - Added `nullstate upload --dry-run`.
  - Refreshes `run-bundle.json` and writes `upload-plan.json`.
  - Records endpoint intent, bundle checksum, artifact count, and token presence without network calls or token values.
- `feat: add CI baseline comparison` (this checkpoint)
  - Added `nullstate baseline`.
  - Added `nullstate run --ci --baseline-file`.
  - CI severity thresholds are evaluated against new findings only when a baseline is supplied.
- `feat: add red-tool policy scaffold` (this checkpoint)
  - Added `nullstate policy init`.
  - Added optional `nullstate run --policy-file`.
  - Enforces allowed target classifications and command policy IDs before `attack.py` execution.
- `feat: add JSON policy result export` (this checkpoint)
  - Added `nullstate policy-result`.
  - Writes `policy-result.json` for an existing run.
  - Reuses severity threshold and optional baseline comparison without re-running a scenario.

### 2026-06-12

- `feat: add evidence integrity manifest` (this checkpoint)
  - Added `nullstate evidence-manifest`.
  - Writes `evidence-manifest.json` with SHA-256 hashes and file sizes for shareable run artifacts.
  - Excludes copied workspaces, Terraform internals, Python caches, and the manifest file itself.
  - Records signing as `unsigned`; cryptographic signing remains future hardening.
- `feat: add evidence manifest verification` (this checkpoint)
  - Added `nullstate evidence-verify`.
  - Writes `evidence-verification.json` with pass/fail status, checked artifact count, and mismatch details.
  - Exits with code `2` when a manifest-listed artifact is missing or changed.
  - Keeps cryptographic signature verification as future hardening.
- `feat: add policy scenario backend allowlists` (this checkpoint)
  - Extended generated policy files with `allowed_scenarios` and `allowed_backends`.
  - `run --policy-file` now enforces scenario, backend, target classification, and command policy ID before generated `attack.py` execution.
  - Older policy files without scenario/backend fields remain valid and keep enforcing their existing fields.
- `feat: add policy command controls` (this checkpoint)
  - Extended generated policy files with allowed stages, generated `attack.py` flags, timeout ceilings, and output-size ceilings.
  - `run --policy-file` now enforces command controls before generated `attack.py` execution.
  - Older policy files without command-control fields remain valid and keep enforcing their existing fields.
- `feat: add policy validation command` (this checkpoint)
  - Added `nullstate policy validate`.
  - Writes optional `policy-validation.json` for CI evidence.
  - Exits with code `2` when the policy file is malformed or invalid.
- `fix: harden policy and evidence verification` (local checkpoint)
  - Reviewed the latest CodeRabbit findings and accepted the verified fail-closed issues.
  - `nullstate policy-result` now fails closed when `findings.json` is missing, malformed, or not a list.
  - `nullstate evidence-verify` now fails copied/wrong manifests whose declared run identity does not match the target run.
  - Malformed evidence manifests now surface as CLI parameter errors instead of Python tracebacks.
  - This checkpoint is intentionally local until the next substantive batch push, to avoid triggering a CodeRabbit review loop over review-response fixes.

## In Progress

- No active implementation slice at this checkpoint.

## Blocked

- Live LocalStack Azure validation:
  - Blocker: LocalStack account/license does not currently have Azure Emulator entitlement.
  - Do not keep retrying because the Azure image is large and disk space is limited.

## Next Candidates

- Per-scenario command policy presets for different generated probes.
- Upload dry-run to live upload transition once an ingestion API exists.
- Cryptographic signing and signature verification for `evidence-manifest.json`.
