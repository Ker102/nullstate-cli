# Policy Command Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend red-tool policies with controls for generated command arguments, allowed stages, timeout ceilings, and output-size ceilings.

**Architecture:** Keep the runner template-based. Add optional policy fields that constrain the already-fixed `attack.py` invocation rather than letting policy define arbitrary commands. Older policy files that omit these fields remain valid. Newly generated policy files include conservative defaults matching the current runner behavior.

**Tech Stack:** Python 3.11+, Typer CLI, `unittest`, JSON policy artifacts.

---

### Task 1: Command Execution Controls

**Files:**
- Modify: `tests/test_attack_policy.py`
- Modify: `src/nullstate/policy.py`
- Modify: `src/nullstate/attack_runner.py`
- Modify: `README.md`
- Modify: `docs/technical-walkthrough.md`
- Modify: `docs/enterprise-readiness.md`
- Modify: `docs/enterprise-roadmap.md`
- Modify: `docs/progress.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Write failing tests**

Add tests that:

- assert `nullstate policy init` writes `allowed_stages`, `allowed_attack_script_args`, `max_timeout_seconds`, and `max_output_bytes`
- assert `run_attack_script()` rejects a stage not allowlisted by policy
- assert `run_attack_script()` rejects a timeout above `max_timeout_seconds`
- assert `run_attack_script()` rejects `max_output_bytes` above the policy ceiling
- assert `run_attack_script()` rejects the `--manifest` argument when the policy does not allow it

- [x] **Step 2: Run tests to verify they fail**

Run: `C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_attack_policy -v`

Expected: FAIL because command controls do not exist yet.

- [x] **Step 3: Implement policy fields**

Add optional fields to `AttackPolicy`:

- `allowed_stages: set[str] | None`
- `allowed_attack_script_args: set[str] | None`
- `max_timeout_seconds: int | None`
- `max_output_bytes: int | None`

Add default generated policy values:

- `allowed_stages`: `before`, `after`
- `allowed_attack_script_args`: `--target-url`, `--stage`, `--manifest`
- `max_timeout_seconds`: `30`
- `max_output_bytes`: `12000`

- [x] **Step 4: Enforce controls in the runner**

Update `enforce_attack_policy()` and `run_attack_script()` so the runner checks stage, argument flags, timeout, and max output bytes before executing `attack.py`.

- [x] **Step 5: Run focused tests**

Run: `C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_attack_policy -v`

Expected: PASS.

- [x] **Step 6: Update docs and progress tracking**

Document the new controls and keep the caveat that policy still constrains a generated command template, not arbitrary shell.

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
git commit -m "feat: add policy command controls"
git push origin feature/red-agent-runner
```
