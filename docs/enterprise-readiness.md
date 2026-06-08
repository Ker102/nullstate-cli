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
| Report evidence classification | implemented | reports distinguish runtime, inconclusive, and offline simulation |
| Local dashboard and bundle | implemented | `nullstate dashboard` and `nullstate bundle` |

## Required Before Enterprise Claims

### Local-Only Enforcement

Default runtime targets should remain local:

- `offline://...`
- `local://...`
- `127.0.0.1`
- `localhost`
- `localhost.localstack.cloud`

Any future real cloud mode should require an explicit `--allow-live-cloud` flag, default off. The run should record the operator approval, target hostname, scenario, backend, and timestamp in `events.jsonl`.

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

### Event Schema Hardening

`red-tool` events should include:

- `schema_version`
- `command_policy_id`
- `attack_script_sha256`
- `manifest_sha256`
- `stdout_truncated`
- `stderr_truncated`
- `target_classification`

These fields make evidence reproducible and easier to audit in CI, support, and compliance workflows.

### Artifact Scrubbing

Before publishing, uploading, or attaching run bundles, an artifact scrubber should redact:

- LocalStack auth tokens
- model endpoint keys
- cloud account IDs
- Azure tenant and subscription IDs
- private endpoints and IP maps
- Terraform state values
- provider credentials
- raw model prompts if they contain customer context

The scrubber should write a scrub report that lists which files were processed and which redaction rules matched.

### Evidence Classification

Enterprise reports should avoid overclaiming. Use these labels:

- `runtime exploit observed`: command output proves object/blob access.
- `runtime probe did not observe exploit`: command reached the target and access was blocked or unavailable after remediation.
- `runtime probe inconclusive`: emulator, route, or runtime support prevented proof.
- `offline deterministic simulation`: no live runtime probe was attempted.

If a report says "exploited", it should include observed command evidence or explicitly say it is an offline deterministic simulation.

## Near-Term Readiness Tasks

1. Add local-target validation around attack target URLs.
2. Add `schema_version` and script hashes to `red-tool` events.
3. Add stdout/stderr truncation metadata.
4. Add artifact scrubber command and tests.
5. Add `--allow-live-cloud` as a future disabled gate before any real cloud adapter work.
6. Run live LocalStack Azure validation and document emulator-specific limitations.

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
