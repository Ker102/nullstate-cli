# Release Provenance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden tagged package releases with a release manifest and GitHub artifact attestations for built distributions.

**Architecture:** Extend the existing `.github/workflows/release.yml` rather than adding a second release pipeline. After `python -m build`, generate `dist/release-manifest.json` with SHA-256 digests and sizes for wheel/sdist artifacts, then use GitHub artifact attestations (`actions/attest@v4`) over `dist/*`. Keep release creation via `gh release create`, now uploading the manifest alongside package files.

**Tech Stack:** GitHub Actions, Python package build, GitHub artifact attestations, `unittest` workflow text tests.

---

### Task 1: Release Manifest And Artifact Attestation

**Files:**
- Modify: `tests/test_github_workflows.py`
- Modify: `.github/workflows/release.yml`
- Modify: `README.md`
- Modify: `docs/ci-cd.md`
- Modify: `docs/security-model.md`
- Modify: `docs/threat-model.md`
- Modify: `docs/enterprise-readiness.md`
- Modify: `docs/progress.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Write failing tests**

Add a workflow test that verifies `.github/workflows/release.yml` includes:

- `id-token: write`
- `attestations: write`
- `actions/attest@v4`
- `subject-path: dist/*`
- `release-manifest.json`
- `hashlib.sha256`
- `gh release create "${GITHUB_REF_NAME}" dist/* --generate-notes`

- [x] **Step 2: Run tests to verify they fail**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_github_workflows -v
```

Expected: FAIL because the release workflow does not generate a manifest or attest artifacts yet.

- [x] **Step 3: Update release workflow permissions**

In `.github/workflows/release.yml`, set:

```yaml
permissions:
  contents: write
  id-token: write
  attestations: write
```

- [x] **Step 4: Generate release manifest**

After `python -m build`, add a Python step that writes `dist/release-manifest.json` with:

- `schema_version`
- `tag`
- `generated_at`
- `artifacts` array containing `name`, `sha256`, and `size_bytes`

Exclude `release-manifest.json` from its own artifact list.

- [x] **Step 5: Add artifact attestation**

After manifest generation, add:

```yaml
- name: Attest release artifacts
  uses: actions/attest@v4
  with:
    subject-path: dist/*
```

- [x] **Step 6: Run focused tests**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_github_workflows -v
```

Expected: PASS.

- [x] **Step 7: Update docs and progress tracking**

Document:

```powershell
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli
```

Clarify that GitHub artifact attestations cover release build provenance, while evidence-manifest HMAC signing covers run evidence artifacts.

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
git add README.md docs .github tests
git commit -m "ci: add release provenance attestations"
```
