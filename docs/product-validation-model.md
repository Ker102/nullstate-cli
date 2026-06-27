# Product and Validation Model

## Product purpose

Nullstate is an evidence-backed cloud attack-path validation platform. It correlates infrastructure-as-code with observed AWS and Azure state, reasons across network, identity, service, and data relationships, validates selected attack paths inside controlled environments, applies remediation, and replays the attack.

The product is not intended to require a perfect Terraform representation of an entire cloud account. IaC describes intended and managed configuration, while read-only discovery describes deployed reality. Nullstate should combine both into a normalized environment graph and preserve the source and confidence of every relationship.

## Environment graph

The environment graph should accept:

- Terraform, CloudFormation, CDK exports, Bicep, ARM, and provider plan/state data.
- AWS and Azure read-only resource inventory.
- IAM roles, Azure RBAC assignments, managed identities, trust relationships, and workload identities.
- AI agent identities, agent identity blueprints, agent workload identities, delegated user context, tool identities, and downstream credential relationships.
- Public endpoints, virtual networks, security groups, NSGs, routes, gateways, private endpoints, and peering.
- Storage, database, secret-management, compute, serverless, container, and Kubernetes configuration.
- Native security findings, activity logs, flow logs, audit logs, and selected runtime metadata.
- Optional data classification supplied by the user or inferred from safe metadata and synthetic fixtures.

The graph does not need to clone every resource. It must identify security-relevant paths and create a minimal attack-path twin containing only the relationships required to test a hypothesis.

## Identity-aware attack analysis

An open port or public container is not the whole finding. Nullstate should evaluate what each authorized attacker perspective can reach:

| Perspective | Example |
|---|---|
| External | Anonymous internet client |
| Tenant user | Authenticated but low-privilege cloud user |
| Developer | Human identity with deployment or read permissions |
| CI workload | GitHub Actions, GitLab, or build-system identity |
| Compromised workload | VM, container, function, or application identity |
| Cloud role | AWS IAM role, Azure service principal, or managed identity |
| AI agent | Dedicated agent identity, agent workload identity, or agent runtime role |
| Delegated agent | Agent acting with authority propagated from a human user |
| Lateral actor | Principal obtained through an earlier attack-path step |

Each observed result should record the principal, assumed permissions, authentication method, target, data or capability reached, command evidence, and confidence.

## AI agents as cloud principals

AI agents increasingly interact with infrastructure, cloud APIs, internal services, data stores, ticketing systems, source repositories, and deployment tools. They may operate through:

- a dedicated identity created specifically for the agent
- a conventional service principal, managed identity, IAM role, or workload identity
- a runtime or tool identity shared by multiple agents
- delegated authority propagated from a human user
- credentials acquired for downstream tools or third-party services

These modes must not be collapsed into one generic service account. Nullstate should represent the agent, runtime, tool, delegated user, credentials, and target service as separate graph nodes. This preserves who initiated an action, whose permissions authorized it, and which component could be compromised.

Agent-specific attack paths include:

- prompt injection causing the agent to misuse legitimate cloud permissions
- compromised tools, plugins, MCP servers, memory, or retrieved content influencing actions
- excessive agency allowing destructive or privilege-changing operations outside the intended task
- a confused-deputy path where an untrusted user causes a privileged agent to act on their behalf
- delegated user authority reaching resources that the agent's own identity could not access
- shared runtime identities making attribution and least privilege ineffective
- agent-to-agent trust enabling lateral movement
- long-lived or broadly scoped downstream credentials increasing the blast radius

Nullstate should evaluate at least three separate permission views:

1. **Agent-native permissions:** resources reachable using the agent's own identity.
2. **Delegated permissions:** resources reachable when acting on behalf of a specific user or user class.
3. **Tool-chain permissions:** resources reachable through runtime identities, plugins, gateways, connectors, and downstream credentials.

The report should explain the effective permission chain and identify the data and operations exposed if the agent, its instructions, memory, or one of its tools is compromised. Safe validation should use synthetic prompts, synthetic data, controlled tools, and disposable environments instead of attempting uncontrolled prompt injection against production agents.

For externally hosted agents, identity analysis alone is insufficient. Nullstate should also assess runtime posture: workload-to-identity binding, artifact provenance, deployment digest, host and runtime integrity, network exposure, tool controls, logging, revocation, and the freshness and strength of supporting evidence. The detailed design is in [External Agent Trust and Runtime Posture](plans/2026-06-22-external-agent-trust-design.md).

The current CLI includes an initial deterministic preview of this model:

```bash
nullstate agent posture verify examples/agent-trust/external-agent-manifest.json
nullstate agent blast-radius examples/agent-trust/external-agent-manifest.json
```

These commands operate on a local manifest, not on live provider collectors. They are intended to harden the data contract first: missing, stale, or unknown posture evidence must remain visible, and delegated-user authority must be separated from the agent's own identity.

