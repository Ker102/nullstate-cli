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

    finding_count = len(findings) if isinstance(findings, list) else 0
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
    body {{ font-family: Inter, Segoe UI, Arial, sans-serif; margin: 0; background: #08111f; color: #e6edf7; }}
    header {{ padding: 32px; background: linear-gradient(135deg, #0f2a44, #111827); border-bottom: 1px solid #203047; }}
    main {{ padding: 24px 32px 48px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }}
    .card {{ background: #0f172a; border: 1px solid #233047; border-radius: 14px; padding: 18px; box-shadow: 0 10px 30px rgba(0,0,0,.25); }}
    .metric {{ font-size: 32px; font-weight: 700; margin: 6px 0; }}
    .label {{ color: #9fb3c8; font-size: 13px; text-transform: uppercase; letter-spacing: .08em; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #030712; padding: 14px; border-radius: 10px; border: 1px solid #1f2937; }}
    table {{ width: 100%; border-collapse: collapse; }}
    td, th {{ border-bottom: 1px solid #26364d; padding: 10px; text-align: left; vertical-align: top; }}
    a {{ color: #60a5fa; }}
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
    </section>
    <section class="card" style="margin-top: 20px;">
      <h2>Findings</h2>
      {_render_findings(findings)}
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
