# Enterprise and Monetization Roadmap

This document frames `nullstate` as a future enterprise DevSecOps product, not only a hackathon CLI.

## Product Positioning

`nullstate` is a local-first purple-team validation platform for infrastructure-as-code. It helps cloud, platform, and security teams prove whether IaC misconfigurations are exploitable, apply deterministic remediation, and preserve evidence for review.

The core message:

> Static scanners tell you what might be wrong. Nullstate proves the attack path, applies the fix, and validates that the path is blocked.

## Target Customers

### Primary

- DevSecOps teams managing Terraform-heavy cloud environments
- Platform engineering teams responsible for secure-by-default IaC modules
- Cloud security teams validating remediation SLAs
- Security consultancies producing evidence-backed remediation reports

### Secondary

- Regulated startups that need audit evidence but cannot send infrastructure data to SaaS tools
- Enterprises exploring private AI for security operations
- MSPs and cloud migration partners

## Core Value Propositions

### 1. Evidence over alerts

Most IaC scanners stop at findings. `nullstate` produces a timeline:

1. finding
2. red-team reasoning
3. sandbox command evidence
4. patch
5. after-remediation validation
6. report

### 2. Local-first and private

Sensitive IaC, Terraform plans, and logs can remain inside the customer environment. Models can run against OpenAI-compatible private endpoints.

### 3. Deterministic security core

The model does not decide pass/fail. Deterministic detection, remediation, and validation keep the product reliable enough for enterprise workflows.

### 4. DevSecOps-native CLI

The first interface is a CLI that can run locally, in CI, or inside ephemeral validation environments.

## Enterprise Product Tiers

### Open Source CLI

Purpose: developer adoption and trust.

Features:

- local/offline runs
- limited scenario library
- report artifacts
- constrained red command runner
- basic LocalStack adapters
- community docs

### Team Edition

Purpose: small teams and consultancies.

Features:

- expanded scenario packs
- HTML/PDF reports
- artifact scrubbing
- baseline comparison
- GitHub Actions/GitLab CI templates
- run history export
- private model endpoint configuration presets

Possible pricing:

- per seat: 19-49 EUR/month
- or per repo: 49-199 EUR/month

### Enterprise Edition

Purpose: larger companies with compliance and private infrastructure needs.

Features:

- policy-as-code controls for attack tooling
- SSO/SAML/OIDC
- audit logs
- centralized run evidence store
- team/role permissions
- private deployment support
- custom scenario development
- enterprise support SLA
- integration with Jira, ServiceNow, Slack, SIEM, and GRC systems

Possible pricing:

- annual contract starting around 15k-50k EUR/year
- custom scenario packs and support as paid add-ons

## Monetization Paths

### Path A: Open-core DevSecOps CLI

Keep core CLI open source. Monetize:

- enterprise scenario packs
- cloud dashboard
- hosted evidence store
- private deployment support
- compliance report exports

Pros:

- strong developer adoption
- GitHub credibility
- easier community trust

Cons:

- needs clear boundary between free and paid
- support load can grow

### Path B: Security Consultancy Tooling

Use `nullstate` as a differentiator for paid security assessments.

Offer:

- IaC purple-team assessment
- Terraform module hardening
- remediation PRs
- audit-ready evidence packs

Pros:

- easiest first revenue
- no full SaaS required
- builds case studies and customer proof

Cons:

- service revenue does not scale as cleanly

### Path C: Enterprise Private AI Security Platform

Position as a private AI security validation layer for IaC and cloud controls.

Pros:

- strong alignment with MI300X/private model narrative
- enterprise budgets are larger

Cons:

- longer sales cycle
- needs more hardening and integrations

## Recommended Near-Term Strategy

Start with a hybrid of Path A and Path B:

1. Keep the CLI open source.
2. Build a strong technical brand around evidence-backed IaC validation.
3. Use portfolio/case study content to win attention.
4. Offer paid assessment or implementation services first.
5. Convert repeated service needs into Team/Enterprise features.

## Product architecture: CLI, local GUI, and paid platform

The CLI should remain the open-source execution engine. It runs locally or in CI, creates run artifacts, and can export a portable run bundle.

The free local GUI should be a single-user viewer/operator surface. It can read local `runs/` folders, generate dashboards, and trigger common CLI actions such as run, report, bundle, and sandbox commands. It should not require cloud login and should not include team, compliance, alerting, or managed-model features.

The paid cloud or self-hosted app should ingest run bundles and provide team dashboards, hosted model calls, centralized evidence history, support workflows, scheduled automation, alerting, integrations, RBAC, audit logs, and compliance exports.

