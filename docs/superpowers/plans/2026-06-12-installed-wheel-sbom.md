# Installed Wheel SBOM Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate release SBOMs from the built wheel installed into a clean virtual environment, including resolved runtime package versions.

**Architecture:** Keep the existing release workflow and `actions/attest@v4` SBOM attestation. Add a clean `.sbom-venv` install before SBOM generation, then update the embedded Python SBOM script to inventory installed distributions with `importlib.metadata`.

**Tech Stack:** GitHub Actions, Python 3.13 standard library, `venv`, `pip`, SPDX 2.3 JSON, `unittest` workflow text tests.

---

### Task 1: Installed Wheel SBOM

**Files:**
- Modify: `tests/test_github_workflows.py`
- Modify: `.github/workflows/release.yml`
- Modify: `README.md`
- Modify: `docs/ci-cd.md`
- Modify: `docs/enterprise-readiness.md`
- Modify: `docs/enterprise-roadmap.md`
- Modify: `docs/progress.md`

- [x] **Step 1: Write failing tests**

Extend the release workflow test to assert:

```python
self.assertIn("python -m venv .sbom-venv", text)
self.assertIn(".sbom-venv/bin/python -m pip install dist/*.whl", text)
self.assertIn("import importlib.metadata", text)
self.assertIn('excluded_tools = {"pip", "setuptools", "wheel"}', text)
self.assertIn('"versionInfo": distribution.version', text)
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_github_workflows -v
```

Expected: FAIL because the workflow still generates the SBOM from `pyproject.toml` dependencies.

- [x] **Step 3: Install built wheel into clean SBOM venv**

In `.github/workflows/release.yml`, update `Generate release SBOM` to run:

```yaml
python -m venv .sbom-venv
.sbom-venv/bin/python -m pip install --upgrade pip
.sbom-venv/bin/python -m pip install dist/*.whl
.sbom-venv/bin/python - <<'PY'
```

- [x] **Step 4: Inventory installed distributions**

Replace dependency-only SBOM generation with `importlib.metadata.distributions()`. Exclude `pip`, `setuptools`, and `wheel`, include `versionInfo`, and build `DEPENDS_ON` relationships from installed package `Requires-Dist` metadata when the target package is installed.

- [x] **Step 5: Run focused tests**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_github_workflows -v
```

Expected: PASS.

- [x] **Step 6: Update docs and progress tracking**

Document that release SBOMs now inventory the built wheel's installed runtime environment, not only declared dependency names.

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
git commit -m "ci: generate sbom from installed wheel"
```
