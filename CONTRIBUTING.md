# Contributing

## Workflow

Use GitHub flow:

1. Create an issue or link to an existing one.
2. Create a branch: `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>`, or `chore/<short-name>`.
3. Open a structured pull request.
4. Wait for CI and review.
5. Squash merge to `main`.

No direct pushes to `main`.

## Local Checks

```powershell
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m ruff check src tests
python -m mypy src
python -m pip_audit
```

## Commit Style

Use conventional commit prefixes:

- `feat:`
- `fix:`
- `docs:`
- `test:`
- `chore:`

## Pull Request Expectations

Each PR should include:

- summary
- test evidence
- security impact
- documentation updates
- screenshots or run artifacts when relevant
