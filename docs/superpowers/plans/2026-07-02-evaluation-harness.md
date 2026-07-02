# Evaluation Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `nullstate eval` so the project can generate case-study metrics from repeatable benchmark suites.

**Architecture:** A JSON eval suite lists scenario runs, expected findings, expected before/after attack statuses, and run options. The CLI executes each case through `python -m nullstate run`, summarizes each generated run with the existing run-summary contract, and writes `eval-results.json` plus `eval-report.md`.

**Tech Stack:** Python 3.11+, Typer, subprocess, unittest, JSON schema documentation.

---

### Task 1: Eval Suite Contract

**Files:**
- Create: `src/nullstate/evaluation.py`
- Create: `tests/test_evaluation.py`
- Create: `docs/schemas/eval-suite.schema.json`
- Create: `examples/eval/iac-security-regression.json`

- [ ] **Step 1: Write failing tests**

Tests should assert:
- valid example suite loads.
- missing fields produce validation errors.
- suite schema document matches the module schema ID.

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest tests.test_evaluation -v`
Expected: FAIL because `nullstate.evaluation` does not exist.

- [ ] **Step 3: Implement suite loader and validator**

Implement:
- `EVAL_SUITE_SCHEMA_ID`
- `EVAL_RESULTS_SCHEMA_ID`
- `load_eval_suite(path)`
- `validate_eval_suite(payload)`

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_evaluation -v`
Expected: PASS for contract tests after implementation.

### Task 2: Eval Runner

**Files:**
- Modify: `src/nullstate/evaluation.py`
- Modify: `tests/test_evaluation.py`

- [ ] **Step 1: Write failing test for offline eval run**

Create a temporary output directory, run the example suite with one offline AWS case, and assert:
- `eval-results.json` exists.
- `eval-report.md` exists.
- case status is `passed`.
- metrics include duration, finding count, highest severity, attack before/after, token totals, and artifact count.

- [ ] **Step 2: Run test to verify failure**

Run: `python -m unittest tests.test_evaluation -v`
Expected: FAIL because the runner is missing.

- [ ] **Step 3: Implement runner**

Implement:
- `run_eval_suite(suite_path, output_dir)`
- `write_eval_report(results, output_dir)`
- command execution through current Python executable and `python -m nullstate run`
- per-case summary through `build_run_summary`

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_evaluation -v`
Expected: PASS.

### Task 3: CLI and Docs

**Files:**
- Modify: `src/nullstate/cli.py`
- Modify: `tests/test_cli.py` or `tests/test_evaluation.py`
- Modify: `README.md`
- Modify: `docs/case-study.md`
- Modify: `docs/progress.md`
- Modify: `docs/handoff.md`

- [ ] **Step 1: Add CLI tests**

Assert `python -m nullstate eval run examples/eval/iac-security-regression.json --output-dir <tmp>` exits 0 and writes results.

- [ ] **Step 2: Implement CLI**

Add `eval_app` with:
- `nullstate eval run <suite.json> --output-dir eval-runs`

- [ ] **Step 3: Update docs**

Document the case-study metrics workflow:
- `nullstate eval run examples/eval/iac-security-regression.json`
- inspect `eval-results.json`
- inspect `eval-report.md`

- [ ] **Step 4: Validate**

Run:
- `git diff --check`
- `python -m ruff check src tests`
- `python -m mypy src`
- `python -m unittest discover -s tests -v`

- [ ] **Step 5: Commit**

Commit message:

```bash
git commit -m "feat: add evaluation metrics harness"
```
