# Attack Manifest Schema Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a versioned JSON Schema contract for `attack-manifest.json` and validate generated attack manifests before constrained red-tool execution consumes them.

**Architecture:** Keep existing run readers tolerant of older attack manifests while strengthening newly generated manifests. Add a `$schema` pointer to generated attack manifests, document the contract under `docs/schemas/`, and validate the local payload inside the attack manifest writer before it writes to disk. The CLI should print an explicit validation status during `nullstate run`.

**Tech Stack:** Python 3.11+, Typer CLI, JSON artifacts, `unittest`.

---

### Task 1: Pin Expected Attack Manifest Contract

**Files:**
- Modify: `tests/test_attack_manifest.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Write failing tests**

Update `tests/test_attack_manifest.py` imports:

```python
from nullstate.attack_manifest import ATTACK_MANIFEST_SCHEMA_ID, validate_attack_manifest, write_attack_manifest
```

Add assertions that generated attack manifests include a schema contract:

```python
self.assertEqual(manifest["$schema"], ATTACK_MANIFEST_SCHEMA_ID)
self.assertEqual(manifest["schema_version"], 1)
self.assertEqual(manifest["scenario"], "aws-public-s3")
self.assertEqual(manifest["backend"], "localstack-aws")
```

Add a validator test:

```python
errors = validate_attack_manifest({"schema_version": 1})
self.assertIn("$schema must reference the nullstate attack-manifest schema", errors)
self.assertIn("scenario is required", errors)
self.assertIn("backend is required", errors)
self.assertIn("target_url is required", errors)
self.assertIn("resources must be an object", errors)
```

Add a schema-document test:

```python
schema = json.loads(Path("docs/schemas/attack-manifest.schema.json").read_text(encoding="utf-8"))
self.assertEqual(schema["$id"], ATTACK_MANIFEST_SCHEMA_ID)
self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
self.assertIn("resources", schema["required"])
```

In `tests/test_cli.py`, add:

```python
self.assertIn("Attack manifest validation: passed", run_completed.stdout)
```

- [x] **Step 2: Verify tests fail**

Run:

```powershell
C:\Users\ivo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_attack_manifest tests.test_cli -v
```

Expected: FAIL because generated attack manifests do not yet include `$schema`, the validator, the schema document, or the CLI validation line.

### Task 2: Implement Attack Manifest Schema Validation

**Files:**
- Modify: `src/nullstate/attack_manifest.py`
- Modify: `src/nullstate/cli.py`
- Create: `docs/schemas/attack-manifest.schema.json`

- [x] **Step 1: Add schema constant and generated metadata**

Add:

```python
ATTACK_MANIFEST_SCHEMA_ID = "https://schemas.nullstate.dev/attack-manifest.schema.json"
ATTACK_MANIFEST_SCHEMA_VERSION = 1
```

Generated manifests should include `$schema` alongside `schema_version`.

- [x] **Step 2: Add `validate_attack_manifest()`**

The validator should check generated manifest shape: schema metadata, nonempty scenario, nonempty backend, nonempty target URL, and object-shaped resource hints with string keys and string values.

- [x] **Step 3: Validate before writing and print status**

`write_attack_manifest()` should raise:

```python
ValueError("Invalid attack manifest: ...")
```

if validation fails. `nullstate run` should print:

```text
Attack manifest validation: passed
```

- [x] **Step 4: Verify focused tests pass**

Run:

```powershell
C:\Users\ivo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_attack_manifest tests.test_cli -v
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

Document that generated `attack-manifest.json` files include a `$schema` pointer to `docs/schemas/attack-manifest.schema.json` and are validated before constrained probe execution.

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
git commit -m "feat: validate attack manifest schema"
git push
gh pr checks 24 --watch --interval 10
```
