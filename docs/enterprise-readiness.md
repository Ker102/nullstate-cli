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
| Report evidence classification | implemented | reports distinguish runtime, inconclusive, and offline simulation |
| Local dashboard and bundle | implemented | `nullstate dashboard` and `nullstate bundle` |
| Red-tool policy scaffold | implemented | `nullstate policy init`, scenario presets, and `run --policy-file` enforce scenario, backend, stage, argument, target, command, timeout, and output fields |
| Policy validation artifact | implemented | `nullstate policy validate` writes optional `policy-validation.json` |
| Evidence integrity manifest | implemented | `nullstate evidence-manifest` writes SHA-256 artifact inventory with explicit unsigned status |
| Evidence manifest verification | implemented | `nullstate evidence-verify` detects missing or changed manifest artifacts and copied manifests for another run |

## Required Before Enterprise Claims

### Local-Only Enforcement

Default runtime targets remain local:

- `offline://...`
- `local://...`
- `127.0.0.1`
- `localhost`
- `localhost.localstack.cloud`

The attack runner rejects non-local HTTP targets by default. Any future real cloud mode should require an explicit `--allow-live-cloud` flag, default off. The run should record the operator approval, target hostname, scenario, backend, and timestamp in `events.jsonl`.

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

Future event metadata should add:

- richer `target_classification` values for future real-cloud gates

These fields make evidence reproducible and easier to audit in CI, support, and compliance workflows.

`nullstate evidence-manifest` adds a run-level artifact inventory for support, case-study, and future ingestion workflows. It records SHA-256 hashes and file sizes for shareable artifacts while excluding copied workspaces, Terraform internals, Python caches, the manifest file itself, and verification output. `nullstate evidence-verify` recomputes recorded hashes and writes `evidence-verification.json`, exiting with code `2` when a listed artifact is missing, changed, or tied to a different declared run identity. The current manifest is deliberately marked `unsigned`; enterprise signing should add a real signature, signing key identity, and verification workflow.

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

### Evidence Classification

Enterprise reports should avoid overclaiming. Use these labels:

- `runtime exploit observed`: command output proves object/blob access.
- `runtime probe did not observe exploit`: command reached the target and access was blocked or unavailable after remediation.
- `runtime probe inconclusive`: emulator, route, or runtime support prevented proof.
- `offline deterministic simulation`: no live runtime probe was attempted.

If a report says "exploited", it should include observed command evidence or explicitly say it is an offline deterministic simulation.

## Near-Term Readiness Tasks

1. Add `--allow-live-cloud` as a future disabled gate before any real cloud adapter work.
2. Run live LocalStack Azure validation and document emulator-specific limitations.
3. Add cryptographic signing and signature verification for `evidence-manifest.json`.

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
