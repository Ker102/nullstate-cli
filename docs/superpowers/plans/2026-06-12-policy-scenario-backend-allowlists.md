# Policy Scenario Backend Allowlists Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend red-tool policy files so operators can allowlist specific scenarios and backends, not only target classifications and command policy IDs.

**Architecture:** Keep the existing JSON policy contract and add optional `allowed_scenarios` and `allowed_backends` fields. Newly generated policies include explicit defaults. Older policy files that omit these fields remain valid and continue enforcing the fields they already define. The CLI passes scenario and backend context into the constrained attack runner, and the runner records that context in red-tool events.

**Tech Stack:** Python 3.11+, Typer CLI, `unittest`, JSON policy artifacts.

---

### Task 1: Scenario and Backend Policy Fields

**Files:**
- Modify: `tests/test_attack_policy.py`
- Modify: `src/nullstate/policy.py`
- Modify: `src/nullstate/attack_runner.py`
- Modify: `src/nullstate/cli.py`
- Modify: `README.md`
- Modify: `docs/technical-walkthrough.md`
- Modify: `docs/enterprise-readiness.md`
- Modify: `docs/enterprise-roadmap.md`
- Modify: `docs/progress.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Write failing tests**

Add tests that:

- assert `nullstate policy init` writes `allowed_scenarios` and `allowed_backends`
- assert `run_attack_script(..., scenario_name="aws-public-s3")` rejects a policy that only allows another scenario
- assert `run_attack_script(..., backend_name="localstack-aws")` rejects a policy that only allows another backend
- assert `nullstate run --policy-file` rejects a policy denying the inferred scenario

- [x] **Step 2: Run tests to verify they fail**

Run: `C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_attack_policy -v`

Expected: FAIL because policies do not include or enforce scenario/backend fields yet.

- [x] **Step 3: Implement policy schema extension**

Update `AttackPolicy` with optional sets:

- `allowed_scenarios: set[str] | None`
- `allowed_backends: set[str] | None`

Update `default_policy_payload()` to include explicit allowlists for the current scenario/backend names.

- [x] **Step 4: Enforce policy context in runner and CLI**

Update `enforce_attack_policy()` and `run_attack_script()` to accept optional `scenario_name` and `backend_name`. The CLI should pass `scenario_spec.name` and `backend.name` for both before and after attack tool executions.

- [x] **Step 5: Run focused tests**

Run: `C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_attack_policy -v`

Expected: PASS.

- [x] **Step 6: Update docs and progress tracking**

Document the new fields and mark richer policy scope as implemented.

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
git commit -m "feat: add policy scenario backend allowlists"
git push origin feature/red-agent-runner
```
