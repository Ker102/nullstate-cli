# Open-Source Readiness Milestones

This document tracks the practical milestones required before `nullstate` should be promoted from an alpha project to a stable open-source CLI.

GitHub tracking:

- Milestone 1: <https://github.com/Ker102/nullstate-cli/milestone/1>
- Milestone 2: <https://github.com/Ker102/nullstate-cli/milestone/3>
- Milestone 3: <https://github.com/Ker102/nullstate-cli/milestone/2>

## Current Status

`nullstate` is ready for open-source alpha users who understand that several backends are still experimental. The AWS LocalStack path has live runtime validation and constrained command evidence. The Azure Blob path has deterministic IaC validation, remediation, manifest-backed probe generation, and offline coverage, but live LocalStack Azure execution is blocked until the LocalStack workspace/user has Azure Emulator access.

## Milestone 1: Alpha publication readiness

Goal: make the repository usable and understandable for early open-source evaluators.

Status: mostly complete.

Acceptance criteria:

- [x] Clear README install path from source and current prerelease tag.
- [x] `nullstate` console entrypoint documented with `python -m nullstate` fallback.
- [x] License, contributing guide, code of conduct, and security policy present.
- [x] GitHub issue templates collect safe run context without asking users to paste secrets.
- [x] Offline quickstart works without LocalStack, Terraform cloud credentials, or model infrastructure.
- [x] Red-team command execution boundaries are documented honestly.
- [x] Reports distinguish observed runtime evidence, deterministic simulation, and inconclusive runtime probes.
- [x] Attach or publish a sanitized sample run artifact for a first-time user to inspect without running Docker. Tracked in issue #29.

## Milestone 2: Stable local sandbox validation

Goal: give users a reliable local proof path for supported scenarios.

Status: AWS ready; Azure blocked by external entitlement.

Acceptance criteria:

- [x] LocalStack AWS S3 scenario deploys vulnerable resources locally.
- [x] Generated AWS `attack.py` performs an anonymous object-read probe before and after remediation.
- [x] AWS report includes real command evidence showing exploit observed before remediation and blocked after remediation.
- [x] `sandbox up` fails closed when a container exits after startup instead of printing false success.
- [x] LocalStack Azure entitlement failure is documented with a clear operator hint.
- [ ] Resolve LocalStack Azure entitlement, or replace LocalStack Azure with a supported Azure storage emulator path.
- [ ] Run the Azure Blob scenario live and prove anonymous blob read before remediation and blocked read after remediation.
- [ ] If LocalStack Azure remains unavailable, implement an Azurite fallback for the `azure-public-blob` storage-only scenario. Tracked in issue #30.

## Milestone 3: Open-source stable CLI

Goal: publish a stable CLI that external users can install, run, and trust for the documented scope.

Status: not complete.

Acceptance criteria:

- [ ] Publish release artifacts that install without cloning the repo.
- [ ] Publish a release page with wheel, sdist, SBOM, release manifest, attestations, and signature verification instructions.
- [x] Add a short "first 10 minutes" walkthrough tested from a clean checkout.
- [x] Include at least one sanitized demo run bundle and dashboard artifact.
- [ ] Keep every non-live scenario clearly labeled as offline/scaffolded.
- [ ] Run dependency audit and document any accepted risk.
- [ ] Confirm GitHub Actions release dry-run passes before tagging the next release.
- [ ] Confirm `pip install` from the latest tag exposes the `nullstate` console command on Windows and Linux.

## Azure Emulator Decision

The current LocalStack Azure startup failure means the provided auth token is valid enough to activate a cached/trial license, but the LocalStack workspace/user is not entitled to run the Azure Emulator image. This is different from Azure cloud permissions; it is a LocalStack product entitlement/license issue.

Options:

1. Ask LocalStack support to enable Azure Emulator access for the workspace/user associated with `LOCALSTACK_AUTH_TOKEN`.
2. Use Azurite fallback for the V1 Azure Blob storage scenario. This would cover blob/container public-read behavior but not the broader Azure Resource Manager control plane.
3. Build a small internal storage emulator adapter for the demo scenario only. This is lowest dependency risk but highest maintenance burden and should be clearly labeled as a scenario simulator, not Azure.
4. Keep Azure as offline deterministic validation until a live emulator is available, and focus open-source live validation on AWS first.

Recommended path:

Use LocalStack Azure if entitlement can be enabled quickly. Otherwise, implement an Azurite fallback for the storage-only Azure Blob scenario and keep Azure Resource Manager emulation as future work.
