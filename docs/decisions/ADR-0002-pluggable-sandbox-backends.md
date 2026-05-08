# ADR-0002: Pluggable sandbox backends

## Status

Accepted.

## Context

nullstate needs to support cloud IaC, Kubernetes manifests, Docker Compose stacks, and on-prem-style configurations over time.

## Decision

Use a sandbox adapter registry with three execution modes:

- executable sandbox
- digital twin sandbox
- plan-only analysis

## Consequences

- V1 can ship with one strong executable target while exposing future backend availability.
- On-prem environments can be modeled without pretending every provider has a perfect emulator.
- Some backends start as documented scaffolds rather than full exploit execution.
