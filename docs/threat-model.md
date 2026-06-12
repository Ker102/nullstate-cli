# Threat Model - nullstate

## System overview

nullstate is a local-first CLI that analyzes IaC, runs or simulates sandbox attacks, uses red/blue model roles, applies remediation in a copied workspace, and emits evidence artifacts.

## Assets

| Asset | Why it matters | Sensitivity |
|---|---|---|
| IaC source | may reveal architecture and secrets | medium/high |
| Run workspace | contains copied IaC and remediation | medium |
| Model API key | grants access to model endpoint | high |
| LocalStack token | grants access to LocalStack Azure image | high |
| Reports | public-facing evidence | low/medium after sanitization |

## Trust boundaries

- User shell to CLI.
- CLI to Docker/LocalStack/kind.
- CLI to model endpoint.
- Generated attack script to local run directory.
- Repository docs to public internet.

## Actors

| Actor | Goal | Trust level |
|---|---|---|
| Operator | Validate local IaC security | trusted |
| External attacker | Abuse published artifacts or exposed sandbox | untrusted |
| Red agent | Find attack path in sandbox | partially trusted |
| Blue agent | Generate remediation | partially trusted |
| Compromised dependency | Execute malicious code | untrusted |

## Threats

| Threat | Impact | Likelihood | Control | Evidence |
|---|---|---|---|---|
| Real cloud target hit accidentally | High | Medium | LocalStack/plan-only defaults | CLI target docs |
| Secret committed | High | Medium | `.gitignore`, `.env.example`, SECURITY.md | repo files |
| Agent escapes sandbox | High | Medium | allowlisted backend commands, copied workspace | sandbox module |
| Dependency compromise | High | Medium | Dependabot, pip-audit, dependency review | workflows |
| Misleading model output | Medium | High | deterministic detector and patch validator | tests |

## Abuse cases

- User accidentally points at production Terraform state.
- Malicious dependency reads environment variables during CI.
- Generated report includes a real token or private endpoint.
- Red agent suggests actions outside LocalStack.
- Sandbox container exposes a port unexpectedly.

## Residual risks

- Local Docker security depends on the operator machine.
- LocalStack Azure feature coverage may differ from real Azure.
- CI cannot enforce branch protection until configured in GitHub repository settings.

## Next improvements

- Add `nullstate scrub runs/<id>`.
- Expand release SBOMs from declared dependencies to resolved dependency lock data.
- Add explicit policy file for red-team tool permissions.
