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
