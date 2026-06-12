# Policy Scenario Presets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add scenario-scoped policy presets so `nullstate policy init --scenario <name>` creates a tighter red-tool policy for one scenario/backend pair.

**Architecture:** Keep the existing broad `policy init` behavior unchanged when no scenario is provided. Add a small policy payload helper that reads the scenario registry and returns the same policy schema with `allowed_scenarios` and `allowed_backends` narrowed to the requested scenario. The CLI validates unknown scenario names through the existing `get_scenario()` lookup and prints the selected preset in the command output.

**Tech Stack:** Python 3.11+, Typer CLI, JSON policy artifacts, `unittest`.

---

### Task 1: Scenario Preset Policy Payload

**Files:**
- Modify: `tests/test_attack_policy.py`
- Modify: `src/nullstate/policy.py`
- Modify: `src/nullstate/cli.py`
- Modify: `README.md`
- Modify: `docs/technical-walkthrough.md`
- Modify: `docs/enterprise-readiness.md`
- Modify: `docs/progress.md`
- Modify: `docs/handoff.md`

- [x] **Step 1: Write failing tests**

Add tests that verify:

- `nullstate policy init --scenario aws-public-s3` writes `allowed_scenarios: ["aws-public-s3"]`.
- the same preset writes `allowed_backends: ["localstack-aws"]`.
- broad fields such as `allowed_target_classifications`, `allowed_command_policy_ids`, `allowed_stages`, `allowed_attack_script_args`, `max_timeout_seconds`, and `max_output_bytes` remain present.
- the generated payload records `preset: "scenario:aws-public-s3"`.
- an unknown scenario exits nonzero and mentions `Unknown scenario`.

- [x] **Step 2: Run tests to verify they fail**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_attack_policy -v
```

Expected: FAIL because `policy init` has no `--scenario` option yet.

- [x] **Step 3: Add preset helper**

In `src/nullstate/policy.py`, add:

```python
def scenario_policy_payload(scenario_name: str, backend_name: str) -> dict[str, Any]:
    payload = default_policy_payload()
    payload["preset"] = f"scenario:{scenario_name}"
    payload["allowed_scenarios"] = [scenario_name]
    payload["allowed_backends"] = [backend_name]
    payload["notes"] = (
        "Controls constrained red-tool execution for one scenario/backend pair. "
        "This does not grant arbitrary shell access."
    )
    return payload
```

Update `write_default_policy()` to accept optional `scenario_name` and `backend_name` keyword arguments, choosing `scenario_policy_payload()` when both are provided.

- [x] **Step 4: Add CLI option**

In `src/nullstate/cli.py`, add a `--scenario` option to `policy init`. When supplied, call `get_scenario(scenario)` and pass the scenario name/backend into `write_default_policy()`. Convert `KeyError` to `typer.BadParameter`.

- [x] **Step 5: Run focused tests**

Run:

```powershell
C:\Users\ivo\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_attack_policy -v
```

Expected: PASS.

- [x] **Step 6: Update docs and progress tracking**

Document the new command:

```powershell
nullstate policy init --scenario aws-public-s3 --output aws-policy.json
```

Clarify that scenario presets narrow the generated allowlists but do not change runtime enforcement semantics.

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
git commit -m "feat: add scenario policy presets"
```
