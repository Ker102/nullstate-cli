# Security Model

## Assets

| Asset | Why it matters | Sensitivity |
|---|---|---|
| Terraform input | describes infrastructure and possible secrets | medium/high |
| Run artifacts | contain findings, logs, patches, and model evidence | medium |
| Model endpoint key | grants LLM access | high |
| LocalStack auth token | starts LocalStack Azure emulator | high |
| Terraform state | may contain sensitive infrastructure data | high |

## Trust boundaries

- Operator shell to nullstate CLI.
- nullstate CLI to sandbox backend.
- nullstate CLI to model endpoint.
- Agent instructions to allowlisted tool execution.
- Local run artifacts to public repo documentation.

## Identities

- Operator: trusted human running the CLI.
- Red agent: partially trusted attacker role constrained to local sandbox.
- Blue agent: partially trusted remediation role.
- External model server: trusted only for configured endpoint behavior.
- CI runner: ephemeral automation identity with minimal permissions.

## Network controls

V1 defaults to offline mode or LocalStack-style local endpoints. Real cloud execution is out of scope by default.

## Secret handling

- Secrets are read from environment variables.
- `.env` and Terraform state are ignored.
- `.env.example` documents required names without values.

## Container security

LocalStack and other sandboxes are runtime dependencies, not vendored binaries. Operators should pull trusted images and avoid running arbitrary red-team code outside generated run workspaces.

## Red-team command execution

The V1 red command runner is constrained by design:

- It only runs the generated `attack.py` file.
- `attack.py` must live directly inside the run directory.
- The command is launched with the current Python interpreter, not an arbitrary shell.
- The only dynamic inputs are `--target-url` and `--stage`.
- The event log records command, stdout, stderr, return code, target URL, start time, end time, and duration.

This allows demos to show real command execution against local sandbox endpoints without giving the model unrestricted tool access.

## CI/CD security

- PR checks run tests, lint, type checks, and dependency audit.
- CodeQL runs on PRs, pushes, and weekly schedule.
- Dependency review runs on PRs.
- Release workflow triggers only from semver tags.
- Workflows use least-privilege permissions.

## Data protection

Artifacts must be reviewed before publishing. Do not publish tokens, real tenant IDs, real subscription IDs, private IP maps, or cloud state.

## Known risks

- Some sandbox adapters are scaffolds, not full execution backends.
- LocalStack Azure requires external setup and auth token.
- Offline metrics report zero token usage because no model is called.
- The generated attack scripts are intentionally narrow probes; richer exploit scripts should remain allowlisted and sandbox-scoped.

## Future improvements

- SBOM generation.
- Package provenance signing.
- Artifact scrubbing command.
- Policy-as-code guardrails for agent tools.
