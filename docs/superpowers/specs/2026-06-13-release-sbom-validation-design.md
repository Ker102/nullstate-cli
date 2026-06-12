# Release SBOM Validation Design

## Context

The release workflow now generates `dist/sbom.spdx.json` from the built wheel installed into `.sbom-venv`, then attests that SBOM with GitHub artifact attestations. The next supply-chain hardening step is to fail the release before attestation if the generated SBOM is malformed or missing expected release metadata.

## Design

Add a `Validate release SBOM` GitHub Actions step immediately after `Generate release SBOM` and before `Generate release manifest`.

The validation is standard-library Python and checks:

- `spdxVersion` is `SPDX-2.3`
- the document has a package list
- the root package `nullstate` is present
- every package has `SPDXID`, `name`, and `versionInfo`
- packaging tools `pip`, `setuptools`, and `wheel` are not included
- the document has a `DESCRIBES` relationship from `SPDXRef-DOCUMENT` to the root package

This keeps the workflow self-contained and deterministic. It does not introduce a third-party SPDX validator or package signing yet.

## Scope

This slice changes the release workflow, workflow tests, and release documentation. It does not tag a release, publish artifacts, change runtime CLI behavior, or add external validation services.

