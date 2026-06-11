# CI/CD

## Branching model

- `main` is protected.
- Feature work uses branches such as `feat/sandbox-localstack`.
- PRs are required for all changes.
- Releases are tagged as `vMAJOR.MINOR.PATCH`.

## Pull request checks

The PR workflow runs:

- unit tests
- Ruff lint
- mypy type check
- pip-audit dependency audit

## Nullstate CI export

Use offline mode for deterministic pull request evidence when no sandbox is available:

```powershell
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --runs-dir runs/ci
python -m nullstate sarif --runs-dir runs/ci --output artifacts/nullstate.sarif
python -m nullstate bundle --runs-dir runs/ci
```

`nullstate sarif` reads the latest run by default, or a specific run ID when provided. It writes SARIF 2.1.0 with one result per finding and preserves severity, evidence, remediation guidance, and the IaC resource address as a logical location. Upload `artifacts/nullstate.sarif` to GitHub code scanning or another SARIF-aware security tool.

The repository includes `.github/workflows/nullstate-sarif.yml` as the first GitHub Actions example. It runs an offline AWS S3 scenario, exports SARIF, uploads it with `github/codeql-action/upload-sarif`, and stores the run artifacts for review.

Run `nullstate scrub` before attaching bundles or reports to public issues, support tickets, or case-study artifacts.

## Security checks

- CodeQL scans Python code on PRs, main pushes, and weekly schedule.
- Dependency Review checks dependency changes in pull requests.
- Dependabot monitors Python and GitHub Actions dependencies.

## Release flow

```text
merge to main
-> update CHANGELOG.md
-> tag v0.1.0
-> release workflow builds package
-> GitHub release created with generated notes
```

## Required repository settings

Configure in GitHub after publishing:

- protect `main`
- require pull request review
- require PR Checks and CodeQL
- block force pushes
- require signed commits if possible
- enable secret scanning and push protection
