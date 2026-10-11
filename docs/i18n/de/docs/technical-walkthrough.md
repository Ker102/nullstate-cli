<a id="technical-walkthrough"></a>
# Technischer Rundgang

Dieses Dokument erklärt, wie `nullstate` vom ersten CLI-Befehl bis zum abschließenden Berichtsartefakt arbeitet. Es richtet sich an Prüfer, die den Implementierungsablauf, die Sicherheitsgrenzen und die aktuellen Erweiterungspunkte verstehen möchten.

<a id="what-nullstate-runs"></a>
## Was Nullstate ausführt

`nullstate` ist eine lokal ausgerichtete Purple-Team-Schleife für Infrastructure as Code. Die aktuelle Implementierung konzentriert sich auf Terraform-Szenarien mit öffentlich zugänglichem Speicher:

- Deaktivierte AWS-S3-Sperre für öffentlichen Zugriff
- Öffentlicher Zugriff auf Azure-Blob-Container

Sie enthält außerdem Offline-Szenariogerüste für Kubernetes, Docker Compose, lokale digitale Zwillinge und allgemeine Planprüfungen.

Die CLI kombiniert drei Ebenen:

1. Deterministische Sicherheitslogik für Befunde, Behebung und Erfolgs- oder Fehlerprüfung.
2. Sandbox-Adapter für lokale Ausführungsziele wie LocalStack.
3. Modellgestützte Red-Team- und Blue-Team-Analyse über OpenAI-kompatible Endpunkte.

Das Modell unterstützt Analyse und Erklärung. Es ist nicht die maßgebliche Quelle dafür, ob eine Schwachstelle besteht oder die Behebung erfolgreich war.

<a id="demo-command-flow"></a>
## Ablauf der Demobefehle

Typischer Offline-Ablauf:

```powershell
nullstate
nullstate status
nullstate run examples/aws-public-s3 --offline
nullstate report
```

Typischer Live-Ablauf mit LocalStack AWS:

```powershell
nullstate sandbox up localstack-aws
nullstate sandbox status localstack-aws
nullstate run examples/aws-public-s3 --target localstack-aws
nullstate report
```

Typischer Live-Ablauf mit LocalStack Azure:

```powershell
nullstate sandbox up localstack-azure
nullstate sandbox status localstack-azure
nullstate run examples/azure-public-blob --target localstack-azure
nullstate report
```

Wenn ein selbst gehosteter Modellendpunkt verfügbar ist, verwenden Sie den benutzerdefinierten Anbieter und konfigurieren Sie einen gemeinsamen Endpunkt:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_LLM_BASE_URL = "http://127.0.0.1:8000"
```

Oder konfigurieren Sie rollenspezifische Endpunkte:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
```

