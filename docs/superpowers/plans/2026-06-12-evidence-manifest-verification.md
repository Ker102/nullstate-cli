# Evidence Manifest Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local verifier for `evidence-manifest.json` so CI, support, and case-study workflows can detect changed or missing run artifacts after a manifest is created.

**Architecture:** Extend `src/nullstate/evidence_manifest.py` with a verification function that loads an existing manifest, validates its artifact entries, recomputes SHA-256 and file sizes from the run directory, and returns a structured result. Add a top-level `nullstate evidence-verify` command that exits `0` when all manifest artifacts match and `2` when any artifact fails verification.

**Tech Stack:** Python 3.11+, Typer CLI, `unittest`, JSON artifacts, SHA-256 from the standard library.

---

### Task 1: Evidence Manifest Verification

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

- [x] **Step 1: Write failing tests**

Add tests that:

- run `nullstate evidence-manifest`
- run `nullstate evidence-verify`
- assert an unchanged run returns exit code `0`
- tamper with `report.md`
- assert verification returns exit code `2`
- assert `evidence-verification.json` records failed status, checked count, and mismatch details
- assert custom manifest paths can be verified with `--manifest`

- [x] **Step 2: Run tests to verify they fail**

Run: `C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_evidence_manifest -v`

Expected: FAIL because `evidence-verify` does not exist yet.

- [x] **Step 3: Implement verifier**

Add to `src/nullstate/evidence_manifest.py`:

- `EVIDENCE_VERIFICATION_FILENAME = "evidence-verification.json"`
- `verify_evidence_manifest(run_dir: Path, *, manifest_path: Path | None = None, output_path: Path | None = None) -> dict[str, Any]`

The verifier should:

- reject unsupported hash algorithms
- treat only manifest-listed artifacts as required
- return `status: "passed"` or `status: "failed"`
- include `checked_artifact_count`, `failure_count`, and `failures`
- write `evidence-verification.json` by default

- [x] **Step 4: Add CLI command**

Add `nullstate evidence-verify` with:

- optional run ID
- `--runs-dir`
- `--manifest`
- `--output`

The command should print a short summary and exit `2` when verification fails.

- [x] **Step 5: Run focused tests**

Run: `C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_evidence_manifest -v`

Expected: PASS.

- [x] **Step 6: Update docs and progress tracking**

Document `nullstate evidence-verify`, the default `evidence-verification.json` artifact, CI usage, and the distinction between hash verification and future cryptographic signing.

- [x] **Step 7: Full verification**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m ruff check src tests
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m mypy src
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest discover -s tests -v
git diff --cached --check
```

Expected: all commands exit `0`.

- [x] **Step 8: Checkpoint**

Commit and push only the feature branch:

```powershell
git add README.md docs src tests
git commit -m "feat: add evidence manifest verification"
git push origin feature/red-agent-runner
```
