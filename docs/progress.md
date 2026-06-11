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

## In Progress

- No active implementation slice at this checkpoint.

## Blocked

- Live LocalStack Azure validation:
  - Blocker: LocalStack account/license does not currently have Azure Emulator entitlement.
  - Do not keep retrying because the Azure image is large and disk space is limited.

## Next Candidates

- JSON policy output beyond `ci-summary.json`.
- Policy file for allowed targets and command templates.
- Upload dry-run to live upload transition once an ingestion API exists.
