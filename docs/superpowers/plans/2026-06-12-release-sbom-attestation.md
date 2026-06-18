# Release SBOM Attestation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a release SBOM artifact and attest it alongside package build provenance.

**Architecture:** Extend `.github/workflows/release.yml` after the package build. Generate `dist/sbom.spdx.json` with a small standard-library Python script that reads `pyproject.toml`, records the root package and declared runtime dependencies in SPDX 2.3 JSON, then include the SBOM in `release-manifest.json` and attest it with `actions/attest@v4` using `sbom-path`.

**Tech Stack:** GitHub Actions, Python 3.13 standard library, SPDX 2.3 JSON, GitHub artifact attestations, `unittest` workflow text tests.

---

### Task 1: Release SBOM Attestation

**Files:**
- Modify: `tests/test_github_workflows.py`
- Modify: `.github/workflows/release.yml`
- Modify: `README.md`
- Modify: `docs/ci-cd.md`
- Modify: `docs/security-model.md`
- Modify: `docs/threat-model.md`
- Modify: `docs/enterprise-readiness.md`
- Modify: `docs/enterprise-roadmap.md`
- Modify: `docs/progress.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Write failing tests**

Extend the release workflow test to assert:

- `sbom.spdx.json`
- `spdxVersion`
- `tomllib`
- `relationships`
- `sbom-path: dist/sbom.spdx.json`
- a step named `Attest release SBOM`
- `gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli --predicate-type https://spdx.dev/Document/v2.3` appears in docs

- [x] **Step 2: Run tests to verify they fail**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_github_workflows -v
```

Expected: FAIL because no release SBOM is generated or attested yet.

- [x] **Step 3: Generate SPDX SBOM**

Add a `Generate release SBOM` step before `Generate release manifest`.

The Python script should:

- read `pyproject.toml` with `tomllib`
- write `dist/sbom.spdx.json`
- include SPDX 2.3 fields: `spdxVersion`, `dataLicense`, `SPDXID`, `name`, `documentNamespace`, `creationInfo`, `packages`, and `relationships`
- include the root package plus runtime dependencies from `[project].dependencies`

- [x] **Step 4: Attest SBOM**

Add:

```yaml
- name: Attest release SBOM
  uses: actions/attest@v4
  with:
    subject-path: dist/*
    sbom-path: dist/sbom.spdx.json
```

- [x] **Step 5: Run focused tests**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_github_workflows -v
```

Expected: PASS.

- [x] **Step 6: Update docs and progress tracking**

Document package and SBOM attestation verification:

```powershell
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli --predicate-type https://spdx.dev/Document/v2.3
```

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
git add README.md docs .github tests
git commit -m "ci: add release sbom attestation"
```
