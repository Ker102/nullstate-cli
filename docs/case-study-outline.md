# Case Study Outline

## Problem

Cloud teams ship Terraform faster than security teams can continuously validate exploitability. Static IaC scanners show possible risk, but they do not prove whether an attacker can use the misconfiguration or whether a remediation actually blocks the path.

## Solution

`nullstate` runs a local purple-team loop against Terraform IaC:

- Analyze planned infrastructure.
- Attempt a red-team exploit.
- Generate a blue-team remediation.
- Revalidate after patching.
- Produce an evidence report.

## Demo Scenario

The live-validated path uses a public AWS S3 fixture in LocalStack: `nullstate` detects the exposure, runs a constrained anonymous read probe, patches the Terraform, and verifies that the attack path is blocked. The Azure Blob fixture follows the same deterministic detection and remediation pattern, but live LocalStack Azure validation is pending Azure Emulator entitlement or a storage-only fallback such as Azurite.

## Why AMD MI300X

The architecture is built for long-context security evidence: Terraform plan JSON, emulator logs, exploit output, and remediation diffs can be sent to a local model endpoint without external API latency or data exposure.

## Next Steps

- Add more Azure rules: storage shared keys, public network access, Key Vault public access.
- Resolve LocalStack Azure entitlement or add an Azurite fallback for the Azure Blob scenario.
- Add Kubernetes, Docker Compose, and on-prem live adapters behind the same run artifact model.
- Add AMD GPU-hosted model evidence with vLLM `/metrics` and `amd-smi` or `rocm-smi` snapshots.