## Exposed data and impact

Cloud administrators may intentionally accept a reachable service because they believe it contains nothing critical. Nullstate should still identify whether the path exposes:

- object names, directory listings, account IDs, tenant IDs, hostnames, or internal topology
- application logs, backups, diagnostics, build artifacts, source maps, or deployment packages
- credentials, tokens, connection strings, configuration, or secret references
- personal, financial, regulated, customer, or proprietary data
- write, delete, impersonation, execution, or policy-changing capabilities
- information that enables credential attacks, lateral movement, privilege escalation, or targeted social engineering

Reports must distinguish:

- configuration suggests exposure
- safe metadata was observed
- synthetic evidence data was retrieved
- a privileged capability was demonstrated
- production-sensitive content was intentionally not accessed

## Why not attack production directly?

Read-only discovery and narrowly approved non-destructive validation may run against production. Autonomous exploitation should default to a controlled environment because:

1. Exploits can modify, delete, corrupt, or expose real data.
2. Probes can cause throttling, outages, account lockouts, quarantine, or incident-response activation.
3. IAM testing can create persistent credentials, trust relationships, or privilege changes.
4. Exfiltration tests can violate privacy, contractual, regulatory, and residency requirements.
5. Production dependencies can affect customers and third parties outside the approved scope.
6. Cleanup cannot guarantee restoration of the exact previous state.
7. Repeated CI validation must be deterministic and safe enough to run without a penetration tester supervising every execution.

The safe operating model is:

1. Discover production through read-only provider APIs.
2. Build and rank attack hypotheses.
3. Run allowlisted non-destructive checks against production only when policy permits.
4. Reconstruct the minimum relevant path using synthetic data in a disposable environment.
5. Execute constrained attacks against that environment.
6. Apply remediation and replay the same attack.
7. Preserve evidence and convert the proven path into a regression test.

## AWS and Azure first

AWS and Azure should be the first cloud providers because they cover a large share of enterprise infrastructure and both have mature IaC ecosystems. Terraform remains a first-class input, not a competing target: Terraform for AWS and Terraform for Azure supply intended topology and configuration, while provider discovery supplies live state and unmanaged drift.

The provider adapters should also inventory emerging agent identity systems. Microsoft Entra Agent ID supplies specialized agent identities and identity blueprints, while Amazon Bedrock AgentCore Identity represents agents through agent/workload identity mechanisms. Nullstate should ingest these relationships alongside conventional service principals, managed identities, and IAM roles without assuming every organization uses a provider-native agent platform.

Provider accuracy should be tiered and explicit:

| Level | Evidence source | Purpose |
|---|---|---|
| Static | IaC, plans, policies, and exported configuration | Fast pre-deployment analysis |
| Observed | Read-only provider inventory and logs | Understand actual deployed state |
| Emulated | LocalStack, service emulators, containers, or digital twins | Safe repeatable validation with known fidelity limits |
| Real sandbox | Disposable AWS account or Azure subscription | Highest-fidelity exploit validation |

Every report should identify the level used. Emulator evidence must never be presented as proof of identical provider behavior.

## CI, cloud-event, and scheduled execution

Nullstate should support three complementary triggers.

### Pull-request and IaC CI

Trigger when Terraform, CloudFormation, Bicep, Helm, policy, or related infrastructure files change.

The pipeline:

1. Analyze the proposed configuration before deployment.
2. Compare findings against an approved baseline.
3. Optionally create a disposable validation environment for high-risk changes.
4. Run selected attack-path regression tests.
5. Export SARIF, a machine-readable policy result, and evidence artifacts.
6. Block the merge when policy thresholds fail.

This is the fastest feedback loop and prevents vulnerable configuration from reaching the cloud.

### Post-deployment validation

Trigger after a successful deployment workflow or provider event.

Examples include a Terraform apply job, CloudFormation deployment, Azure deployment, or cloud event indicating a security-relevant resource or policy change. Nullstate refreshes the observed environment graph, checks for drift, and runs only affected safe validations. Potentially destructive validation is routed to a disposable sandbox rather than the updated production environment.

### Scheduled assurance

Run hourly, daily, or weekly to detect manual console changes, unmanaged resources, permission drift, newly public endpoints, stale accepted risk, and attack paths created by changes outside Git.

These modes solve different problems:

- PR CI validates intended change before deployment.
- Post-deployment validation confirms observed state matches expectations.
- Scheduled assurance catches drift and out-of-band changes.

The mature paid platform can coordinate all three, retain history, notify teams, and supply managed model inference. The open-source CLI remains capable of local and CI execution using customer-provided credentials and model endpoints.

## Provider references

- [Microsoft Entra Agent ID](https://learn.microsoft.com/en-us/entra/agent-id/)
- [Agent identity concepts in Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-identity)
- [Amazon Bedrock AgentCore Identity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity-overview.html)
- [AWS agent identity and permission management guidance](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentsec03.html)
