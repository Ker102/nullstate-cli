# Real Sandbox Red-Team Commands Implementation Plan

> **For Agent:** Use executing-plans skill to implement this plan task-by-task.

**Goal:** Replace shallow LocalStack health probes with scenario-specific red-team probes that attempt real sandbox reads before and after remediation while preserving strict command boundaries.

**Architecture:** Keep the existing constrained `attack.py` runner. Move exploit logic into scenario templates that receive a target URL, stage, and a generated evidence manifest. The deterministic detector remains the source of truth, but the report distinguishes between configuration validation and real runtime exploit evidence.

**Tech Stack:** Python standard library, Terraform, LocalStack AWS/Azure, Typer/Rich CLI, unittest, Ruff, mypy.

---

## Current State

The current red-team execution feature is safe but shallow:

- `src/nullstate/attack_runner.py` executes only generated `attack.py` inside the run directory.
- `events.jsonl` records command, stdout, stderr, return code, target URL, stage, timestamps, and duration.
- AWS/Azure `attack.py` scripts currently call `/_localstack/health` when online.
- The before/after `success` and `blocked` verdict still comes from `simulate_attack()`.

This is a strong security boundary, but not yet a full enterprise exploit validation engine.

## Progress Status

Updated 2026-06-01:

- Completed locally: Task 1 attack evidence manifest.
- Completed locally: Task 2 safe runner manifest argument.
- Completed locally: initial platform foundation outside this plan:
  - `nullstate bundle`
  - `run-bundle.json`
  - `nullstate dashboard`
  - `dashboard.html`
- Not pushed: the branch is ahead of origin with local-only commits.
- Freeze rule: do not merge to `main`, do not push unless the user explicitly asks.

Next task to execute:

```text
Task 3: Make AWS S3 Scenario Actually Read Sandbox Evidence
```

## Target State

For AWS S3 and Azure Blob:

1. Terraform creates an intentionally exposed object/blob in the sandbox.
2. The red command attempts anonymous read/list access against the sandbox endpoint.
3. The before-remediation command returns evidence that the object/blob was reachable.
4. Remediation removes the exposure.
5. The after-remediation command returns evidence that the same read/list path is denied or unavailable.
6. `report.md` clearly separates:
   - model reasoning
   - command evidence
   - deterministic config validation
   - final verdict

## Enterprise Reliability Rule

A finding should not be labeled as “exploited” unless at least one of these is true:

- runtime attack command observed access to the target object/blob; or
- the run is explicitly offline/mock and the report labels it as deterministic simulation.

## Task 1: Add Attack Evidence Manifest

Status: completed locally in commit `55775a7 feat: add attack manifest foundation`.

**Files:**
- Create: `src/nullstate/attack_manifest.py`
- Modify: `src/nullstate/cli.py`
- Test: `tests/test_attack_manifest.py`

**Step 1: Write failing tests**

Create tests for a manifest shaped like:

```json
{
  "scenario": "aws-public-s3",
  "backend": "localstack-aws",
  "target_url": "http://localhost.localstack.cloud:4566",
  "resources": {
    "bucket_hint": "nullstate-public-logs",
    "object_key": "evidence.txt"
  }
}
```

Expected behavior:

- manifest writes to `runs/<id>/attack-manifest.json`
- manifest is passed to `attack.py` as `--manifest attack-manifest.json`
- manifest path must live inside the run directory

**Step 2: Implement minimal manifest writer**

Add a dataclass or function:

```python
def write_attack_manifest(path: Path, *, scenario_name: str, backend_name: str, target_url: str, workspace_dir: Path) -> dict[str, object]:
    ...
```

For V1, infer resource hints from Terraform text or plan values.

**Step 3: Run tests**

```powershell
python -m unittest tests.test_attack_manifest -v
python -m ruff check src tests
python -m mypy src
```

**Step 4: Commit locally only**

```powershell
git add src/nullstate/attack_manifest.py src/nullstate/cli.py tests/test_attack_manifest.py
git commit -m "feat: add attack evidence manifest"
```

Do not merge to main during the hackathon freeze.

---

## Task 2: Extend Attack Runner Arguments Safely

Status: completed locally in commit `55775a7 feat: add attack manifest foundation`.

**Files:**
- Modify: `src/nullstate/attack_runner.py`
- Modify: `tests/test_attack_runner.py`

