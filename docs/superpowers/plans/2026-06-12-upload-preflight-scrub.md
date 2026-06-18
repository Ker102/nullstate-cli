# Upload Preflight Scrub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add upload dry-run preflight metadata that warns when a raw, unscrubbed run is being prepared for future cloud ingestion.

**Architecture:** Extend `src/nullstate/upload.py` with a local scrub preflight helper that checks for `scrub-report.json` in the selected run directory. Keep dry-run upload no-network, include the preflight result in `upload-plan.json`, and surface a concise CLI warning for raw runs.

**Tech Stack:** Python standard library, Typer CLI, `unittest`, existing artifact scrubber and upload-plan JSON.

---

### Task 1: Upload Preflight Scrub Metadata

**Files:**
- Modify: `tests/test_upload.py`
- Modify: `src/nullstate/upload.py`
- Modify: `src/nullstate/cli.py`
- Modify: `README.md`
- Modify: `docs/ci-cd.md`
- Modify: `docs/technical-walkthrough.md`
- Modify: `docs/enterprise-readiness.md`
- Modify: `docs/enterprise-roadmap.md`
- Modify: `docs/progress.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Write failing tests**

Add assertions that raw upload plans include:

```python
self.assertEqual(plan["preflight"]["scrub"]["status"], "not_performed")
self.assertFalse(plan["preflight"]["scrub"]["scrub_report_present"])
self.assertFalse(plan["preflight"]["scrub"]["upload_recommended"])
self.assertIn("Run has not been scrubbed", plan["preflight"]["scrub"]["warnings"][0])
self.assertIn("Run has not been scrubbed", completed.stdout)
```

Add a second test that runs `nullstate scrub`, uploads from the scrubbed output directory, and asserts:

```python
self.assertEqual(plan["preflight"]["scrub"]["status"], "scrubbed")
self.assertTrue(plan["preflight"]["scrub"]["scrub_report_present"])
self.assertTrue(plan["preflight"]["scrub"]["upload_recommended"])
self.assertEqual(plan["preflight"]["scrub"]["scrub_report_path"], "scrub-report.json")
self.assertEqual(plan["preflight"]["scrub"]["warnings"], [])
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_upload -v
```

Expected: FAIL because `preflight` is not present.

- [x] **Step 3: Implement upload preflight**

Add a helper in `src/nullstate/upload.py`:

```python
def _build_scrub_preflight(run_dir: Path) -> dict[str, Any]:
    report_path = run_dir / "scrub-report.json"
    if report_path.is_file():
        return {
            "status": "scrubbed",
            "scrub_report_present": True,
            "scrub_report_path": report_path.relative_to(run_dir).as_posix(),
            "upload_recommended": True,
            "warnings": [],
        }
    return {
        "status": "not_performed",
        "scrub_report_present": False,
        "upload_recommended": False,
        "warnings": [
            "Run has not been scrubbed. Run nullstate scrub before sharing or future cloud upload."
        ],
    }
```

Call it from `build_upload_plan()` under:

```python
"preflight": {
    "scrub": _build_scrub_preflight(run_dir),
},
```

- [x] **Step 4: Surface CLI warning**

In `src/nullstate/cli.py`, after printing token status, print each warning from `plan["preflight"]["scrub"]["warnings"]`.

- [x] **Step 5: Run focused tests**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_upload -v
```

Expected: PASS.

- [x] **Step 6: Update docs and progress tracking**

Document that `upload --dry-run` now records scrub readiness and warns when a raw run is selected.

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
git add README.md docs src/nullstate/upload.py src/nullstate/cli.py tests/test_upload.py
git commit -m "feat: add upload scrub preflight"
```
