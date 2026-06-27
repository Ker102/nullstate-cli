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
| Agent identity and delegation graph | reveals agent permissions, user delegation, tools, and reachable systems | high |
| Agent memory and tool configuration | may contain instructions, credentials, retrieved data, and trusted integration details | high |

## Trust boundaries

- User shell to CLI.
- CLI to Docker/LocalStack/kind.
- CLI to model endpoint.
- AI agent to cloud identity provider, tool gateway, downstream service, and delegated user context.
- Generated attack script to local run directory.
- Repository docs to public internet.

## Actors

| Actor | Goal | Trust level |
|---|---|---|
| Operator | Validate local IaC security | trusted |
| External attacker | Abuse published artifacts or exposed sandbox | untrusted |
| Red agent | Find attack path in sandbox | partially trusted |
| Blue agent | Generate remediation | partially trusted |
| Customer AI agent | Operate cloud resources through its own or delegated identity | partially trusted |
| Compromised agent tool or memory source | Influence agent decisions or misuse its authority | untrusted |
| Compromised dependency | Execute malicious code | untrusted |

## Threats

| Threat | Impact | Likelihood | Control | Evidence |
|---|---|---|---|---|
| Real cloud target hit accidentally | High | Medium | LocalStack/plan-only defaults | CLI target docs |
| Secret committed | High | Medium | `.gitignore`, `.env.example`, SECURITY.md | repo files |
| Agent escapes sandbox | High | Medium | allowlisted backend commands, copied workspace | sandbox module |
| Dependency compromise | High | Medium | Dependabot, pip-audit, dependency review | workflows |
| Misleading model output | Medium | High | deterministic detector and patch validator | tests |
| Compromised AI agent misuses cloud authority | High | Medium | identity-aware graph, least privilege, delegated-context separation, controlled validation | future agent identity adapter |
| Privileged agent becomes a confused deputy | High | Medium | caller/delegation attribution, policy checks, per-tool authorization | future agent identity adapter |
| Shared agent runtime identity hides attribution | High | Medium | require distinct agent/runtime/tool identity evidence where supported | future identity inventory |
| External agent host is compromised while its tenant identity remains valid | High | Medium | runtime posture evidence, short-lived federation, authorization gateway, least privilege, revocation | future posture collector |
| Forged or stale runtime posture is accepted | High | Medium | signed evidence, issuer verification, timestamps, freshness policy, fail-closed high-impact access | future posture verifier |

## Abuse cases

- User accidentally points at production Terraform state.
- Malicious dependency reads environment variables during CI.
- Generated report includes a real token or private endpoint.
- Red agent suggests actions outside LocalStack.
- Sandbox container exposes a port unexpectedly.
- Prompt injection causes a cloud-management agent to invoke a legitimate tool with harmful parameters.
- An agent acting for a low-privilege user retains or acquires broader service-principal permissions.
- A compromised MCP server, connector, plugin, memory item, or retrieved document redirects agent actions.
- Multiple agents share one privileged runtime identity, obscuring which agent initiated a change.
- An agent obtains a downstream credential whose scope or lifetime exceeds the original task.
- A third-party agent presents a valid identity from a vulnerable host and uses approved permissions maliciously.
- An operator treats an image signature or hardware attestation as proof that the complete agent application is safe.

## Residual risks

- Local Docker security depends on the operator machine.
- LocalStack Azure feature coverage may differ from real Azure.
- CI cannot enforce branch protection until configured in GitHub repository settings.
- Provider-native agent identity systems and delegated authorization flows are evolving and require provider-specific inventory and evidence.

## Next improvements

- Run live LocalStack Azure validation when the account has Azure Emulator entitlement.
- Add live-cloud adapters only with provider-specific endpoint allowlists and approval workflows.
- Add AWS and Azure agent identity inventory covering native agent identities, conventional workload identities, delegated users, tool identities, and downstream credentials.
- Add external runtime posture evidence with explicit verified, observed, operator-attested, inferred, and unknown classifications.
