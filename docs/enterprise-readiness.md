# Enterprise Readiness

This checklist tracks the controls needed to move `nullstate` from a local hackathon prototype into an enterprise DevSecOps tool. It separates what is already enforced from what should be added before paid team, cloud, or self-hosted use.

## Current Controls

| Control | Status | Evidence |
|---|---|---|
| Deterministic finding source of truth | implemented | detectors in `src/nullstate/findings.py` |
| Deterministic remediation | implemented | patch logic in `src/nullstate/remediation.py` |
| Copied run workspace | implemented | original IaC directory is not mutated |
| Constrained red runner | implemented | only run-directory `attack.py` executes |
| Manifest-scoped probe inputs | implemented | `attack-manifest.json` carries resource hints |
| Runtime evidence logging | implemented | `red-tool` events include command output and timing |
| Local target enforcement | implemented | attack runner rejects non-local HTTP targets by default |
| Attack artifact hashes | implemented | `red-tool` events include script and manifest SHA-256 values |
| Output truncation metadata | implemented | `red-tool` events identify truncated stdout/stderr |
| Non-destructive artifact scrubber | implemented | `nullstate scrub` copies and redacts run artifacts |
| Upload scrub preflight | implemented | `nullstate upload --dry-run` records scrub readiness and warns on raw runs |
| Report evidence classification | implemented | reports distinguish runtime, inconclusive, and offline simulation |
| Local dashboard and bundle | implemented | `nullstate dashboard`, `nullstate bundle`, and `docs/schemas/run-bundle.schema.json` |
| Red-tool policy scaffold | implemented | `nullstate policy init`, scenario presets, and `run --policy-file` enforce scenario, backend, stage, argument, target, command, timeout, and output fields |
| Policy validation artifact | implemented | `nullstate policy validate` writes optional `policy-validation.json` |
| Evidence integrity manifest | implemented | `nullstate evidence-manifest` writes SHA-256 artifact inventory with optional HMAC evidence signing |
| Evidence manifest verification | implemented | `nullstate evidence-verify` detects missing or changed manifest artifacts, copied manifests, and invalid HMAC signatures |
| Release provenance | implemented | tagged release workflow writes `release-manifest.json` and creates GitHub artifact attestations for `dist/*` |
| Release SBOM | implemented | tagged release workflow installs the built wheel into a clean environment, validates `sbom.spdx.json` locally and with SPDX tools, and attests it with GitHub artifact attestations |
| Keyless release signing | implemented | tagged release workflow signs primary release assets with Sigstore through GitHub OIDC |
| Release dry-run rehearsal | implemented | manual `workflow_dispatch` runs release validation without creating a GitHub release |
| Versioned remediation rules | implemented | `remediation.json` records the ruleset version, scenario, changed files, and applied rule IDs |

## Required Before Enterprise Claims

### Local-Only Enforcement

Default runtime targets remain local:

- `offline://...`
- `local://...`
- `127.0.0.1`
- `localhost`
- `localhost.localstack.cloud`

The attack runner rejects non-local HTTP targets by default. Any real cloud mode requires the explicit `--allow-live-cloud` flag, default off. The run records operator approval in `events.jsonl`, and red-tool events record whether the live-cloud gate was enabled for the executed command.

### Command Allowlist Policy

The red runner should stay template-based. A scenario policy should define:

- allowed scenario names
- allowed backend names
- allowed generated script name
- allowed CLI arguments
- maximum timeout
- maximum stdout/stderr bytes
- allowed target URL schemes and host patterns

The model may explain an attack path, but it should not create arbitrary shell commands.

`nullstate policy init` creates the first JSON policy scaffold. `nullstate policy init --scenario <name>` creates a narrower preset for one known scenario/backend pair, which is useful for CI jobs that should not allow every scaffolded scenario. `nullstate policy validate` checks that scaffold before CI runs or local scenarios. `nullstate run --policy-file` enforces allowed scenario names, backend names, stages, generated `attack.py` flags, target classifications, command policy IDs, timeout ceilings, and output-size ceilings before `attack.py` can execute. This is intentionally narrower than a full policy engine, but it creates the product contract for future richer per-scenario command policies.

