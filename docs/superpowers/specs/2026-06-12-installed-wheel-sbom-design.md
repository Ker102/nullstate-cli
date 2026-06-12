# Installed Wheel SBOM Design

## Context

The release workflow currently writes `dist/sbom.spdx.json` from `[project].dependencies` in `pyproject.toml`. That records the intended runtime dependencies, but it does not include resolved installed versions or transitive runtime packages.

## Design

Generate the release SBOM from a clean virtual environment after building the wheel:

1. Create `.sbom-venv` in the GitHub Actions runner.
2. Install the built wheel with `.sbom-venv/bin/python -m pip install dist/*.whl`.
3. Run the SBOM generator inside that virtual environment.
4. Use `importlib.metadata.distributions()` to inventory installed runtime distributions.
5. Exclude packaging tools: `pip`, `setuptools`, and `wheel`.
6. Include `versionInfo` for each installed package.
7. Build SPDX `DEPENDS_ON` relationships from installed package metadata where the required package is also installed.

This remains a lightweight SPDX 2.3 SBOM. It does not add a checked-in lockfile or a third-party SBOM generator yet.

## Scope

This slice changes only the release workflow, workflow tests, and documentation. It does not publish releases, tag versions, install new project dependencies, or change runtime CLI behavior.

## Testing

Extend workflow text tests to assert that the release workflow:

- creates `.sbom-venv`
- installs `dist/*.whl`
- uses `importlib.metadata`
- excludes `pip`, `setuptools`, and `wheel`
- writes package `versionInfo`

