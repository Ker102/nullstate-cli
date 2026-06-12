# Keyless Release Signing Design

## Context

The release workflow already builds wheel/sdist artifacts, generates a checksum manifest, validates and attests `sbom.spdx.json`, and creates GitHub artifact attestations. The remaining release hardening item is package signing. Long-lived signing keys would add secret-management burden and are easy to mishandle in a personal case-study project.

## Design

Use Sigstore keyless signing through GitHub Actions OIDC:

- keep `id-token: write` permission
- use `sigstore/gh-action-sigstore-python`
- sign the wheel, sdist, SBOM, and release manifest after the manifest and attestations exist
- publish generated `.sigstore.json` bundles because the final `gh release create ... dist/*` uploads everything in `dist/`
- validate locally in the workflow that every primary release artifact has a matching `.sigstore.json` bundle before release creation

This gives package-level signing without a stored private key. GitHub artifact attestations remain build provenance and SBOM predicate evidence; Sigstore bundles provide artifact signatures.

## Scope

This slice does not publish to PyPI, create a release, tag a version, or introduce project runtime dependencies. It only updates the release workflow, workflow text tests, and release documentation.

