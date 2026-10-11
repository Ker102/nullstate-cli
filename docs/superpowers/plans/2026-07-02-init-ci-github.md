# Init CI GitHub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `nullstate init-ci github` to bootstrap a GitHub Actions workflow and starter policy for open-source users.

**Architecture:** Keep generation local and deterministic. A small module renders the checked-in enforcing workflow template with selected scenario/IaC/fail-threshold values and writes a default or scenario-scoped policy file.

**Tech Stack:** Python 3.11+, Typer, unittest, existing policy module.

---

### Task 1: CI Bootstrap Module

**Files:**
- Create: `src/nullstate/ci_templates.py`
- Create: `tests/test_ci_templates.py`

- [ ] **Step 1: Write failing tests**

Tests should assert:
- `render_github_workflow()` replaces scenario, IaC path, policy path, baseline path, and severity.
- `write_github_ci_files()` writes `.github/workflows/nullstate.yml`.
- policy file is created with a scenario preset.
- existing files are not overwritten unless `force=True`.

- [ ] **Step 2: Run failing tests**

Run: `python -m unittest tests.test_ci_templates -v`
Expected: FAIL because `nullstate.ci_templates` does not exist.

- [ ] **Step 3: Implement module**

Implement:
- `render_github_workflow(...)`
- `write_github_ci_files(...)`
- guarded overwrite behavior

- [ ] **Step 4: Run focused tests**

Run: `python -m unittest tests.test_ci_templates -v`
Expected: PASS.

### Task 2: CLI Command

**Files:**
- Modify: `src/nullstate/cli.py`
- Modify: `tests/test_cli.py` or `tests/test_ci_templates.py`

- [ ] **Step 1: Write failing CLI test**

Assert:
- `python -m nullstate init-ci github --output <tmp>/.github/workflows/nullstate.yml --policy-output <tmp>/nullstate-policy.json --scenario aws-public-s3 --iac-path examples/aws-public-s3` exits 0.
- workflow and policy files exist.

- [ ] **Step 2: Implement CLI**

Add `init_ci` command with `provider=github`.

- [ ] **Step 3: Run focused tests**

Run: `python -m unittest tests.test_ci_templates tests.test_cli -v`
Expected: PASS.

### Task 3: Docs and Validation

**Files:**
- Modify: `README.md`
- Modify: `docs/quickstart-10-minutes.md`
- Modify: `docs/ci-cd.md`
- Modify: `docs/progress.md`
- Modify: `docs/handoff.md`

- [ ] **Step 1: Document bootstrap command**

Show:

```bash
nullstate init-ci github
```

- [ ] **Step 2: Validate**

Run:
- `git diff --check`
- `python -m ruff check src tests`
- `python -m mypy src`
- `python -m unittest discover -s tests -v`

- [ ] **Step 3: Commit**

Commit message:

```bash
git commit -m "feat: add GitHub Actions bootstrap command"
```
