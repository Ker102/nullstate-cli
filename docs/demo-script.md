# Demo Script

## 60-Second Version

1. "This is `nullstate`, a local-first purple-team CLI for Terraform security validation."
2. "It reads IaC, runs a local sandbox scenario, uses a model for red/blue reasoning, executes an allowlisted attack script, applies a deterministic Terraform patch, and validates that the attack path is blocked."
3. Run:

```powershell
python -m nullstate
python -m nullstate status
python -m nullstate run examples/aws-public-s3 --target localstack-aws --runs-dir runs/final-aws-gemma26b --red-model nullstate-gemma4-26b-a4b --blue-model nullstate-gemma4-26b-a4b
python -m nullstate report --runs-dir runs/final-aws-gemma26b
```

4. Show the terminal summary:
   - Finding count
   - Red before: success
   - Red after: blocked
   - Artifact path
5. Show `events.jsonl` and point out the `red-tool` entries. They include command, stdout, stderr, return code, target URL, and timestamps.
6. Show the report output and the run directory path. The same report can be reopened with `python -m nullstate report` or `python -m nullstate report <run-id> --runs-dir runs`.

## MI300X Talking Points

- The CLI is designed for huge IaC plans and long security logs.
- MI300X is used for long-context blue-team analysis through an OpenAI-compatible vLLM or SGLang endpoint.
- The deterministic core keeps the security verdict reproducible; the model adds reasoning, explanation, and remediation context.
- Users do not manually prompt the model; nullstate sends role-specific agent instructions and evidence.
- Token metrics come from model API usage fields and vLLM Prometheus metrics when available.
- The red command runner is intentionally constrained to generated `attack.py` scripts inside the run directory.

## Fallback Path

If LocalStack Azure or the model endpoint is unavailable, use `--offline`. The same CLI and report flow still works.

## Live Sandbox Shot

When LocalStack is configured, show the guided sequence. Run AWS and Azure sequentially because both use LocalStack edge port `4566`.

```powershell
python -m nullstate sandbox up localstack-aws
python -m nullstate sandbox status localstack-aws
python -m nullstate run examples/aws-public-s3 --target localstack-aws --runs-dir runs/final-aws-gemma26b --red-model nullstate-gemma4-26b-a4b --blue-model nullstate-gemma4-26b-a4b
python -m nullstate report --runs-dir runs/final-aws-gemma26b

python -m nullstate sandbox down localstack-aws

python -m nullstate sandbox up localstack-azure
python -m nullstate sandbox status localstack-azure
python -m nullstate run examples/azure-public-blob --target localstack-azure --runs-dir runs/final-azure-gemma26b --red-model nullstate-gemma4-26b-a4b --blue-model nullstate-gemma4-26b-a4b
python -m nullstate report --runs-dir runs/final-azure-gemma26b
```

Keep `LOCALSTACK_AUTH_TOKEN` in `.env.local`, `.env`, or the shell. Do not show token values in the recording.

## Accuracy Note

Do not say the red model has unrestricted shell access. In V1, the model produces red-team attack reasoning, and nullstate executes only generated `attack.py` scripts inside the run directory against configured local targets.
