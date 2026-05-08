# Case Study Outline

## Problem

Cloud teams ship Terraform faster than security teams can continuously validate exploitability. Static IaC scanners show possible risk, but they do not prove whether an attacker can use the misconfiguration or whether a remediation actually blocks the path.

## Solution

`nullstate` runs a local purple-team loop against Terraform Azure:

- Analyze planned infrastructure.
- Attempt a red-team exploit.
- Generate a blue-team remediation.
- Revalidate after patching.
- Produce an evidence report.

## Demo Scenario

An Azure Blob container is configured with anonymous container access. `nullstate` detects the exposure, simulates an anonymous read, patches the Terraform to private access, and verifies that the exploit is blocked.

## Why AMD MI300X

The architecture is built for long-context security evidence: Terraform plan JSON, emulator logs, exploit output, and remediation diffs can be sent to a local model endpoint without external API latency or data exposure.

## Next Steps

- Add more Azure rules: storage shared keys, public network access, Key Vault public access.
- Add real LocalStack Azure exploit execution.
- Add AWS and Kubernetes adapters behind the same run artifact model.
