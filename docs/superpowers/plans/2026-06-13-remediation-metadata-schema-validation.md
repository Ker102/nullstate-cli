# Remediation Metadata Schema Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a versioned JSON Schema contract for `remediation.json` and validate generated remediation metadata before it is written into run artifacts.

**Architecture:** Keep existing readers tolerant of older `remediation.json` files while strengthening newly generated metadata. Add a `$schema` pointer to generated metadata, document the contract under `docs/schemas/`, and validate the local payload inside the remediation metadata builder before the CLI writes reports, bundles, and run artifacts.

**Tech Stack:** Python 3.11+, JSON artifacts, `unittest`.

---

### Task 1: Pin Expected Remediation Metadata Contract

**Files:**
- Modify: `tests/test_remediation.py`

- [x] **Step 1: Write failing tests**

Add assertions that generated remediation metadata includes a schema contract:

```python
metadata = build_remediation_metadata(
    "aws-public-s3",
    PatchResult(
        changed=True,
        diff="",
        changed_files=["main.tf"],
        rules_applied=("AWS_S3_BLOCK_PUBLIC_ACCESS",),
    ),
)
self.assertEqual(metadata["$schema"], REMEDIATION_METADATA_SCHEMA_ID)
self.assertEqual(metadata["schema_version"], 1)
self.assertEqual(metadata["scenario"], "aws-public-s3")
self.assertEqual(metadata["changed_files"], ["main.tf"])
```

Add a validator test:

```python
errors = validate_remediation_metadata({"schema_version": 1})
self.assertIn("$schema must reference the nullstate remediation metadata schema", errors)
self.assertIn("scenario is required", errors)
self.assertIn("changed must be a boolean", errors)
self.assertIn("changed_files must be a list", errors)
```

Add a schema-document test:

```python
schema = json.loads(Path("docs/schemas/remediation-metadata.schema.json").read_text(encoding="utf-8"))
self.assertEqual(schema["$id"], REMEDIATION_METADATA_SCHEMA_ID)
self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
self.assertIn("rules_applied", schema["required"])
```

- [x] **Step 2: Verify tests fail**

Run:

```powershell
C:\Users\ivo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_remediation -v
```

Expected: FAIL because generated metadata does not yet include `$schema`, the validator, or the schema document.

### Task 2: Implement Remediation Metadata Schema Validation

**Files:**
- Modify: `src/nullstate/remediation.py`
- Create: `docs/schemas/remediation-metadata.schema.json`

- [x] **Step 1: Add schema constant and generated metadata**

Add:

```python
REMEDIATION_METADATA_SCHEMA_ID = "https://schemas.nullstate.dev/remediation-metadata.schema.json"
```

Generated metadata should include `$schema` alongside `schema_version`.

- [x] **Step 2: Add `validate_remediation_metadata()`**

The validator should check generated metadata shape: schema metadata, nonempty scenario, boolean changed flag, changed file list, nonempty ruleset version, and applied rule list.

- [x] **Step 3: Validate before returning metadata**

`build_remediation_metadata()` should raise:

```python
ValueError("Invalid remediation metadata: ...")
```

if validation fails.

- [x] **Step 4: Verify focused tests pass**

Run:

```powershell
C:\Users\ivo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_remediation -v
```

Expected: PASS.

### Task 3: Update Docs and Checkpoint

**Files:**
- Modify: `README.md`
- Modify: `docs/enterprise-readiness.md`
- Modify: `docs/enterprise-roadmap.md`
- Modify: `docs/handoff.md`
- Modify: `docs/progress.md`
- Modify: `docs/technical-walkthrough.md`

- [x] **Step 1: Update documentation**

Document that generated `remediation.json` files include a `$schema` pointer to `docs/schemas/remediation-metadata.schema.json` and are validated before run artifacts consume them.

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
git commit -m "feat: validate remediation metadata schema"
git push
gh pr checks 24 --watch --interval 10
```
