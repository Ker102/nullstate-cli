from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .bundle import BUNDLE_FILENAME, write_run_bundle


DASHBOARD_FILENAME = "dashboard.html"


def write_run_dashboard(run_dir: Path) -> Path:
    run_dir = run_dir.resolve()
    bundle_path = run_dir / BUNDLE_FILENAME
    if bundle_path.is_file():
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    else:
        bundle = write_run_bundle(run_dir)

    dashboard_path = run_dir / DASHBOARD_FILENAME
    dashboard_path.write_text(render_dashboard(bundle), encoding="utf-8")
    return dashboard_path


def render_dashboard(bundle: dict[str, Any]) -> str:
    run = bundle.get("run") or {}
    evidence = bundle.get("evidence") or {}
    findings = evidence.get("findings") if isinstance(evidence, dict) else []
    events = evidence.get("events") if isinstance(evidence, dict) else []
    metrics = evidence.get("metrics") if isinstance(evidence, dict) else {}
    remediation = evidence.get("remediation") if isinstance(evidence, dict) else {}
    artifacts = bundle.get("artifacts")

    finding_count = len(findings) if isinstance(findings, list) else 0
    artifact_count = len(artifacts) if isinstance(artifacts, list) else 0
    event_list = events if isinstance(events, list) else []
    red_tool_count = len([event for event in event_list if isinstance(event, dict) and event.get("phase") == "red-tool"])
    model_calls: list[Any] = []
    if isinstance(metrics, dict):
        raw_model_calls = metrics.get("model_calls") or []
        if isinstance(raw_model_calls, list):
            model_calls = raw_model_calls

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>nullstate run dashboard</title>
  <style>
    body {{ font-family: Inter, Segoe UI, Arial, sans-serif; margin: 0; background: #10131a; color: #eef3f8; }}
    header {{ padding: 32px; background: #132238; border-bottom: 3px solid #2f9e8f; }}
    main {{ padding: 24px 32px 48px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }}
    .card {{ background: #171b24; border: 1px solid #364052; border-radius: 8px; padding: 18px; box-shadow: 0 10px 30px rgba(0,0,0,.22); }}
    .metric {{ font-size: 32px; font-weight: 700; margin: 6px 0; }}
    .label {{ color: #b5c4ce; font-size: 13px; text-transform: uppercase; letter-spacing: 0; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #0b0e13; padding: 14px; border-radius: 8px; border: 1px solid #303846; }}
    table {{ width: 100%; border-collapse: collapse; }}
    td, th {{ border-bottom: 1px solid #384455; padding: 10px; text-align: left; vertical-align: top; }}
    code {{ color: #8ee6d6; }}
    a {{ color: #8ec5ff; }}
  </style>
</head>
<body>
  <header>
    <div class="label">nullstate local dashboard</div>
    <h1>Run {html.escape(str(run.get("id") or "unknown"))}</h1>
    <p>Scenario: <strong>{html.escape(str(run.get("scenario") or "unknown"))}</strong> · Target: <strong>{html.escape(str(run.get("target") or "unknown"))}</strong></p>
  </header>
  <main>
    <section class="grid">
      <div class="card"><div class="label">Verdict</div><div class="metric">{html.escape(str(run.get("verdict") or "unknown"))}</div></div>
      <div class="card"><div class="label">Findings</div><div class="metric">{finding_count}</div></div>
      <div class="card"><div class="label">Red tool events</div><div class="metric">{red_tool_count}</div></div>
      <div class="card"><div class="label">Model calls</div><div class="metric">{len(model_calls)}</div></div>
      <div class="card"><div class="label">Artifacts</div><div class="metric">{artifact_count}</div></div>
    </section>
    <section class="card" style="margin-top: 20px;">
      <h2>Findings</h2>
      {_render_findings(findings)}
    </section>
    <section class="card" style="margin-top: 20px;">
      <h2>Remediation</h2>
      {_render_remediation(remediation)}
    </section>
    <section class="card" style="margin-top: 20px;">
      <h2>Bundle contract</h2>
      {_render_bundle_contract(bundle)}
    </section>
    <section class="card" style="margin-top: 20px;">
      <h2>Artifacts</h2>
      {_render_artifacts(artifacts)}
    </section>
    <section class="card" style="margin-top: 20px;">
      <h2>Evidence timeline</h2>
      {_render_events(events)}
    </section>
    <section class="card" style="margin-top: 20px;">
      <h2>Report excerpt</h2>
      <pre>{html.escape(str((evidence or {}).get("report_excerpt") or ""))}</pre>
    </section>
    <section class="card" style="margin-top: 20px;">
      <h2>Next paid-platform path</h2>
      <p>This local dashboard is single-user and offline. Team dashboards, cloud upload, managed model calls, support, scheduled scans, alerts, RBAC, and compliance exports belong in Nullstate Cloud or the self-hosted Enterprise app.</p>
    </section>
  </main>
</body>
</html>
"""


def _render_findings(findings: Any) -> str:
    if not isinstance(findings, list) or not findings:
        return "<p>No findings.</p>"
    rows = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(finding.get('severity', 'unknown')).upper())}</td>"
            f"<td>{html.escape(str(finding.get('rule_id', 'unknown')))}</td>"
            f"<td>{html.escape(str(finding.get('resource_address', 'unknown')))}</td>"
            f"<td>{html.escape(str(finding.get('summary', '')))}</td>"
            "</tr>"
        )
    return "<table><thead><tr><th>Severity</th><th>Rule</th><th>Resource</th><th>Summary</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


def _render_remediation(remediation: Any) -> str:
    if not isinstance(remediation, dict) or not remediation:
        return "<p>No remediation metadata.</p>"
    rules = remediation.get("rules_applied")
    rule_rows = []
    if isinstance(rules, list):
        for rule in rules:
            rule_rows.append(f"<tr><td>{html.escape(str(rule))}</td></tr>")
    rules_table = "<p>No rules recorded.</p>"
    if rule_rows:
        rules_table = "<table><thead><tr><th>Rule ID</th></tr></thead><tbody>" + "".join(rule_rows) + "</tbody></table>"
    changed_files = remediation.get("changed_files")
    changed_count = len(changed_files) if isinstance(changed_files, list) else 0
    return (
        "<p>"
        f"Ruleset: <code>{html.escape(str(remediation.get('ruleset_version', 'unknown')))}</code> "
        f"Scenario: <code>{html.escape(str(remediation.get('scenario', 'unknown')))}</code> "
        f"Changed files: <strong>{changed_count}</strong>"
        "</p>"
        + rules_table
    )


def _render_bundle_contract(bundle: dict[str, Any]) -> str:
    return (
        "<table><tbody>"
        f"<tr><th>Schema</th><td><code>{html.escape(str(bundle.get('$schema', 'unknown')))}</code></td></tr>"
        f"<tr><th>Version</th><td><code>{html.escape(str(bundle.get('schema_version', 'unknown')))}</code></td></tr>"
        f"<tr><th>Generated</th><td>{html.escape(str(bundle.get('generated_at', 'unknown')))}</td></tr>"
        "</tbody></table>"
    )


def _render_artifacts(artifacts: Any) -> str:
    if not isinstance(artifacts, list) or not artifacts:
        return "<p>No artifacts.</p>"
    rows = []
    for artifact in artifacts[:100]:
        if not isinstance(artifact, dict):
            continue
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(artifact.get('path', 'unknown')))}</td>"
            f"<td>{html.escape(str(artifact.get('size_bytes', 'unknown')))}</td>"
            f"<td><code>{html.escape(str(artifact.get('sha256', 'unknown'))[:16])}</code></td>"
            "</tr>"
        )
    return "<table><thead><tr><th>Path</th><th>Bytes</th><th>SHA-256 prefix</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


def _render_events(events: Any) -> str:
    if not isinstance(events, list) or not events:
        return "<p>No events.</p>"
    rows = []
    for event in events[:100]:
        if not isinstance(event, dict):
            continue
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(event.get('timestamp', '')))}</td>"
            f"<td>{html.escape(str(event.get('phase', '')))}</td>"
            f"<td>{html.escape(str(event.get('message', '')))}</td>"
            "</tr>"
        )
    return "<table><thead><tr><th>Time</th><th>Phase</th><th>Message</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
