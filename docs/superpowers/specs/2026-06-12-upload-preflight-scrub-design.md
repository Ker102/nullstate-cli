# Upload Preflight Scrub Design

## Context

`nullstate upload --dry-run` currently writes `upload-plan.json` and refreshes `run-bundle.json` without sending network traffic. The plan records endpoint intent, bundle checksum, artifact count, and token presence. It does not yet tell operators whether the selected run is a raw run or a scrubbed copy.

## Design

Add a small upload preflight section to `upload-plan.json`:

```json
{
  "preflight": {
    "scrub": {
      "status": "not_performed",
      "scrub_report_present": false,
      "upload_recommended": false,
      "warnings": ["Run has not been scrubbed. Run nullstate scrub before sharing or future cloud upload."]
    }
  }
}
```

Detection is intentionally local and deterministic. A run is considered scrubbed when `scrub-report.json` exists directly inside the selected run directory. Raw runs keep working in dry-run mode, but the plan and CLI output should warn that upload is not recommended until a scrubbed copy is used.

For scrubbed copies, the plan records `status: "scrubbed"`, `scrub_report_present: true`, `upload_recommended: true`, the relative `scrub_report_path`, and no warning.

## Scope

This slice does not implement live upload, network requests, ingestion APIs, authentication flows, or stronger scrub-report validation. It only adds local upload readiness metadata and documentation.

## Testing

Add unit coverage for:

- raw run upload plans warn and mark upload as not recommended
- scrubbed run upload plans detect `scrub-report.json` and mark upload as recommended
- token values remain excluded

