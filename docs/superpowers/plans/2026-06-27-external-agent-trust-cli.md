# External Agent Trust CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an initial deterministic `nullstate agent` command family that validates external AI-agent trust manifests and reports posture/blast-radius risk.

**Architecture:** Keep the implementation local-first and deterministic. A JSON manifest describes an external agent runtime, identities, delegated users, tools, posture evidence, and reachable resources; `src/nullstate/agent_trust.py` validates and summarizes it without requiring cloud APIs.

**Tech Stack:** Python 3.11+, Typer, Rich, unittest, JSON schema documentation.

---

### Task 1: Agent Trust Manifest Contract

**Files:**
- Create: `src/nullstate/agent_trust.py`
- Create: `tests/test_agent_trust.py`
- Create: `docs/schemas/external-agent-manifest.schema.json`
- Create: `examples/agent-trust/external-agent-manifest.json`

- [ ] **Step 1: Write failing unit tests**

Create tests that assert:
- a valid example manifest loads without errors.
- missing required top-level fields produce validation errors.
- unknown or stale runtime evidence prevents a passing posture result.
- delegated user + agent permissions are both represented in blast radius.

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest tests.test_agent_trust -v`
Expected: FAIL because `nullstate.agent_trust` does not exist.

- [ ] **Step 3: Implement minimal analyzer**

Implement:
- `AGENT_MANIFEST_SCHEMA_ID`
- `load_agent_manifest(path)`
- `validate_agent_manifest(payload)`
- `build_posture_report(payload, now=None)`
- `build_blast_radius_report(payload)`

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m unittest tests.test_agent_trust -v`
Expected: PASS.

### Task 2: CLI Commands

**Files:**
- Modify: `src/nullstate/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Add subprocess tests for:
- `python -m nullstate agent posture verify examples/agent-trust/external-agent-manifest.json`
- `python -m nullstate agent blast-radius examples/agent-trust/external-agent-manifest.json`

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest tests.test_cli -v`
Expected: FAIL because `agent` commands are missing.

- [ ] **Step 3: Implement CLI subcommands**

Add `agent_app = typer.Typer(...)`, register it on `app`, and implement:
- `agent posture verify`
- `agent blast-radius`

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m unittest tests.test_cli tests.test_agent_trust -v`
Expected: PASS.

### Task 3: Documentation and Handoff

**Files:**
- Modify: `README.md`
- Modify: `docs/progress.md`
- Modify: `docs/handoff.md`
- Modify: `docs/product-validation-model.md`

- [ ] **Step 1: Document command purpose**

Explain that `agent` commands are deterministic preview commands for external AI-agent trust validation, not a replacement for cloud inventory collectors.

- [ ] **Step 2: Update handoff**

Record branch, files, tests, and next implementation slice.

- [ ] **Step 3: Validate**

Run:
- `git diff --check`
- `python -m ruff check src tests`
- `python -m mypy src`
- `python -m unittest tests.test_agent_trust tests.test_cli -v`
- `python -m unittest discover -s tests -v`
