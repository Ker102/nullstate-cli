# Policy Schema Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a versioned JSON Schema contract for generated red-tool policy files and validate generated policies before writing them.

**Architecture:** Keep existing policy loading backward-compatible for older files. Add a `$schema` pointer to newly generated policies, a checked-in JSON Schema under `docs/schemas/`, and a lightweight validator that `policy init` uses before writing. Continue accepting older hand-written policy files that omit `$schema`.

**Tech Stack:** Python 3.11+, Typer CLI, JSON artifacts, `unittest`.

---

### Task 1: Pin Expected Policy Contract

**Files:**
- Modify: `tests/test_attack_policy.py`

- [x] **Step 1: Write failing tests**

Add assertions that generated policies include:

```python
self.assertEqual(payload["$schema"], POLICY_SCHEMA_ID)
self.assertEqual(payload["schema_version"], 1)
self.assertIn("Policy validation: passed", completed.stdout)
```

Add a validator test:

```python
errors = validate_policy_payload({"schema_version": 1})
self.assertIn("$schema must reference the nullstate policy schema", errors)
self.assertIn("allowed_target_classifications must be a list", errors)
```

Add a schema-document test:

```python
schema = json.loads(Path("docs/schemas/nullstate-policy.schema.json").read_text(encoding="utf-8"))
self.assertEqual(schema["$id"], POLICY_SCHEMA_ID)
self.assertIn("allowed_command_policy_ids", schema["required"])
```

- [x] **Step 2: Verify tests fail**

Run:

```powershell
python -m unittest tests.test_attack_policy -v
```

Expected: FAIL because generated policies do not yet include `$schema`, the validator, or the schema document.

### Task 2: Implement Policy Schema Validation

**Files:**
- Modify: `src/nullstate/policy.py`
- Modify: `src/nullstate/cli.py`
- Create: `docs/schemas/nullstate-policy.schema.json`

- [x] **Step 1: Add schema constant and generated metadata**

Add:

```python
POLICY_SCHEMA_ID = "https://schemas.nullstate.dev/nullstate-policy.schema.json"
```

Generated policies should include `$schema` alongside `schema_version`.

- [x] **Step 2: Add `validate_policy_payload()`**

The validator should check generated policy payload shape: schema metadata, required allowlist arrays, positive timeout/output ceilings, and optional notes text.

- [x] **Step 3: Validate before writing and print status**

`write_default_policy()` should raise `ValueError("Invalid policy: ...")` if validation fails. `policy init` should print:

```text
Policy validation: passed
```

- [x] **Step 4: Verify focused tests pass**

Run:

```powershell
python -m unittest tests.test_attack_policy -v
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

Document that generated policy files include a `$schema` pointer to `docs/schemas/nullstate-policy.schema.json` and are validated before writing.

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
git commit -m "feat: validate generated policy schema"
git push
gh pr checks 24 --watch --interval 10
```
