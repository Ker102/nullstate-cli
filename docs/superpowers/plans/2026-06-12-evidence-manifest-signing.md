# Evidence Manifest Signing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional shared-key signatures for `evidence-manifest.json` so CI and support workflows can detect manifest tampering in addition to artifact tampering.

**Architecture:** Use standard-library HMAC-SHA256 to avoid adding a crypto dependency in this slice. `nullstate evidence-manifest --signing-key-env NAME` reads the signing key from the named environment variable and stores only the env-var name as a non-secret key id. `nullstate evidence-verify --signing-key-env NAME` verifies signed manifests with the same key and fails if the signature is missing, invalid, or cannot be checked. Unsigned manifests keep the existing hash-only verification path.

**Tech Stack:** Python 3.11+, Typer CLI, `unittest`, JSON canonicalization, `hmac`, `hashlib`.

---

### Task 1: Shared-Key Evidence Signing

**Files:**
- Modify: `tests/test_evidence_manifest.py`
- Modify: `src/nullstate/evidence_manifest.py`
- Modify: `src/nullstate/cli.py`
- Modify: `README.md`
- Modify: `docs/ci-cd.md`
- Modify: `docs/technical-walkthrough.md`
- Modify: `docs/enterprise-readiness.md`
- Modify: `docs/enterprise-roadmap.md`
- Modify: `docs/progress.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Write failing tests**

Add tests that verify:

- `evidence-manifest --signing-key-env NULLSTATE_TEST_SIGNING_KEY` writes `signing.status: "signed"`.
- the manifest records `algorithm: "hmac-sha256"`, `key_id: "NULLSTATE_TEST_SIGNING_KEY"`, and a 64-character hex signature.
- the signing key value is not written to the manifest.
- `evidence-verify --signing-key-env NULLSTATE_TEST_SIGNING_KEY` reports signature status `verified` and exits `0`.
- changing a signed manifest after signing makes `evidence-verify --signing-key-env ...` exit `2` with `invalid_signature`.

- [x] **Step 2: Run tests to verify they fail**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_evidence_manifest -v
```

Expected: FAIL because the signing CLI options and signature checks do not exist yet.

- [x] **Step 3: Implement signing helpers**

In `src/nullstate/evidence_manifest.py`:

- add optional `signing_key` and `signing_key_id` arguments to manifest writing/building
- add `_sign_manifest(payload, signing_key, key_id)`
- add `_manifest_signature(payload, signing_key)`
- canonicalize JSON with `sort_keys=True` and compact separators after setting `signing.signature` to `None`
- use `hmac.new(signing_key.encode("utf-8"), canonical_bytes, hashlib.sha256).hexdigest()`

- [x] **Step 4: Implement signature verification**

In `verify_evidence_manifest()`, add optional `signing_key`.

Rules:

- unsigned manifest without a signing key remains `signature.status: "unsigned"` and does not fail.
- unsigned manifest with a signing key fails with `missing_signature`.
- signed manifest without a signing key fails with `signature_key_unavailable`.
- signed manifest with the wrong signature fails with `invalid_signature`.
- signed manifest with a matching signature reports `signature.status: "verified"`.

- [x] **Step 5: Add CLI options**

Add `--signing-key-env` to:

- `nullstate evidence-manifest`
- `nullstate evidence-verify`

The CLI reads the key from `os.environ`. If the option is supplied and the environment variable is missing or empty, raise `typer.BadParameter` before writing output.

- [x] **Step 6: Run focused tests**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_evidence_manifest -v
```

Expected: PASS.

- [x] **Step 7: Update docs and progress tracking**

Document:

```powershell
$env:NULLSTATE_EVIDENCE_SIGNING_KEY = "<secret>"
nullstate evidence-manifest --signing-key-env NULLSTATE_EVIDENCE_SIGNING_KEY
nullstate evidence-verify --signing-key-env NULLSTATE_EVIDENCE_SIGNING_KEY
```

Clarify that this is shared-key evidence signing for run artifacts, not public-key release/package provenance.

- [x] **Step 8: Full verification**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m ruff check src tests
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m mypy src
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest discover tests
git diff --check
```

Expected: all commands exit `0`.

- [x] **Step 9: Checkpoint**

Commit locally:

```powershell
git add README.md docs src tests
git commit -m "feat: add evidence manifest signing"
```
