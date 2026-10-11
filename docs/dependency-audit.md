# Dependency Audit

This project treats dependency audit results as release evidence, not as a one-time checkbox.

## Current Result

Last local audit:

```text
Date: 2026-07-02
Command: python -m pip_audit . --skip-editable
Tool: pip-audit 2.10.0
Result: No known vulnerabilities found
```

The PR workflow also runs the same audit command after installing the project with development dependencies.

## Policy

- New direct dependencies should be justified in the pull request.
- Dependency audit failures block release readiness unless the issue is documented here with scope, affected package, exploitability, mitigation, and planned removal date.
- Editable project metadata is skipped with `--skip-editable` so the audit focuses on installed third-party packages.
- Release candidates should rerun:

```powershell
python -m pip install -e ".[dev]"
python -m pip_audit . --skip-editable
```

## Accepted Risk

No accepted vulnerable dependency risk is currently documented.
