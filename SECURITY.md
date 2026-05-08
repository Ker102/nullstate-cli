# Security Policy

## Supported Versions

The hackathon prototype is pre-1.0. Security fixes target the latest `main` branch until the first tagged release.

## Reporting a Vulnerability

Do not open public issues for exploitable vulnerabilities in nullstate itself. Contact the maintainer privately, then publish details only after a fix or mitigation is available.

## Security Boundaries

nullstate is designed to test intentionally vulnerable local sandboxes. It must not be pointed at production infrastructure unless the operator owns the environment and understands the risk.

V1 defaults:

- no real Azure execution by default
- LocalStack/Docker sandboxes only when explicitly started
- run artifacts are local files
- secrets should be supplied through environment variables, not committed files

## Secret Handling

Never commit:

- `LOCALSTACK_AUTH_TOKEN`
- model API keys
- cloud credentials
- Terraform state
- `.env`
- real `.tfvars`

Use `.env.example` for documented configuration.
