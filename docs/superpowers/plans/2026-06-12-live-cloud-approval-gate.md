# Live Cloud Approval Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a default-off live-cloud approval gate so future non-local runtime probes require explicit operator approval and leave an audit trail.

**Architecture:** Keep all existing targets local by default. Extend the attack runner with `allow_live_cloud=False`; non-local HTTP(S) targets still fail unless that flag is true, in which case they are classified as `external-http` and the result records `live_cloud_allowed=True`. Add `nullstate run --allow-live-cloud` only as an audit/gate input; existing scenarios still resolve to local/offline targets until a future adapter supplies a real cloud target.

**Tech Stack:** Python 3.11+, Typer CLI, `unittest`, JSON event logs.

---

### Task 1: Runner Gate And Audit Metadata

**Files:**
- Modify: `tests/test_attack_runner.py`
- Modify: `tests/test_offline_scenario_runs.py`
- Modify: `src/nullstate/attack_runner.py`
- Modify: `src/nullstate/cli.py`
- Modify: `README.md`
- Modify: `docs/security-model.md`
- Modify: `docs/technical-walkthrough.md`
- Modify: `docs/enterprise-readiness.md`
- Modify: `docs/progress.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Write failing tests**

Add tests that verify:

- `run_attack_script(..., target_url="https://example.com")` still fails by default.
- `run_attack_script(..., target_url="https://example.com", allow_live_cloud=True)` runs a generated script and records `target_classification: "external-http"` and `live_cloud_allowed: True`.
- default local/offline targets record `live_cloud_allowed: False`.
- `nullstate run --offline --allow-live-cloud` writes the start event with `allow_live_cloud: True` and red-tool events with `live_cloud_allowed: True` or `False` depending on the target actually used.
- attack command timeouts return structured red-tool evidence with return code `124` instead of a traceback.

- [x] **Step 2: Run tests to verify they fail**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_attack_runner tests.test_offline_scenario_runs -v
```

Expected: FAIL because `allow_live_cloud` is not accepted and no event metadata exists.

- [x] **Step 3: Implement runner gate**

In `src/nullstate/attack_runner.py`:

- add `live_cloud_allowed: bool` to `AttackToolResult`
- add `allow_live_cloud: bool = False` to `run_attack_script()`
- update target validation so non-local HTTP(S) targets raise unless `allow_live_cloud=True`
- return `external-http` for approved non-local HTTP(S) targets
- include `live_cloud_allowed=allow_live_cloud` in the result payload
- catch `subprocess.TimeoutExpired` and return a normal `AttackToolResult` with timeout stderr evidence

- [x] **Step 4: Add CLI option and events**

In `src/nullstate/cli.py`:

- add `allow_live_cloud: bool = typer.Option(False, "--allow-live-cloud", help=...)` to `run`
- add `allow_live_cloud=allow_live_cloud` to the start event
- pass `allow_live_cloud=allow_live_cloud` to both before/after `run_attack_script()` calls

- [x] **Step 5: Run focused tests**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_attack_runner tests.test_offline_scenario_runs -v
```

Expected: PASS.

- [x] **Step 6: Update docs and progress tracking**

Document that `--allow-live-cloud` exists as a required future real-cloud approval gate, but current built-in scenarios still target local/offline sandboxes.

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
git add README.md docs src tests
git commit -m "feat: add live cloud approval gate"
```
