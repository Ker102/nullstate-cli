<a id="dependency-audit"></a>
# Abhängigkeitsaudit

Audits sind Release-Evidenz, keine einmalige Checkbox.

<a id="current-result"></a>
## Aktuelles Ergebnis

Letztes lokales Audit:

```text
Date: 2026-07-02
Command: python -m pip_audit . --skip-editable
Tool: pip-audit 2.10.0
Result: No known vulnerabilities found
```

PR-Workflow nutzt denselben Befehl nach Dev-Installation.

<a id="policy"></a>
## Richtlinie

- Neue direkte Dependencies im PR begründen.
- Auditfehler blockieren Releases außer bei dokumentiertem Umfang, Paket, Ausnutzbarkeit, Mitigation und Entferndatum.
- `--skip-editable` überspringt editable Metadaten für installierte Drittanbieterpakete.
- Kandidaten erneut prüfen:

```powershell
python -m pip install -e ".[dev]"
python -m pip_audit . --skip-editable
```

<a id="accepted-risk"></a>
## Akzeptiertes Risiko

Kein akzeptiertes verwundbares Dependency-Risiko dokumentiert.
