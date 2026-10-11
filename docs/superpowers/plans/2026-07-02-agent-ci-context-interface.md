# Agent CI Context Interface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Nullstate easier for coding agents and GitHub Actions to consume by adding a compact run summary command and a safe local cloud-context manifest contract.

**Architecture:** Add deterministic modules only: `summary.py` reads existing run artifacts and emits one stable JSON object; `cloud_context.py` validates user-supplied read-only cloud context manifests without calling cloud APIs. CLI commands expose these contracts without adding live credentials or production access.

**Tech Stack:** Python 3.11+, Typer, Rich, unittest, JSON schema documentation.

---

### Task 1: Run Summary Contract

**Files:**
- Create: `src/nullstate/summary.py`
- Create: `tests/test_summary.py`
- Modify: `src/nullstate/cli.py`
- Create: `docs/schemas/run-summary.schema.json`

- [ ] **Step 1: Write failing tests**

Tests should create a minimal run directory with `findings.json`, `events.jsonl`, `metrics.json`, `report.md`, and selected optional artifacts. They should assert that `build_run_summary()` returns:
- run ID
- status
- finding count
- highest severity
- before/after attack status
- artifact paths
- model token totals
- limitations

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest tests.test_summary -v`
Expected: FAIL because `nullstate.summary` does not exist.

- [ ] **Step 3: Implement minimal summary builder**

Implement:
- `RUN_SUMMARY_SCHEMA_ID`
- `build_run_summary(run_dir)`
- `validate_run_summary(payload)`
- deterministic severity ordering
- permissive missing-artifact handling with limitations

- [ ] **Step 4: Add CLI command**

Add:
- `nullstate summary [run_id]`
- `--json`
- `--runs-dir`

- [ ] **Step 5: Run focused tests**

Run: `python -m unittest tests.test_summary tests.test_cli -v`
Expected: PASS.

### Task 2: Local Cloud Context Manifest Contract

**Files:**
- Create: `src/nullstate/cloud_context.py`
- Create: `tests/test_cloud_context.py`
- Modify: `src/nullstate/cli.py`
- Create: `docs/schemas/cloud-context.schema.json`
- Create: `examples/cloud-context/aws-readonly-context.json`

- [ ] **Step 1: Write failing tests**

Tests should assert:
- example context loads and validates.
- malformed context reports missing provider/account/resource fields.
- graph summary counts providers, accounts, identities, resources, public endpoints, and sensitive resources.

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest tests.test_cloud_context -v`
Expected: FAIL because `nullstate.cloud_context` does not exist.

- [ ] **Step 3: Implement local manifest validator**

Implement:
- `CLOUD_CONTEXT_SCHEMA_ID`
- `load_cloud_context(path)`
- `validate_cloud_context(payload)`
- `build_context_summary(payload)`

- [ ] **Step 4: Add CLI commands**

Add `context_app` with:
- `nullstate context validate <context.json>`
- `nullstate context summary <context.json> --json`

- [ ] **Step 5: Run focused tests**

Run: `python -m unittest tests.test_cloud_context tests.test_cli -v`
Expected: PASS.

### Task 3: Documentation and Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/product-validation-model.md`
- Modify: `docs/case-study.md`
- Modify: `docs/progress.md`
- Modify: `docs/handoff.md`

- [ ] **Step 1: Document agent/CI workflow**

Show how a coding agent or GitHub Actions job can call:
- `nullstate run`
- `nullstate summary --json`
- `nullstate context validate`

- [ ] **Step 2: Update case-study proof section**

Describe this as an agent-consumable evidence interface rather than a scanner-only UX.

- [ ] **Step 3: Run validation**

Run:
- `git diff --check`
- `python -m ruff check src tests`
- `python -m mypy src`
- `python -m unittest discover -s tests -v`

- [ ] **Step 4: Commit**

Commit message:

```bash
git commit -m "feat: add agent and CI evidence contracts"
```