Voreinstellungen für verwaltete Anbieter können Nutzern mit eigenen Schlüsseln die Endpunktkonfiguration ersparen:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
```

Die Voreinstellung `claude` ist ebenfalls über Anthropics OpenAI-SDK-Kompatibilitätsschicht verfügbar, sollte aber bis zur Verfügbarkeit eines nativen Claude-Adapters als experimentell behandelt werden.

<a id="runtime-modes"></a>
## Laufzeitmodi

<a id="offline-mode"></a>
### Offline-Modus

`--offline` überspringt die Terraform-Ausführung und Aufrufe des Cloud-Emulators. Die CLI verwendet statische IaC-Analyse und deterministisches Szenarioverhalten. Dieser Modus dient wiederholbaren Demos, Tests und der Entwicklung ohne Docker, LocalStack oder GPU.

Wichtiges Detail: `--offline` deaktiviert Modellaufrufe nicht automatisch. Sind Umgebungsvariablen für Modellendpunkte konfiguriert, verwenden Aufrufe der roten und blauen Agenten weiterhin diese Endpunkte. Verwenden Sie `--mock-agents`, wenn vollständig deterministisches Verhalten ohne Modelle beabsichtigt ist.

<a id="live-localstack-mode"></a>
### Live-Modus mit LocalStack

Der Live-Modus kopiert das Terraform-Projekt in einen Ausführungsarbeitsbereich, führt Terraform-Automatisierungsbefehle aus, verwendet LocalStack als Ziel, führt die Red/Blue-Schleife aus, wendet die Behebung im kopierten Arbeitsbereich an und validiert erneut.

Das ursprüngliche Terraform-Verzeichnis wird nicht verändert. Die Behebung erfolgt in:

```text
runs/<run-id>/workspace/
```

<a id="model-endpoint-mode"></a>
### Modellendpunkt-Modus

Der Modellendpunkt muss eine OpenAI-kompatible API bereitstellen. Dadurch funktioniert dieselbe CLI-Integration mit lokalem vLLM, SGLang, Voreinstellungen für verwaltete Anbieter oder einem benutzerdefinierten Proxy.

Die Anbieterauflösung folgt dieser Reihenfolge:

1. rollenspezifische CLI-Optionen oder Umgebungswerte
2. gemeinsame CLI-Optionen oder Umgebungswerte
3. Standard-URL der Anbietervoreinstellung
4. Rückfall auf einen deterministischen Mock-Agenten, wenn kein Endpunkt konfiguriert ist

Die Voreinstellung `google` wird zum OpenAI-kompatiblen Endpunkt von Gemini aufgelöst. Die Voreinstellung `claude` wird zu Anthropics OpenAI-SDK-Kompatibilitätsendpunkt aufgelöst. Die Modi `custom` und `openai-compatible` benötigen eine Basis-URL, sofern keine rollenspezifische URL angegeben wird.

Die CLI erfasst Modelltokenzahlen und Latenz aus den `usage`-Feldern der Antwort, sofern verfügbar. Sie versucht außerdem, `/metrics` im Prometheus-Stil vom Endpunkt abzurufen, und schreibt die unverarbeiteten Metriksnapshots in das Ausführungsverzeichnis.

<a id="end-to-end-execution-path"></a>
## Durchgängiger Ausführungsablauf

<a id="1-command-entry"></a>
### 1. Befehlseinstieg

Einstiegspunkt:

```text
src/nullstate/cli.py
```

Der Befehl `run` erhält:

- Terraform-Verzeichnis
- Zielbackend oder `auto`
- Szenario oder `auto`
- Offline-/Mock-Optionen
- Verzeichnis für Ausführungsartefakte
- Einstellungen für das rote und das blaue Modell

Wird kein Befehl angegeben, zeigt die CLI den Startbildschirm mit Produktbranding und wahrscheinlichen nächsten Befehlen an.

<a id="2-scenario-inference"></a>
### 2. Szenarioermittlung

Relevante Dateien:

```text
src/nullstate/scenario_detection.py
src/nullstate/scenarios.py
```

Bei Verwendung von `--scenario auto` untersucht die CLI das IaC-Verzeichnis und ordnet die Eingabe einem bekannten Szenario zu. Zum Beispiel:

- `examples/aws-public-s3` wird `aws-public-s3` zugeordnet
- `examples/azure-public-blob` wird `azure-public-blob` zugeordnet

Die Szenariodefinition wählt das Standard-Sandbox-Backend aus. Nutzer können dies weiterhin mit `--target` überschreiben.

<a id="3-sandbox-backend-selection"></a>
### 3. Auswahl des Sandbox-Backends

Relevante Datei:

```text
src/nullstate/sandbox.py
```

Sandbox-Backends definieren:

- Backendname
- IaC-Zieltyp
- Ausführungsmodus
- Docker-Image
- Start-/Stoppbefehle
- Laufzeitprobes

Zu den aktuellen Backends gehören:

| Backend | Zweck |
|---|---|
| `localstack-aws` | Live-Ausführung von Speicherszenarien nach AWS-Art |
| `localstack-azure` | Live-Ausführung von Speicherszenarien nach Azure-Art |
| `kind-kubernetes` | Gerüst für Kubernetes-Szenarien |
| `docker-compose` | Gerüst für digitale Zwillinge mit Docker Compose |
| `microvm-onprem` | Gerüst für lokale digitale Zwillinge |
| `plan-only` | Analysemodus ohne Laufzeit |

`nullstate sandbox up` startet das Backend. `nullstate sandbox status` prüft gegebenenfalls Docker und die HTTP-Erreichbarkeit.

<a id="4-run-workspace-creation"></a>
### 4. Erstellung des Ausführungsarbeitsbereichs

Die CLI erstellt ein neues Ausführungsverzeichnis:

```text
runs/<run-id>/
```

Sie kopiert das eingegebene Terraform-Verzeichnis nach:

```text
runs/<run-id>/workspace/
```

Dadurch bleibt das ursprüngliche Projekt unverändert. Terraform-Zustand, `.terraform`, zwischengespeicherte Pläne und Ausführungsverzeichnisse werden von der Kopie ausgeschlossen.

<a id="5-terraform-plan-loading"></a>
### 5. Laden des Terraform-Plans

Relevante Datei:

```text
src/nullstate/terraform.py
```

Im Live-Modus verwendet der Terraform-Ablauf automatisierungsfreundliche Befehle:

```text
terraform init -input=false
terraform plan -out=tfplan -input=false
terraform show -json tfplan
```

Im Offline-Modus verwendet die CLI einen statischen Terraform-Parser für die unterstützten Demo-Testdaten. Dadurch bleiben Tests und Demos auch ohne externe Laufzeitabhängigkeiten reproduzierbar.

Ergebnisse von Terraform-Befehlen werden geschrieben nach:

```text
runs/<run-id>/events.jsonl
```

<a id="6-finding-detection"></a>
### 6. Befunderkennung

Relevante Datei:

```text
src/nullstate/findings.py
```

Der deterministische Detektor erkennt unterstützte riskante Konfigurationen. Beispiele:

- Der Azure-Blob-Container hat `container_access_type = "blob"` oder `"container"`
- Das Azure-Speicherkonto erlaubt verschachtelte öffentliche Elemente
- Die AWS-S3-Kontrollen zur Sperrung des öffentlichen Zugriffs sind deaktiviert

Befunde werden als strukturiertes JSON geschrieben:

```text
runs/<run-id>/findings.json
```

Diese deterministischen Befunddaten sind die maßgebliche Quelle für den restlichen Durchlauf.

<a id="7-red-team-model-reasoning"></a>
### 7. Analyse durch das Red-Team-Modell

Relevante Datei:

```text
src/nullstate/agents.py
```

Der rote Agent erhält interne Anweisungen und Szenarionachweise. Der Nutzer gibt dem Modell während des Durchlaufs keine manuellen Prompts.

Das rote Modell liefert Angriffsanalysen, zum Beispiel:

- einen Pfad zum anonymen Lesen von S3-Objekten
- einen Pfad zum anonymen Lesen von Azure-Blob-Containern
- wahrscheinlich zu sammelnde Nachweise

Ist kein Endpunkt konfiguriert, greift die Rolle auf deterministische Mock-Ausgaben zurück.

<a id="8-constrained-attack-script-execution"></a>
### 8. Eingeschränkte Ausführung des Angriffsskripts

Relevante Dateien:

```text
src/nullstate/attack.py
src/nullstate/attack_runner.py
```

`nullstate` schreibt ein generiertes Angriffsartefakt:

```text
runs/<run-id>/attack.py
runs/<run-id>/attack-manifest.json
```

Das Manifest erfasst Szenario, Backend, Ziel-URL und Ressourcenhinweise, die Szenarioprobes nutzen können, ohne dem Modell die freie Konstruktion von Befehlen zu erlauben. Es enthält einen `$schema`-Verweis auf `docs/schemas/attack-manifest.schema.json`, und `nullstate run` validiert das Manifest vor der eingeschränkten Probe-Ausführung.

Anschließend führt der eingeschränkte Runner ausschließlich dieses generierte Skript aus. Er erzwingt folgende Grenzen:

- der Skriptname muss exakt `attack.py` sein
- das Skript muss direkt im aktuellen Ausführungsverzeichnis liegen
- die Ausführung verwendet den aktuellen Python-Interpreter
- es werden keine beliebigen Shellbefehle akzeptiert
- dynamische Eingaben sind auf `--target-url`, `--stage` und das im Ausführungsverzeichnis generierte `attack-manifest.json` beschränkt

Der Runner zeichnet Befehlsnachweise vor und nach der Behebung auf:

```json
{
  "phase": "red-tool",
  "message": "Allowlisted attack command completed",
  "data": {
    "command": ["python", "attack.py", "--target-url", "...", "--stage", "before", "--manifest", "..."],
    "target_url": "...",
    "stage": "before",
    "returncode": 0,
    "stdout": "...",
    "stderr": "",
    "started_at": "...",
    "ended_at": "...",
    "duration_seconds": 0.123
  }
}
```

Dies gibt dem Bericht echte Befehlsnachweise und vermeidet uneingeschränkten Werkzeugzugriff für den roten Agenten.

Unternehmensbezogene Schutzmaßnahmen für diese Ebene:

- Die Befehlsrichtlinie basiert auf Szenariovorlagen. Das Modell kann den Angriffspfad analysieren, aber keinen beliebigen Shellbefehl auswählen.
- `nullstate policy init` erstellt eine Richtliniendatei mit Schemaverweis und validiert sie vor dem Schreiben; `policy init --scenario <name>` erstellt eine engere Voreinstellung für ein Szenario-/Backendpaar. `run --policy-file` erzwingt vor der Ausführung erlaubte Szenarien, Backends, Phasen, Optionen des generierten `attack.py`, Zielklassifizierungen, Zielhost-Zulassungslisten, Befehlsrichtlinien-IDs sowie Obergrenzen für Zeitüberschreitungen und Ausgabegrößen.
- `nullstate policy validate` prüft eine Richtliniendatei, ohne ein Szenario auszuführen, und kann `policy-validation.json` als CI-Nachweis schreiben.
- Laufzeitziele bleiben lokale Sandbox-Endpunkte, sofern `--allow-live-cloud` nicht ausdrücklich angegeben und erfasst wird.
- `red-tool`-Ereignisse enthalten eine Version des Befehlsschemas und Reproduzierbarkeitshashes für das generierte `attack.py` und das Manifest.
- Standardausgabe und Standardfehlerausgabe der Probes sollten vor Upload, Ticketanhang oder langfristiger Nachweisaufbewahrung begrenzt werden.
- Berichte müssen beobachtete Laufzeitnachweise von deterministischer Simulation und im Emulator nicht eindeutigen Probes unterscheiden.

<a id="9-deterministic-remediation"></a>
### 9. Deterministische Behebung

Relevante Datei:

```text
src/nullstate/remediation.py
```

Das blaue Modell erklärt die Behebung, der Patch selbst wird jedoch von deterministischer Behebungslogik erzeugt.

Bei öffentlich zugänglichen Azure Blobs setzt die Behebung:

```hcl
allow_nested_items_to_be_public = false
container_access_type           = "private"
```

Bei öffentlich zugänglichem AWS S3 setzt die Behebung die Kontrollen zur Sperrung des öffentlichen Zugriffs auf `true`:

```hcl
block_public_acls       = true
block_public_policy     = true
ignore_public_acls      = true
restrict_public_buckets = true
```

Der Diff wird geschrieben nach:

```text
runs/<run-id>/remediation.patch
```

<a id="10-re-plan-and-validation"></a>
### 10. Erneute Planung und Validierung

Nach der Behebung lädt die CLI den korrigierten Arbeitsbereich erneut. Im Live-Modus führt sie Terraform-Planungs- und Anwendungsschritte im kopierten Arbeitsbereich aus. Im Offline-Modus analysiert sie die aktualisierten Dateien erneut.

Der Detektor wird erneut ausgeführt. Ist der Befund verschwunden, liefert die deterministische Angriffssimulation:

```text
Red after: blocked
```

Das eingeschränkte Angriffsskript wird ebenfalls ein zweites Mal ausgeführt mit:

```text
--stage after
```

Diese Befehlsausgabe nach der Behebung wird als weiteres `red-tool`-Ereignis protokolliert.

<a id="11-report-and-metrics"></a>
### 11. Bericht und Metriken

Relevante Dateien:

```text
src/nullstate/report.py
src/nullstate/metrics.py
```

Jeder Durchlauf schreibt:

| Artefakt | Zweck |
|---|---|
| `events.jsonl` | Vollständige Ereigniszeitleiste |
| `findings.json` | Strukturierte Schwachstellenbefunde |
| `attack.py` | Generiertes eingeschränktes Angriffsartefakt |
| `attack-manifest.json` | Schemavalidierte Angaben zu Szenario, Backend, Ziel-URL und Ressourcenhinweisen für eingeschränkte Probes |
| `remediation.patch` | Terraform-Behebungsdiff |
| `remediation.json` | Schemavalidierte Metadaten des deterministischen Behebungsregelsatzes |
| `metrics.json` | Modellaufrufe, Tokenzahlen, Latenz, Endpunktmetriken |
| `ci-summary.json` | Schemavalidiertes maschinenlesbares CI-Urteil bei Verwendung von `--ci` |
| `policy-result.json` | Eigenständige JSON-Richtlinienentscheidung für einen bestehenden Durchlauf |
| `report.md` | Für Menschen lesbare Zusammenfassung |
| `evidence-manifest.json` | SHA-256-Inventar für teilbare Ausführungsnachweise bei Verwendung von `nullstate evidence-manifest` |
| `evidence-verification.json` | Prüfergebnis für ein Manifest bei Verwendung von `nullstate evidence-verify` |
| `upload-plan.json` | Uploadplan ohne Netzwerkzugriff bei Verwendung von `nullstate upload --dry-run` |
| `workspace/` | Kopierter und korrigierter IaC-Arbeitsbereich |

`nullstate report` öffnet standardmäßig den neuesten Bericht, einschließlich Berichten in Unterverzeichnissen benannter Ausführungsverzeichnisse.

`remediation.json` enthält einen `$schema`-Verweis auf `docs/schemas/remediation-metadata.schema.json`. Die generierten Behebungsmetadaten werden validiert, bevor Berichte, Bundles und Ausführungsartefakte sie verwenden.

`nullstate bundle` schreibt `run-bundle.json`, den portablen Nachweisvertrag für lokale Dashboards, CI-Uploads, Supportbundles und die zukünftige Übernahme durch Nullstate Cloud. Das Bundle enthält einen `$schema`-Verweis auf `docs/schemas/run-bundle.schema.json`, und die CLI validiert seine Struktur vor dem Schreiben. Sofern verfügbar, enthält das Bundle auch Metadaten aus `remediation.json`, damit nachgelagerte Werkzeuge die Version des Behebungsregelsatzes und die Regel-IDs anzeigen können.

`nullstate dashboard` schreibt `dashboard.html`, ein kostenloses lokales Dashboard für einen einzelnen Durchlauf, das ohne Cloud-Anmeldung geöffnet werden kann. Es fasst Befunde, Behebungsmetadaten, Bundle-Schemametadaten, Artefaktinventar, Nachweiszeitleiste und den Berichtsauszug zusammen.

`nullstate sarif` schreibt `nullstate.sarif`, einen Export im Format SARIF 2.1.0 mit einem Ergebnis je Befund für CI- und Codescanning-Uploads.

`nullstate run --ci` schreibt `ci-summary.json` und beendet sich mit Code `2`, wenn die ursprünglichen Befunde des Durchlaufs `--fail-on-severity` erreichen oder überschreiten. Die Zusammenfassung enthält einen `$schema`-Verweis auf `docs/schemas/ci-summary.schema.json` und wird vor dem Schreiben validiert. So erhält CI eine stabile Richtlinienprüfung, ohne den Bericht für Menschen zu verändern.

`nullstate baseline` schreibt eine JSON-Baseline der Befundidentitäten. Bei Verwendung von `nullstate run --ci --baseline-file` bleiben bekannte Baseline-Befunde sichtbar, die CI-Fehlerschwelle wird jedoch nur anhand neuer Befunde bewertet.

`nullstate policy-result` schreibt dieselbe Art von Schwellen- und Baseline-Entscheidung für einen bestehenden Durchlauf, ohne das Szenario erneut auszuführen.

`nullstate evidence-manifest` schreibt `evidence-manifest.json`, ein deterministisches Integritätsinventar für teilbare Ausführungsartefakte. Das Manifest enthält einen `$schema`-Verweis auf `docs/schemas/evidence-manifest.schema.json`, und die CLI validiert seine Struktur vor dem Schreiben. Es schließt kopierte Arbeitsbereiche, Terraform-Interna, Python-Caches, die Manifestdatei selbst und Prüfausgaben aus. Verwenden Sie `--signing-key-env`, um eine HMAC-SHA256-Nachweissignatur mit gemeinsamem Schlüssel aus einem Umgebungsgeheimnis anzuhängen; dies signiert Ausführungsnachweise und ist kein Herkunftsnachweis für Pakete mit öffentlichen Schlüsseln.

`nullstate evidence-verify` schreibt `evidence-verification.json` nach erneuter Berechnung der erfassten Artefakthashes und Dateigrößen. Es prüft nur im Manifest aufgeführte Artefakte, ignoriert nicht zugehörige neue Dateien, überprüft HMAC-Signaturen bei Angabe von `--signing-key-env` und beendet sich mit Code `2`, wenn ein erfasstes Artefakt fehlt, verändert wurde, aus einem anderen Durchlauf kopiert wurde oder eine ungültige Signatur hat.

`nullstate upload --dry-run` schreibt `upload-plan.json`, aktualisiert `run-bundle.json`, erfasst den vorgesehenen Endpunkt und die Token-Umgebungsvariable und bestätigt das Vorhandensein des Tokens, ohne seinen Wert zu speichern. Der Plan enthält einen `$schema`-Verweis auf `docs/schemas/upload-plan.schema.json`, und die CLI validiert seine Struktur vor dem Schreiben. Er erfasst außerdem den Status der Bereinigungsvorprüfung: Unbereinigte Durchläufe warnen mit `upload_recommended: false`, während bereinigte Kopien mit `scrub-report.json` für den zukünftigen Übernahmepfad als uploadbereit markiert werden.

`nullstate scrub` erstellt eine bereinigte Kopie eines Durchlaufs unter `scrubbed-runs/` und schreibt `scrub-report.json`. Der ursprüngliche Durchlauf bleibt unverändert, und eine bestehende bereinigte Kopie wird nicht überschrieben.

<a id="security-boundaries"></a>
## Sicherheitsgrenzen

Die wichtigen Grenzen sind:

- Standardmäßig kein echtes Cloud-Ziel.
- Terraform-Änderungen erfolgen in einem kopierten Arbeitsbereich.
- Das rote Modell erhält keinen Shellzugriff.
- Der Angriffsrunner führt ausschließlich das im Ausführungsverzeichnis generierte `attack.py` aus.
- Geheimnisse werden aus Umgebungsvariablen oder ignorierten lokalen env-Dateien geladen.
- Ausführungsartefakte müssen vor der Veröffentlichung geprüft werden.
- `nullstate scrub` sollte vor der Veröffentlichung öffentlicher Fallstudien, CI-Uploads oder dem Teilen von Supportbundles ausgeführt werden.
- Vor der Ansprache eines nicht lokalen Cloud-Endpunkts ist `--allow-live-cloud` erforderlich.

<a id="extension-points"></a>
## Erweiterungspunkte

<a id="new-scenario"></a>
### Neues Szenario

Ergänzen oder aktualisieren Sie:

```text
src/nullstate/scenarios.py
src/nullstate/scenario_detection.py
src/nullstate/findings.py
src/nullstate/remediation.py
src/nullstate/attack.py
examples/<scenario-name>/
tests/
```

<a id="new-sandbox-backend"></a>
### Neues Sandbox-Backend

Ergänzen Sie Backendmetadaten und Befehle in:

```text
src/nullstate/sandbox.py
```

Fügen Sie anschließend Tests hinzu für:

- `sandbox list`
- `sandbox status`
- `sandbox up --dry-run`
- `sandbox down`

<a id="richer-red-tooling"></a>
### Umfangreichere Red-Team-Werkzeuge

Die nächste sichere Erweiterung ist kein freier Shellzugriff. Sie sollte aus einer szenariospezifischen Zulassungsliste bestehen:

- generierte Python-Probes
- feste Befehlsvorlagen
- ausschließlich lokale Ziel-URLs
- striktes Zeitlimit
- vollständige Ereignisprotokollierung
- keine Übernahme echter Cloud-Zugangsdaten

Siehe [Unternehmensreife](enterprise-readiness.md) für die Kontrollcheckliste, die abgeschlossen werden sollte, bevor Laufzeitprobes als Team- oder Unternehmensnachweise positioniert werden.

<a id="test-coverage"></a>
## Testabdeckung

Primäre Validierungsbefehle:

```powershell
python -m unittest discover -s tests -v
python -m ruff check src tests
python -m mypy src
```

Nützlicher Smoketest:

```powershell
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --runs-dir runs/red-tool-smoke
python -m nullstate report --runs-dir runs/red-tool-smoke
```

Der Smoketest-Durchlauf sollte zeigen:

- einen Befund vor der Behebung
- `Red before: success`
- `Red after: blocked`
- zwei `red-tool`-Ereignisse in `events.jsonl`
