# Release SBOM Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fail tagged releases before attestation when `dist/sbom.spdx.json` is malformed or missing expected package metadata.

**Architecture:** Add a `Validate release SBOM` step after `Generate release SBOM` in `.github/workflows/release.yml`. Use a short standard-library Python validator that reads the generated SPDX JSON, checks required fields and relationships, and exits non-zero with clear messages when validation fails.

**Tech Stack:** GitHub Actions, Python 3.13 standard library, SPDX 2.3 JSON, `unittest` workflow text tests.

---

### Task 1: Release SBOM Validation

**Files:**
- Modify: `tests/test_github_workflows.py`
- Modify: `.github/workflows/release.yml`
- Modify: `README.md`
- Modify: `docs/ci-cd.md`
- Modify: `docs/enterprise-readiness.md`
- Modify: `docs/progress.md`

- [x] **Step 1: Write failing tests**

Extend the release workflow test to assert:

```python
self.assertIn("Validate release SBOM", text)
self.assertIn('sbom_path = Path("dist/sbom.spdx.json")', text)
self.assertIn('if sbom.get("spdxVersion") != "SPDX-2.3"', text)
self.assertIn('required_package_fields = {"SPDXID", "name", "versionInfo"}', text)
self.assertIn('forbidden_packages = {"pip", "setuptools", "wheel"}', text)
self.assertIn('relationshipType") == "DESCRIBES"', text)
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_github_workflows -v
```

Expected: FAIL because the release workflow does not yet validate the generated SBOM.

- [x] **Step 3: Add validation step**

Add `Validate release SBOM` after `Generate release SBOM` and before `Generate release manifest`. The step should load `dist/sbom.spdx.json`, check the required fields, and raise `SystemExit` with a readable message for failures.

- [x] **Step 4: Run focused tests**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_github_workflows -v
```

Expected: PASS.

- [x] **Step 5: Update docs and progress tracking**

Document that tagged releases validate the generated SBOM before manifest creation and attestation.

- [x] **Step 6: Full verification**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m ruff check src tests
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m mypy src
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest discover tests
git diff --check
```

Expected: all commands exit `0`.

- [x] **Step 7: Checkpoint**

Commit locally:

```powershell
git add README.md docs .github/workflows/release.yml tests/test_github_workflows.py
git commit -m "ci: validate release sbom"
```
