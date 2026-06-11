# Evidence Integrity Manifest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic run evidence manifest that inventories shareable run artifacts with SHA-256 checksums and records that cryptographic signing is not yet enabled.

**Architecture:** Implement a focused manifest writer in `src/nullstate/evidence_manifest.py`, then expose it through a new `nullstate evidence-manifest` command. The manifest should exclude copied workspaces, Terraform internals, Python caches, and the manifest file itself so repeated writes do not recursively change the artifact list.

**Tech Stack:** Python 3.11+, Typer CLI, `unittest`, JSON artifacts, SHA-256 from the standard library.

---

### Task 1: Evidence Manifest Command

**Files:**
- Create: `tests/test_evidence_manifest.py`
- Create: `src/nullstate/evidence_manifest.py`
- Modify: `src/nullstate/cli.py`
- Modify: `README.md`
- Modify: `docs/technical-walkthrough.md`
- Modify: `docs/enterprise-readiness.md`
- Modify: `docs/enterprise-roadmap.md`
- Modify: `docs/progress.md`

- [x] **Step 1: Write the failing test**

Create `tests/test_evidence_manifest.py` with a minimal run directory and assertions that `nullstate evidence-manifest` writes `evidence-manifest.json`, includes artifact hashes, excludes `workspace/` files, excludes itself, and marks signing as unsigned.

- [x] **Step 2: Run test to verify it fails**

Run: `C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_evidence_manifest -v`

Expected: FAIL because the `evidence-manifest` command does not exist yet.

- [x] **Step 3: Write minimal implementation**

Create `src/nullstate/evidence_manifest.py` with:

- `EVIDENCE_MANIFEST_SCHEMA_VERSION = 1`
- `EVIDENCE_MANIFEST_FILENAME = "evidence-manifest.json"`
- `build_evidence_manifest(run_dir: Path, *, output_path: Path | None = None) -> dict[str, Any]`
- `write_evidence_manifest(run_dir: Path, output_path: Path | None = None) -> dict[str, Any]`

Add a `nullstate evidence-manifest` command in `src/nullstate/cli.py` that resolves a run directory, writes the manifest, prints artifact count, and points to report/bundle.

- [x] **Step 4: Run test to verify it passes**

Run: `C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_evidence_manifest -v`

Expected: PASS.

- [x] **Step 5: Update documentation and progress tracking**

Document the new artifact, command, and enterprise caveat: this is integrity inventory, not cryptographic signing. Update `docs/progress.md` with this checkpoint.

- [x] **Step 6: Full verification**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m ruff check src tests
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m mypy src
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest discover -s tests -v
git diff --check
```

Expected: all commands exit `0`.

- [x] **Step 7: Checkpoint**

Commit and push only the feature branch:

```powershell
git add README.md docs src tests
git commit -m "feat: add evidence integrity manifest"
git push origin feature/red-agent-runner
```
