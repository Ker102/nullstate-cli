# Policy Target Host Allowlists Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add policy-level target host allowlists so future live-cloud probes require both operator approval and an explicit host constraint.

**Architecture:** Keep the runner's default local-only network gate unchanged. Add an optional `allowed_target_hosts` policy field that is enforced after URL classification and before generated `attack.py` execution. Newly generated policies include conservative local defaults; older policy files that omit the field remain compatible.

**Tech Stack:** Python 3.11+, Typer CLI, JSON policy artifacts, `unittest`.

---

### Task 1: Define Expected Policy Behavior

**Files:**
- Modify: `tests/test_attack_policy.py`

- [x] **Step 1: Write failing tests**

Add tests that assert:

```python
self.assertIn("localhost", payload["allowed_target_hosts"])
self.assertIn("localhost.localstack.cloud", payload["allowed_target_hosts"])
```

Add runner tests that build `AttackPolicy(..., allowed_target_hosts={...})` and verify:

```python
with self.assertRaisesRegex(ValueError, "target host"):
    run_attack_script(..., target_url="https://storage.example.com/blob", allow_live_cloud=True, policy=policy)
```

and:

```python
result = run_attack_script(
    ...,
    target_url="https://demo.blob.core.windows.net/container/evidence.txt",
    allow_live_cloud=True,
    policy=policy,
)
self.assertEqual(result.target_classification, "external-http")
```

- [x] **Step 2: Verify the tests fail**

Run:

```powershell
python -m unittest tests.test_attack_policy -v
```

Expected: FAIL because `AttackPolicy` and generated policies do not yet understand `allowed_target_hosts`.

### Task 2: Implement Host Allowlist Enforcement

**Files:**
- Modify: `src/nullstate/policy.py`
- Modify: `src/nullstate/attack_runner.py`

- [x] **Step 1: Extend policy data**

Add default local host values:

```python
DEFAULT_ALLOWED_TARGET_HOSTS = {"localhost", "127.0.0.1", "::1", "localhost.localstack.cloud", "*.localhost.localstack.cloud"}
```

Add optional policy field:

```python
allowed_target_hosts: set[str] | None = None
```

- [x] **Step 2: Enforce target hosts**

Pass the raw target URL into `enforce_attack_policy()`. For HTTP(S) targets and policies that include `allowed_target_hosts`, extract the hostname with `urlparse(target_url).hostname`, normalize it to lowercase, and require either an exact match or a suffix match for patterns beginning with `*.`.

- [x] **Step 3: Verify focused tests pass**

Run:

```powershell
python -m unittest tests.test_attack_policy tests.test_attack_runner -v
```

Expected: PASS.

### Task 3: Document and Checkpoint

**Files:**
- Modify: `README.md`
- Modify: `docs/enterprise-readiness.md`
- Modify: `docs/security-model.md`
- Modify: `docs/technical-walkthrough.md`
- Modify: `docs/handoff.md`
- Modify: `docs/progress.md`

- [x] **Step 1: Update docs**

Document that non-local targets require:

```text
--allow-live-cloud
allowed_target_classifications including external-http
allowed_target_hosts matching the target hostname
```

- [x] **Step 2: Verify full quality gates**

Run:

```powershell
python -m ruff check src tests
python -m mypy src
python -m unittest discover -s tests -v
git diff --check
```

- [x] **Step 3: Commit and push**

Run:

```powershell
git add .
git commit -m "feat: add target host policy allowlists"
git push
gh pr checks 24 --watch --interval 10
```
