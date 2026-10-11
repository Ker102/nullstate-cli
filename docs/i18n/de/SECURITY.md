<a id="security-policy"></a>
# Sicherheitsrichtlinie

<a id="supported-versions"></a>
## Unterstützte Versionen

`nullstate` ist vor 1.0. Sicherheitskorrekturen zielen auf den neuesten `main`-Stand und den neuesten Vorabtag, wenn Evaluatoren eine Veröffentlichung benötigen.

| Version | Unterstützung |
|---|---|
| `main` | ja |
| neueste Vorabversion | ja |
| ältere Vorabversionen | nach Möglichkeit |

<a id="reporting-a-vulnerability"></a>
## Schwachstellen melden

Keine öffentlichen Issues für ausnutzbare Schwachstellen in nullstate selbst öffnen. Maintainer privat kontaktieren oder aktivierte private GitHub-Meldung verwenden. Details erst nach verfügbarer Korrektur oder Risikominderung veröffentlichen.

<a id="security-boundaries"></a>
## Sicherheitsgrenzen

nullstate testet absichtlich verwundbare lokale Sandboxes. Nicht auf Produktion richten, außer der Betreiber besitzt die Umgebung und versteht das Risiko.

V1-Standards:

- standardmäßig keine echte Azure-Ausführung
- LocalStack-/Docker-Sandboxes nur bei explizitem Start
- Artefakte sind lokale Dateien
- Geheimnisse über Umgebungsvariablen, nicht committete Dateien
- eingeschränkte Red-Proben führen nur generiertes `attack.py` im Ausführungsverzeichnis aus
- nicht lokale HTTP-Ziele benötigen explizite Betreiberzustimmung und Richtlinienkontrollen

<a id="secret-handling"></a>
## Umgang mit Geheimnissen

Niemals committen:

- `LOCALSTACK_AUTH_TOKEN`
- Modell-API-Keys
- Cloud-Zugangsdaten
- Terraform-State
- `.env`
- echte `.tfvars`

Konfiguration mit `.env.example` dokumentieren.

Vor Anhängen an Issues, Tickets, Fallstudien oder Supportanfragen:

```powershell
nullstate scrub
```

Die bereinigte Kopie aus `scrubbed-runs/` anhängen, nicht das rohe `runs/`.
