# Demo Script

## 60-Second Version

1. "This is `nullstate`, an autonomous purple-team CLI for Terraform Azure."
2. "It reads IaC, spins a local security scenario, lets a red agent exploit it, lets a blue agent patch it, then validates the fix."
3. Run:

```powershell
python -m nullstate run examples/azure-public-blob --offline
```

4. Show the terminal summary:
   - Finding count
   - Red before: success
   - Red after: blocked
   - Artifact path
5. Open `report.md` and show the before/after evidence plus patch.

## MI300X Talking Points

- The CLI is designed for huge IaC plans and long security logs.
- MI300X is used for long-context blue-team analysis through an OpenAI-compatible vLLM or SGLang endpoint.
- The deterministic core keeps the security verdict reproducible; the model adds reasoning, explanation, and remediation context.
- Users do not manually prompt the model; nullstate sends role-specific agent instructions and evidence.
- Token metrics come from model API usage fields and vLLM Prometheus metrics when available.

## Fallback Path

If LocalStack Azure or the model endpoint is unavailable, use `--offline`. The same CLI and report flow still works.