**Step 1: Write failing test**

Assert runner command includes:

```text
python attack.py --target-url <url> --stage before --manifest <run-dir>/attack-manifest.json
```

Reject manifests outside the run directory.

**Step 2: Implement**

Add optional `manifest_path: Path | None` parameter to `run_attack_script()`.

Validation:

- if present, manifest must be a file
- manifest must live directly inside run dir
- command still uses no shell

**Step 3: Run tests**

```powershell
python -m unittest tests.test_attack_runner -v
```

---

## Task 3: Make AWS S3 Scenario Actually Read Sandbox Evidence

Status: next.

**Files:**
- Modify: `examples/aws-public-s3/main.tf`
- Modify: `src/nullstate/attack.py`
- Modify: `src/nullstate/findings.py`
- Modify: `tests/test_scenarios.py`
- Modify: `tests/test_attack_runner.py`

**Design:**

Current AWS example only disables public access block. That is risky, but not sufficient to prove anonymous reads by itself. Add intentionally public evidence resources for the demo fixture:

- `aws_s3_object` with key `evidence.txt`
- public bucket policy allowing `s3:GetObject` for the evidence path, if LocalStack supports it reliably

The attack script should try anonymous HTTP GET against path-style or virtual-host-style LocalStack S3 URL.

Example request candidates:

```text
http://s3.localhost.localstack.cloud:4566/<bucket>/evidence.txt
http://<bucket>.s3.localhost.localstack.cloud:4566/evidence.txt
```

The script should print:

- candidate URL
- HTTP status
- first bytes of response body if accessible
- denial/error if blocked

**Success criteria:**

- before stage: command returns `0` only if object read returns a 2xx response
- after stage: command returns non-zero or prints denied/unavailable
- report includes actual stdout evidence

**Risk:**

LocalStack public S3 semantics may differ from AWS. If public policy behavior is inconsistent, keep runtime evidence labeled “LocalStack exploit probe” and keep deterministic config validation separate.

---

## Task 4: Make Azure Blob Scenario Use Real Blob Probe Where Supported

**Files:**
- Modify: `examples/azure-public-blob/main.tf`
- Modify: `src/nullstate/attack.py`
- Modify: `src/nullstate/attack_manifest.py`
- Test: new Azure attack script tests

**Design:**

Add or infer a blob object if LocalStack Azure supports the relevant resource. The attack script should attempt anonymous HTTP GET/list for the container/blob URL.

If LocalStack Azure support is inconsistent, implement a two-level probe:

1. runtime endpoint probe with explicit stdout explaining support status
2. deterministic IaC validation as the final verdict source

Do not overclaim Azure runtime exploitation if the emulator cannot prove it reliably.

---

## Task 5: Report Runtime Evidence Separately

**Files:**
- Modify: `src/nullstate/report.py`
- Modify: `tests/test_report.py`

Add a “Runtime command evidence” section:

```markdown
## Runtime command evidence

### Before remediation
- Command: `python attack.py ...`
- Return code: 0
- Target: http://localhost.localstack.cloud:4566
- Stdout excerpt: ...

### After remediation
- Command: `python attack.py ...`
- Return code: 2
- Target: http://localhost.localstack.cloud:4566
- Stdout excerpt: ...
```

Report language must distinguish:

- “runtime exploit observed”
- “runtime probe inconclusive”
- “offline deterministic simulation”

---

## Task 6: Enterprise Guardrails

**Files:**
- Modify: `docs/security-model.md`
- Modify: `docs/technical-walkthrough.md`
- Create: `docs/enterprise-readiness.md`

Add enterprise controls:

- local-only target enforcement
- explicit `--allow-live-cloud` future gate for real cloud, default off
- artifact scrubber before publish
- command allowlist policy
- timeout and max stdout/stderr capture length
- red-team command schema version in events
- reproducibility hash for generated `attack.py`

---

## Validation Before Completion

Run:

```powershell
python -m unittest discover -s tests -v
python -m ruff check src tests
python -m mypy src
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --runs-dir runs/real-red-smoke
```

If LocalStack is available, run:

```powershell
python -m nullstate sandbox up localstack-aws
python -m nullstate run examples/aws-public-s3 --target localstack-aws --runs-dir runs/live-real-red-aws
python -m nullstate report --runs-dir runs/live-real-red-aws
python -m nullstate sandbox down localstack-aws
```