The initial bundle artifact is `run-bundle.json`. It is the contract between the open-source CLI, free local dashboard, CI uploads, support bundles, and the future paid platform.

## CI and managed model inference

CI should support two model modes:

- Customer-provided model mode: users store `NULLSTATE_LLM_BASE_URL` and `NULLSTATE_LLM_API_KEY` in CI secrets.
- Nullstate-managed model mode: users store `NULLSTATE_CLOUD_TOKEN`, and the CLI uses Nullstate Cloud for red/blue model reasoning.

The managed model mode belongs in the paid platform because usage can be metered by organization, project, run, model, tokens, latency, and estimated cost.

## Support, automation, and alerts

Paid users should have an in-app support and feedback panel. A support ticket should be able to attach a sanitized run bundle, product version, run ID, scenario, and dashboard link.

Automation should support scheduled scans against connected repos or uploaded IaC sources. Alert rules should cover new critical findings, observed exploit evidence, remediation failure, CI policy failure, stale unresolved risk, and model endpoint failures. Email and webhooks should be first; Slack, Teams, Jira, GitHub Issues, and SIEM integrations can follow.

## Brand Direction

### Name

`nullstate` is strong because it suggests returning infrastructure risk to a safe baseline state.

### Tagline Options

- Prove, patch, and validate IaC risk.
- Purple-team validation for Terraform security.
- From IaC finding to blocked attack path.
- Evidence-backed DevSecOps for cloud infrastructure.
- Local-first attack validation for infrastructure-as-code.

Recommended primary tagline:

> Prove, patch, and validate IaC risk.

### Brand Personality

- precise
- technical
- trustworthy
- security-first
- enterprise-aware
- not hype-driven

Avoid overclaiming “autonomous hacker agent” until the red tooling is much deeper. Prefer:

- constrained red-team execution
- evidence-backed validation
- local-first purple-team loop

## Enterprise Reliability Requirements

Before businesses can rely on it, the product needs:

1. Real exploit probes for core scenarios.
2. Clear distinction between simulated, inferred, and observed evidence.
3. Policy-defined command allowlists.
4. Artifact scrubbing.
5. Stable scenario schema.
6. CI mode with machine-readable exit codes.
7. SARIF or JSON export for security tooling. SARIF export is now available; JSON policy output remains future work.
8. Reproducible run manifests.
9. Versioned remediation rules.
10. Safe defaults that never target real cloud unless explicitly enabled.

## Next Feature Priorities

### P0: Trust and correctness

- real AWS S3 sandbox read probe
- runtime evidence section in reports
- artifact scrubber
- machine-readable run verdict and exit codes

### P1: CI/CD adoption

- `nullstate run --ci`
- SARIF export through `nullstate sarif`
- GitHub Actions template
- baseline/fail-on-severity settings

### P2: Enterprise controls

- policy file for allowed targets and commands
- organization-level config
- signed run evidence
- SBOM and package provenance

### P3: Growth and brand

- portfolio case study
- demo video
- technical blog post
- comparison page against IaC scanners
- landing page with CLI demo GIF

## Case Study Angle

The strongest story is not “I built a scanner.” It is:

> I built a local-first DevSecOps CLI that turns Terraform findings into a reproducible purple-team loop: detect the issue, reason about the attack, run a constrained sandbox command, apply deterministic remediation, validate the path is blocked, and preserve evidence.

The honest caveat:

> The hackathon version has the safe command-execution boundary in place. The next enterprise iteration expands the scenario scripts from health probes into real exploit probes against sandbox resources.

That honesty improves credibility with security reviewers.

## Success Metrics

Technical:

- number of scenarios with observed runtime exploit evidence
- false-positive rate against test fixtures
- remediation success rate
- run reproducibility
- command evidence completeness

Business:

- GitHub stars and forks
- demo video completion rate
- inbound security/platform conversations
- pilot users
- paid assessment leads
- recurring use in CI

## 90-Day Roadmap

### Days 1-14

- real AWS S3 exploit probe
- runtime evidence report section
- artifact scrubber
- technical walkthrough polish
- portfolio case study publish

### Days 15-30

- Azure Blob real probe or explicit emulator limitation handling
- `--ci` mode and exit codes
- SARIF/JSON export
- GitHub Actions example

### Days 31-60

- additional AWS/Azure scenario pack
- policy file for allowed commands/targets
- signed evidence manifest
- case-study-driven landing page

### Days 61-90

- first design partner outreach
- paid assessment offer
- team dashboard prototype or evidence store
- enterprise deployment architecture
