# Policy Validation Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `nullstate policy validate` so teams can check red-tool policy files in CI without running a scenario.

**Architecture:** Reuse the existing policy loader as the source of truth. Add a small validation payload builder that returns pass/fail status, parsed field counts, warnings for omitted optional constraints, and an error message for malformed policies. The CLI prints a short summary, optionally writes `policy-validation.json`, and exits `2` for invalid policies.

**Tech Stack:** Python 3.11+, Typer CLI, `unittest`, JSON policy artifacts.

---

### Task 1: Policy Validate Command

**Files:**
- Modify: `tests/test_attack_policy.py`
- Modify: `src/nullstate/policy.py`
- Modify: `src/nullstate/cli.py`
- Modify: `README.md`
- Modify: `docs/ci-cd.md`
- Modify: `docs/technical-walkthrough.md`
- Modify: `docs/enterprise-readiness.md`
- Modify: `docs/progress.md`

- [x] **Step 1: Write failing tests**

Add tests that:

- run `nullstate policy validate <policy-file>`
- assert valid policies exit `0`
- assert optional `--output policy-validation.json` writes structured status
- assert malformed policies exit `2` and write invalid status when `--output` is supplied

- [x] **Step 2: Run tests to verify they fail**

Run: `C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_attack_policy -v`

Expected: FAIL because `policy validate` does not exist yet.

- [x] **Step 3: Implement validation helper**

Add `build_policy_validation(path: Path) -> dict[str, Any]` and `write_policy_validation(path: Path, output_path: Path) -> dict[str, Any]` to `src/nullstate/policy.py`.

- [x] **Step 4: Implement CLI command**

Add `nullstate policy validate` under the policy Typer app. It should accept a policy path argument defaulting to `nullstate-policy.json`, optional `--output`, print status, and exit `2` when invalid.

- [x] **Step 5: Run focused tests**

Run: `C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_attack_policy -v`

Expected: PASS.

- [x] **Step 6: Update docs and progress tracking**

Document the command in README and CI docs, then update progress/readiness/walkthrough.

- [x] **Step 7: Full verification**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m ruff check src tests
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m mypy src
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest discover -s tests -v
git diff --cached --check
```

Expected: all commands exit `0`.

- [x] **Step 8: Checkpoint and PR**

Commit, push `feature/red-agent-runner`, and open a draft PR to `main` without merging.
