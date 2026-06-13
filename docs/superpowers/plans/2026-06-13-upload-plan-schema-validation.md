# Upload Plan Schema Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a versioned upload-plan schema contract and local validation so future cloud ingestion can rely on a stable dry-run artifact.

**Architecture:** Keep `nullstate upload --dry-run` no-network. Add `$schema`, product metadata, a lightweight in-code validator, and a checked-in JSON Schema document under `docs/schemas/`. Validate the generated plan before writing and print a short CLI validation status.

**Tech Stack:** Python 3.11+, Typer CLI, JSON artifacts, `unittest`.

---

### Task 1: Pin Expected Upload Plan Contract

**Files:**
- Modify: `tests/test_upload.py`

- [x] **Step 1: Write failing tests**

Add tests that assert generated upload plans include:

```python
self.assertEqual(plan["$schema"], UPLOAD_PLAN_SCHEMA_ID)
self.assertEqual(plan["schema_version"], 1)
self.assertEqual(plan["product"], "nullstate")
self.assertIn("Upload plan validation: passed", completed.stdout)
```

Add a validator test:

```python
errors = validate_upload_plan({"schema_version": 1})
self.assertIn("run.id is required", errors)
self.assertIn("bundle.sha256 is required", errors)
```

Add a schema-document test:

```python
schema = json.loads(Path("docs/schemas/upload-plan.schema.json").read_text(encoding="utf-8"))
self.assertEqual(schema["$id"], UPLOAD_PLAN_SCHEMA_ID)
self.assertIn("preflight", schema["required"])
```

- [x] **Step 2: Verify tests fail**

Run:

```powershell
python -m unittest tests.test_upload -v
```

Expected: FAIL because upload plans do not yet expose schema metadata or validation.

### Task 2: Implement Validation

**Files:**
- Modify: `src/nullstate/upload.py`
- Modify: `src/nullstate/cli.py`
- Create: `docs/schemas/upload-plan.schema.json`

- [x] **Step 1: Add schema constants and plan metadata**

Add:

```python
UPLOAD_PLAN_SCHEMA_VERSION = 1
UPLOAD_PLAN_SCHEMA_ID = "https://schemas.nullstate.dev/upload-plan.schema.json"
```

Generated plans should include `$schema`, `schema_version`, `product`, and `product_version`.

- [x] **Step 2: Add `validate_upload_plan()`**

The validator should check required top-level sections, required nested values, SHA-256 format, dry-run status, method, auth token redaction flag, and scrub preflight shape.

- [x] **Step 3: Validate before writing and print status**

`write_upload_plan()` should raise `ValueError("Invalid upload plan: ...")` if validation fails. The CLI should print:

```text
Upload plan validation: passed
```

- [x] **Step 4: Verify focused tests pass**

Run:

```powershell
python -m unittest tests.test_upload -v
```

Expected: PASS.

### Task 3: Update Product Docs and Checkpoint

**Files:**
- Modify: `README.md`
- Modify: `docs/ci-cd.md`
- Modify: `docs/enterprise-roadmap.md`
- Modify: `docs/technical-walkthrough.md`
- Modify: `docs/handoff.md`
- Modify: `docs/progress.md`

- [x] **Step 1: Update documentation**

Document that `upload-plan.json` now includes a `$schema` pointer and is validated locally before being written.

- [x] **Step 2: Run full verification**

Run:

```powershell
python -m ruff check src tests
python -m mypy src
python -m unittest discover -s tests -v
git diff --check
```

- [x] **Step 3: Commit and push**

Run:

```powershell
git add .
git commit -m "feat: validate upload plan schema"
git push
gh pr checks 24 --watch --interval 10
```
