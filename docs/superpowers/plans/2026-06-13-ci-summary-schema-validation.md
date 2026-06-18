# CI Summary Schema Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a versioned JSON Schema contract for `ci-summary.json` and validate generated CI summaries before writing them.

**Architecture:** Keep the CI decision logic unchanged while strengthening the generated artifact contract. Add a `$schema` pointer to generated CI summaries, document the contract under `docs/schemas/`, and validate the payload inside the CI summary builder before the CLI writes it. `nullstate run --ci` should print an explicit validation status.

**Tech Stack:** Python 3.11+, Typer CLI, JSON artifacts, `unittest`.

---

### Task 1: Pin Expected CI Summary Contract

**Files:**
- Modify: `tests/test_cli_ci.py`

- [x] **Step 1: Write failing tests**

Add imports:

```python
from nullstate.ci import CI_SUMMARY_SCHEMA_ID, validate_ci_summary
```

In the existing CI summary test, assert:

```python
self.assertEqual(summary["$schema"], CI_SUMMARY_SCHEMA_ID)
self.assertEqual(summary["schema_version"], 1)
self.assertIn("CI summary validation: passed", completed.stdout)
```

Add a validator test:

```python
errors = validate_ci_summary({"schema_version": 1})
self.assertIn("$schema must reference the nullstate ci-summary schema", errors)
self.assertIn("run_id is required", errors)
self.assertIn("failed must be a boolean", errors)
self.assertIn("exit_code must be an integer", errors)
self.assertIn("baseline must be an object", errors)
```

Add a schema-document test:

```python
schema = json.loads(Path("docs/schemas/ci-summary.schema.json").read_text(encoding="utf-8"))
self.assertEqual(schema["$id"], CI_SUMMARY_SCHEMA_ID)
self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
self.assertIn("baseline", schema["required"])
```

- [x] **Step 2: Verify tests fail**

Run:

```powershell
C:\Users\ivo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_cli_ci -v
```

Expected: FAIL because generated CI summaries do not yet include `$schema`, the validator, the schema document, or the validation line.

### Task 2: Implement CI Summary Schema Validation

**Files:**
- Modify: `src/nullstate/ci.py`
- Modify: `src/nullstate/cli.py`
- Create: `docs/schemas/ci-summary.schema.json`

- [x] **Step 1: Add schema constant and generated metadata**

Add:

```python
CI_SUMMARY_SCHEMA_ID = "https://schemas.nullstate.dev/ci-summary.schema.json"
CI_SUMMARY_SCHEMA_VERSION = 1
```

Generated summaries should include `$schema` alongside `schema_version`.

- [x] **Step 2: Add `validate_ci_summary()`**

The validator should check generated summary shape: schema metadata, nonempty run ID, boolean failure state, integer exit code, known fail threshold, known max severity, nonnegative counts, verdict string, attack status strings, finding list, and baseline object.

- [x] **Step 3: Validate before writing and print status**

`build_ci_summary()` should raise:

```python
ValueError("Invalid CI summary: ...")
```

if validation fails. `nullstate run --ci` should print:

```text
CI summary validation: passed
```

- [x] **Step 4: Verify focused tests pass**

Run:

```powershell
C:\Users\ivo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_cli_ci -v
```

Expected: PASS.

### Task 3: Update Docs and Checkpoint

**Files:**
- Modify: `README.md`
- Modify: `docs/ci-cd.md`
- Modify: `docs/enterprise-readiness.md`
- Modify: `docs/enterprise-roadmap.md`
- Modify: `docs/handoff.md`
- Modify: `docs/progress.md`
- Modify: `docs/technical-walkthrough.md`

- [x] **Step 1: Update documentation**

Document that generated `ci-summary.json` files include a `$schema` pointer to `docs/schemas/ci-summary.schema.json` and are validated before being written.

- [x] **Step 2: Run full verification**

Run:

```powershell
C:\Users\ivo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check src tests
C:\Users\ivo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m mypy src
C:\Users\ivo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover -s tests -v
git diff --check
```

- [x] **Step 3: Commit and push**

Run:

```powershell
git add .
git commit -m "feat: validate ci summary schema"
git push
gh pr checks 24 --watch --interval 10
```
