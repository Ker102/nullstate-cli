# ADR-0003: LocalStack Azure for V1

## Status

Accepted.

## Context

The first demo target is Terraform Azure. Real Azure would increase credential, cost, cleanup, and safety risks.

## Decision

Use LocalStack Azure as the first executable sandbox backend, with plan-only mode as a fallback.

## Consequences

- The demo can run without real Azure resources.
- The operator still needs Docker and `LOCALSTACK_AUTH_TOKEN` for live LocalStack Azure.
- The repo must clearly distinguish LocalStack integration from vendoring LocalStack.
