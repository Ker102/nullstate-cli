# Security Policy

## Supported Versions

`nullstate` is pre-1.0. Security fixes target the latest `main` branch and the newest prerelease tag when a fix needs to be published for evaluators.

| Version | Supported |
|---|---|
| `main` | yes |
| latest prerelease | yes |
| older prereleases | best effort |

## Reporting a Vulnerability

Do not open public issues for exploitable vulnerabilities in nullstate itself. Contact the maintainer privately or use GitHub private vulnerability reporting if it is enabled for the repository. Publish details only after a fix or mitigation is available.

## Security Boundaries

nullstate is designed to test intentionally vulnerable local sandboxes. It must not be pointed at production infrastructure unless the operator owns the environment and understands the risk.

V1 defaults:

- no real Azure execution by default
- LocalStack/Docker sandboxes only when explicitly started
- run artifacts are local files
- secrets should be supplied through environment variables, not committed files
- constrained red-team probes execute generated run-directory `attack.py` only
- non-local HTTP probe targets require explicit operator approval and policy controls

## Secret Handling

Never commit:

- `LOCALSTACK_AUTH_TOKEN`
- model API keys
- cloud credentials
- Terraform state
- `.env`
- real `.tfvars`

Use `.env.example` for documented configuration.

Before attaching run artifacts to issues, tickets, case studies, or support requests:

```powershell
nullstate scrub
```

Attach the scrubbed copy from `scrubbed-runs/`, not the raw `runs/` directory.
