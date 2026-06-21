# Contributing

## Workflow

Use GitHub flow:

1. Create an issue or link to an existing one.
2. Create a branch: `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>`, or `chore/<short-name>`.
3. Open a structured pull request.
4. Wait for CI and review.
5. Squash merge to `main`.

No direct pushes to `main`.

## Local Setup

```powershell
git clone https://github.com/Ker102/nullstate-cli.git
cd nullstate-cli
python -m pip install -e ".[dev]"
nullstate doctor --offline
```

If the `nullstate` console command is not on `PATH`, use:

```powershell
python -m nullstate doctor --offline
```

## Local Checks

```powershell
python -m pip install -e ".[dev]"
python -m ruff check src tests
python -m mypy src
python -m unittest discover -s tests -v
python -m pip_audit
```

Use `pip_audit` as a security signal, not as a substitute for review. If it reports a dependency issue, document whether the vulnerable path is reachable in `nullstate`.

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

## Security Expectations

- Do not include real cloud credentials, LocalStack auth tokens, model API keys, `.env` files, Terraform state, or unsanitized run bundles.
- Use `nullstate scrub` before sharing run artifacts publicly.
- Keep attack execution local by default. Any future real-cloud target work must be explicit, opt-in, policy-controlled, and documented.
- If a change touches the red runner, policy enforcement, artifact scrubbing, upload planning, release workflow, or CI gates, include focused tests.
