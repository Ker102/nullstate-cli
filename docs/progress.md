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
- `fix: make SARIF upload and CodeQL fixtures CI-clean` (local checkpoint)
  - Investigated PR #24 failing checks with `gh`.
  - Fixed GitHub SARIF upload validation by moving finding logical locations under SARIF result locations.
  - Reworked scrubber test fixture values/naming so CodeQL does not treat the test artifact as clear-text secret storage.
  - GitHub has not re-run these checks yet because the fixes remain local on this branch.
- `feat: add scenario policy presets` (this checkpoint)
  - Added `nullstate policy init --scenario <name>`.
  - Scenario presets narrow generated `allowed_scenarios` and `allowed_backends` to one known scenario/backend pair.
  - Plain `nullstate policy init` still writes the broad starter policy for compatibility.
  - Unknown scenario names fail before writing a policy file.
- `feat: add evidence manifest signing` (this checkpoint)
  - Added optional `--signing-key-env` support to `nullstate evidence-manifest` and `nullstate evidence-verify`.
  - Signed manifests use HMAC-SHA256 with a key read from the environment; key values are not written to artifacts.
  - Verification reports signature status and exits `2` for missing, unavailable, invalid, or tampered signatures when signature checking is requested or required.
  - Public-key package/release provenance remains a separate future hardening item.
- `feat: add live cloud approval gate` (this checkpoint)
  - Added default-off `--allow-live-cloud` to `nullstate run`.
  - Non-local HTTP(S) attack probe targets remain rejected unless the gate is explicitly enabled.
  - Start events record operator approval, and red-tool events record `live_cloud_allowed` plus `external-http` classification when applicable.
  - Attack command timeouts now return structured red-tool evidence with return code `124` instead of a traceback.
  - Built-in scenarios still resolve to local/offline targets; real cloud adapters remain future work.
- `ci: add release provenance attestations` (this checkpoint)
  - Hardened the tag release workflow with GitHub artifact attestation permissions.
  - Added `release-manifest.json` with SHA-256 digests and sizes for built wheel/sdist artifacts.
  - Added `actions/attest@v4` provenance attestation for `dist/*` release assets.
- `ci: add release sbom attestation` (this checkpoint)
  - Added `sbom.spdx.json` generation to the tag release workflow.
  - The SBOM records the root package and declared runtime dependencies in SPDX 2.3 JSON.
  - Added a GitHub artifact attestation for the SBOM predicate over `dist/*`.
  - Documented package provenance and SBOM attestation verification commands.
- `feat: add upload scrub preflight` (this checkpoint)
  - Added `preflight.scrub` metadata to `upload-plan.json`.
  - Raw runs are marked `upload_recommended: false` and produce a CLI warning.
  - Scrubbed run copies with `scrub-report.json` are marked `upload_recommended: true`.
  - Live upload remains blocked until an ingestion API exists.
- `docs: align productization status wording` (this checkpoint)
  - Removed older future-tense scrubber and release-provenance wording from security, case-study, failure-mode, and README status docs.
  - Kept future scope focused on broader redaction rules, richer SBOMs, package signing, and live ingestion.
- `ci: generate sbom from installed wheel` (this checkpoint)
  - Release workflow now installs the built wheel into `.sbom-venv` before generating `sbom.spdx.json`.
  - SBOM packages now come from installed runtime distributions and include package versions.
  - SBOM dependency relationships are derived from installed package metadata when both sides are present.
- `ci: validate release sbom` (this checkpoint)
  - Added release workflow validation for `dist/sbom.spdx.json` before manifest generation and attestation.
  - Validation checks SPDX version, required package fields, root package presence, packaging-tool exclusion, and root-package relationships.
- `ci: add keyless release signing` (this checkpoint)
  - Added Sigstore keyless signing for the wheel, sdist, SBOM, and release manifest.
  - The release workflow now validates adjacent `.sigstore.json` bundles before creating the GitHub release.
  - Signing uses GitHub OIDC and does not require long-lived signing keys.
- `docs: add release signature verification examples` (this checkpoint)
  - Documented Cosign verification for release wheel signatures and adjacent `.sigstore.json` bundles.
- `fix: add SARIF physical locations` (this checkpoint)
  - GitHub Code Scanning rejected SARIF without `physicalLocation`.
  - SARIF results now point to the run `findings.json` artifact while preserving the Terraform resource as a logical location.
- `ci: add spdx tools sbom validation` (this checkpoint)
  - Added release workflow validation with `spdx-tools==0.8.5` and `pyspdxtools`.
  - SPDX tools run after local SBOM structure checks and before release manifest generation.
- `ci: add release dry-run rehearsal` (this checkpoint)
  - Added manual `workflow_dispatch` support to the release workflow.
  - Manual release dry runs execute build, validation, attestation, signing, and signature-bundle checks without creating a GitHub release.
  - The GitHub release creation step now runs only on tag pushes.
- `docs: add first release verification checklist` (this checkpoint)
  - Added a runbook checklist for the first tagged release.
  - Captures PR check review, manual release dry-run rehearsal, release inspection, GitHub attestation verification, and Sigstore bundle verification.
  - Keeps the freeze rule explicit: no tagging, release publishing, or `main` updates until approved.

## In Progress

- No active implementation slice at this checkpoint.

## Blocked

- Live LocalStack Azure validation:
  - Blocker: LocalStack account/license does not currently have Azure Emulator entitlement.
  - Do not keep retrying because the Azure image is large and disk space is limited.

## Next Candidates

- Upload dry-run to live upload transition once an ingestion API exists.
- Live LocalStack Azure validation once the account has Azure Emulator entitlement.
