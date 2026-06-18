# Failure Modes

## LocalStack Azure unavailable

Impact: live sandbox execution cannot run.

Fallback: use `--offline` or `--target plan-only`.

## Missing Docker

Impact: executable local sandboxes cannot start.

Fallback: plan-only mode still parses IaC and generates reports.

## Missing model endpoint

Impact: real red/blue model calls cannot run.

Fallback: offline mock agents preserve the full demo flow.

## Unknown model provider

Impact: the CLI cannot infer the OpenAI-compatible URL for model calls.

Fallback: set `NULLSTATE_LLM_PROVIDER` to `custom`, `google`, or `claude`. For custom/self-hosted models, also set `NULLSTATE_LLM_BASE_URL` or role-specific red/blue base URLs.

## Terraform provider mismatch

Impact: live `terraform init` or `plan` can fail.

Fallback: offline static parser works for the demo fixture.

## Model output is wrong

Impact: explanation or remediation text may be misleading.

Control: deterministic detector and deterministic remediation are the source of truth for V1.

## Report includes sensitive data

Impact: public case study leaks private information.

Control: review artifacts before publishing; run `nullstate scrub` first and review `scrub-report.json`.
