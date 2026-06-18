# Keyless Release Signing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sign release artifacts with Sigstore keyless signing and fail the release if signing bundles are missing.

**Architecture:** Keep the existing tag release workflow. After release manifest generation and GitHub attestations, use `sigstore/gh-action-sigstore-python` with explicit `dist/*.whl`, `dist/*.tar.gz`, `dist/sbom.spdx.json`, and `dist/release-manifest.json` inputs. Add a Python validation step that checks each primary release artifact has a neighboring `.sigstore.json` bundle before `gh release create dist/*`.

**Tech Stack:** GitHub Actions, GitHub OIDC, Sigstore Python GitHub Action, Python 3.13 standard library, `unittest` workflow text tests.

---

### Task 1: Keyless Release Signing

**Files:**
- Modify: `tests/test_github_workflows.py`
- Modify: `.github/workflows/release.yml`
- Modify: `README.md`
- Modify: `docs/ci-cd.md`
- Modify: `docs/enterprise-readiness.md`
- Modify: `docs/enterprise-roadmap.md`
- Modify: `docs/progress.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Write failing tests**

Extend the release workflow test to assert:

```python
self.assertIn("Sign release artifacts", text)
self.assertIn("sigstore/gh-action-sigstore-python@v3.4.0", text)
self.assertIn("dist/*.whl", text)
self.assertIn("dist/*.tar.gz", text)
self.assertIn("dist/sbom.spdx.json", text)
self.assertIn("dist/release-manifest.json", text)
self.assertIn("release-signing-artifacts: false", text)
self.assertIn("Validate release signatures", text)
self.assertIn('signature_path = path.with_name(path.name + ".sigstore.json")', text)
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_github_workflows -v
```

Expected: FAIL because the release workflow does not sign artifacts yet.

- [x] **Step 3: Add Sigstore signing step**

After `Attest release SBOM`, add:

```yaml
- name: Sign release artifacts
  uses: sigstore/gh-action-sigstore-python@v3.4.0
  with:
    inputs: |
      dist/*.whl
      dist/*.tar.gz
      dist/sbom.spdx.json
      dist/release-manifest.json
    release-signing-artifacts: false
```

- [x] **Step 4: Validate signing bundles**

After signing and before `Create GitHub release`, add a Python step that checks each primary artifact has a neighboring `.sigstore.json` file.

- [x] **Step 5: Run focused tests**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_github_workflows -v
```

Expected: PASS.

- [x] **Step 6: Update docs and progress tracking**

Document keyless Sigstore signing, `.sigstore.json` release assets, and that this is separate from GitHub artifact attestations.

- [x] **Step 7: Full verification**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m ruff check src tests
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m mypy src
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest discover tests
git diff --check
```

Expected: all commands exit `0`.

- [x] **Step 8: Checkpoint**

Commit locally:

```powershell
git add README.md docs .github/workflows/release.yml tests/test_github_workflows.py
git commit -m "ci: add keyless release signing"
```
