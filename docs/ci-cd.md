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
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --ci --fail-on-severity none --runs-dir runs/ci
python -m nullstate policy-result --runs-dir runs/ci --fail-on-severity high
python -m nullstate sarif --runs-dir runs/ci --output artifacts/nullstate.sarif
python -m nullstate bundle --runs-dir runs/ci
python -m nullstate upload --runs-dir runs/ci --dry-run
```

`--ci` writes `ci-summary.json` into the run directory and exits with code `2` when the original findings meet or exceed `--fail-on-severity`. Supported thresholds are `none`, `low`, `medium`, `high`, and `critical`.

`nullstate policy-result` writes `policy-result.json` from an existing run. Use it when a pipeline needs a standalone JSON decision artifact without re-running the scenario.

Use `--fail-on-severity none` for demonstration or pure upload workflows. Use `--fail-on-severity high` or `--fail-on-severity critical` for enforcing PR gates; if the job must both fail and upload SARIF, run the upload step with explicit `continue-on-error` handling or split export and enforcement into separate steps.

For repositories with existing accepted findings, create a baseline from a reviewed run:

```powershell
python -m nullstate baseline --runs-dir runs/ci --output nullstate-baseline.json
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --ci --baseline-file nullstate-baseline.json --runs-dir runs/ci-next
python -m nullstate policy-result --runs-dir runs/ci-next --baseline-file nullstate-baseline.json
```

When `--baseline-file` is set, `ci-summary.json` records known and new finding counts. The severity threshold is evaluated against new findings only.

`nullstate sarif` reads the latest run by default, or a specific run ID when provided. It writes SARIF 2.1.0 with one result per finding and preserves severity, evidence, remediation guidance, and the IaC resource address as a logical location. Upload `artifacts/nullstate.sarif` to GitHub code scanning or another SARIF-aware security tool.

The repository includes `.github/workflows/nullstate-sarif.yml` as the first GitHub Actions example. It runs an offline AWS S3 scenario with `--ci --fail-on-severity none` so the intentionally vulnerable demo can still upload SARIF, uploads it with `github/codeql-action/upload-sarif`, and stores the run artifacts for review. Change the threshold to `high` or `critical` when using the workflow as an enforcing PR gate against real project IaC.

Run `nullstate scrub` before attaching bundles or reports to public issues, support tickets, or case-study artifacts.

`nullstate upload --dry-run` writes `upload-plan.json` beside the run bundle. It prepares the future Nullstate Cloud ingestion request shape without sending network traffic or storing token values.

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