### Event Schema Hardening

`red-tool` events include the first set of audit metadata:

- `schema_version`
- `command_policy_id`
- `attack_script_sha256`
- `manifest_sha256`

They should also add richer policy fields over time. Current events already include:

- `stdout_truncated`
- `stderr_truncated`

Current events also include:

- `live_cloud_allowed`
- richer `target_classification` values, including `external-http` when the live-cloud gate is explicitly enabled

These fields make evidence reproducible and easier to audit in CI, support, and compliance workflows.

`nullstate evidence-manifest` adds a run-level artifact inventory for support, case-study, and future ingestion workflows. It records SHA-256 hashes and file sizes for shareable artifacts while excluding copied workspaces, Terraform internals, Python caches, the manifest file itself, and verification output. `--signing-key-env` adds a shared-key HMAC-SHA256 evidence signature using a secret from the environment; the key value is never written to the manifest. `nullstate evidence-verify` recomputes recorded hashes and writes `evidence-verification.json`, exiting with code `2` when a listed artifact is missing, changed, tied to a different declared run identity, or has an invalid signature.

Tagged package releases write `release-manifest.json` with SHA-256 digests and `sbom.spdx.json` from the built wheel installed into a clean environment. The workflow validates the SBOM with local structural checks and `pyspdxtools` before manifest generation and attestation. GitHub artifact attestations cover both build provenance and the SPDX SBOM predicate for `dist/*`. Sigstore keyless signing publishes adjacent `.sigstore.json` bundles for the wheel, sdist, SBOM, and release manifest. This is release supply-chain provenance; it is separate from run evidence HMAC signatures.

The same release workflow can be run manually with `dry_run=true` before tagging. Manual dry runs exercise the release build, validation, attestation, signing, and signature-bundle checks while skipping GitHub release creation.

Each run also writes `remediation.json` beside `remediation.patch`. The JSON artifact records the deterministic remediation ruleset version, scenario, changed flag, changed files, and rule IDs applied by the remediation engine. Reports and run bundles include the same metadata so support, CI, and future ingestion workflows can tie a remediation patch back to the exact rule contract.

`run-bundle.json` is now schema-addressed and validated locally. The generated bundle includes a `$schema` field pointing at `docs/schemas/run-bundle.schema.json`, and `nullstate bundle` fails before writing if the required top-level contract is malformed.

### Artifact Scrubbing

Before publishing, uploading, or attaching run bundles, run `nullstate scrub`. The scrubber writes a sanitized copy and redacts:

- LocalStack auth tokens
- model endpoint keys
- cloud account IDs
- Azure tenant and subscription IDs
- private endpoints and IP maps
- Terraform state values
- provider credentials
- raw model prompts if they contain customer context

The scrubber writes `scrub-report.json`, listing which files were processed and which redaction rules matched.

`nullstate upload --dry-run` now checks for `scrub-report.json` in the selected run directory and records `preflight.scrub` in `upload-plan.json`. Raw runs remain allowed for local planning, but the plan marks them `upload_recommended: false` and prints a warning.

### Evidence Classification

Enterprise reports should avoid overclaiming. Use these labels:

- `runtime exploit observed`: command output proves object/blob access.
- `runtime probe did not observe exploit`: command reached the target and access was blocked or unavailable after remediation.
- `runtime probe inconclusive`: emulator, route, or runtime support prevented proof.
- `offline deterministic simulation`: no live runtime probe was attempted.

If a report says "exploited", it should include observed command evidence or explicitly say it is an offline deterministic simulation.

## Near-Term Readiness Tasks

1. Run live LocalStack Azure validation and document emulator-specific limitations.
2. Add live-cloud adapters only after endpoint allowlists and approval workflows are specified.

## Commercial Boundary

The open-source CLI can keep local/offline runs, LocalStack probes, reports, bundles, and a single-user dashboard. Paid team or enterprise products should focus on controls that require governance:

- centralized evidence history
- RBAC and audit logs
- policy-as-code command allowlists
- managed model calls
- support bundle workflow
- compliance exports
- scheduled scans and alerts
- private deployment support
