# Nullstate Project Handoff

Last updated: 2026-06-01

## Read this first

The repository is currently under a hackathon freeze rule:

- Do not merge anything into `main`.
- Do not push new work unless the user explicitly asks.
- It is safe to keep working locally on feature branches and make local commits.
- Current active branch: `feature/red-agent-runner`.
- Current local state at handoff: branch has local-only commits; run `git status --short --branch` for the exact ahead count.

Recent local-only commits:

```text
7117340 feat: add run bundles and local dashboard
55775a7 feat: add attack manifest foundation
```

These two commits have not been pushed.

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
- Portable run bundle:
  - `nullstate bundle`
  - writes `runs/<id>/run-bundle.json`
- Free local HTML dashboard:
  - `nullstate dashboard`
  - writes `runs/<id>/dashboard.html`

Important limitation:

- The constrained red runner is real, but AWS/Azure `attack.py` scripts are still shallow probes.
- The before/after success verdict is still mostly deterministic via `simulate_attack()`.
- Enterprise-grade exploit validation still requires real sandbox object/blob read probes.

## Important docs

Start here:

- `README.md`
- `docs/technical-walkthrough.md`
- `docs/case-study.md`
- `docs/enterprise-roadmap.md`
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
63 tests OK
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

## Where to continue

Next highest-value feature:

```text
Real AWS S3 runtime exploit probe
```

Current AWS example only disables public access block. That is risky but not sufficient to prove anonymous reads by itself.

Next implementation should:

1. Add a Terraform evidence object to `examples/aws-public-s3/main.tf`.
2. Add public read configuration if LocalStack supports it reliably.
3. Update `attack.py` AWS template to try anonymous HTTP GET against LocalStack S3.
4. Use `attack-manifest.json` resource hints for bucket/object candidates.
5. Log stdout with candidate URL, HTTP status, and body excerpt.
6. Update report language to distinguish:
   - observed runtime exploit evidence
   - deterministic simulation
   - inconclusive emulator result
7. Keep safety boundaries:
   - local endpoints only
   - no arbitrary shell
   - no real cloud credentials
   - strict timeout

Recommended next tests:

- Unit test AWS attack script template parses manifest and builds candidate URLs.
- Offline run still passes.
- LocalStack live AWS run proves whether public object read can be observed.
- Report includes runtime command evidence.

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
