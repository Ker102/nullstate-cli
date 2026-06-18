# Evidence Manifest Schema Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a versioned evidence-manifest schema contract and local validation for shareable run evidence inventories.

**Architecture:** Keep evidence manifests local and deterministic. Add `$schema`, a checked-in JSON Schema document, and a lightweight validator that checks the generated manifest before writing. Keep verification focused on artifact integrity, but preserve the manifest schema metadata in verification output.

**Tech Stack:** Python 3.11+, Typer CLI, JSON artifacts, `unittest`.

---

### Task 1: Pin Expected Evidence Manifest Contract

**Files:**
- Modify: `tests/test_evidence_manifest.py`

- [x] **Step 1: Write failing tests**

Add tests that assert generated evidence manifests include:

```python
self.assertEqual(payload["$schema"], EVIDENCE_MANIFEST_SCHEMA_ID)
self.assertEqual(payload["schema_version"], 1)
self.assertIn("Evidence manifest validation: passed", completed.stdout)
```

Add a validator test:

```python
errors = validate_evidence_manifest({"schema_version": 1})
self.assertIn("$schema must reference the nullstate evidence-manifest schema", errors)
self.assertIn("run.id is required", errors)
self.assertIn("artifacts must be a list", errors)
```

Add a schema-document test:

```python
schema = json.loads(Path("docs/schemas/evidence-manifest.schema.json").read_text(encoding="utf-8"))
self.assertEqual(schema["$id"], EVIDENCE_MANIFEST_SCHEMA_ID)
self.assertIn("integrity", schema["required"])
self.assertIn("signing", schema["required"])
```

- [x] **Step 2: Verify tests fail**

Run:

```powershell
python -m unittest tests.test_evidence_manifest -v
```

Expected: FAIL because evidence manifests do not yet expose `$schema`, schema validation, or a schema document.

### Task 2: Implement Evidence Manifest Validation

**Files:**
- Modify: `src/nullstate/evidence_manifest.py`
- Modify: `src/nullstate/cli.py`
- Create: `docs/schemas/evidence-manifest.schema.json`

- [x] **Step 1: Add schema constant and generated metadata**

Add:

```python
EVIDENCE_MANIFEST_SCHEMA_ID = "https://schemas.nullstate.dev/evidence-manifest.schema.json"
```

Generated manifests should include `$schema` alongside `schema_version`.

- [x] **Step 2: Add `validate_evidence_manifest()`**

The validator should check required top-level sections, required run identity, artifact count consistency, artifact path/hash/size fields, integrity hash algorithm, and signing metadata.

- [x] **Step 3: Validate before writing and print status**

`write_evidence_manifest()` should raise `ValueError("Invalid evidence manifest: ...")` if validation fails. The CLI should print:

```text
Evidence manifest validation: passed
```

- [x] **Step 4: Verify focused tests pass**

Run:

```powershell
python -m unittest tests.test_evidence_manifest -v
```

Expected: PASS.

### Task 3: Update Docs and Checkpoint

**Files:**
- Modify: `README.md`
- Modify: `docs/ci-cd.md`
- Modify: `docs/enterprise-readiness.md`
- Modify: `docs/enterprise-roadmap.md`
- Modify: `docs/technical-walkthrough.md`
- Modify: `docs/handoff.md`
- Modify: `docs/progress.md`

- [x] **Step 1: Update documentation**

Document that `evidence-manifest.json` now includes a `$schema` pointer to `docs/schemas/evidence-manifest.schema.json` and is validated locally before writing.

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
git commit -m "feat: validate evidence manifest schema"
git push
gh pr checks 24 --watch --interval 10
```
