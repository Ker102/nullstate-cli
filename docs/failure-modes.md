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

## Terraform provider mismatch

Impact: live `terraform init` or `plan` can fail.

Fallback: offline static parser works for the demo fixture.

## Model output is wrong

Impact: explanation or remediation text may be misleading.

Control: deterministic detector and deterministic remediation are the source of truth for V1.

## Report includes sensitive data

Impact: public case study leaks private information.

Control: review artifacts before publishing; future `scrub` command should automate this.
