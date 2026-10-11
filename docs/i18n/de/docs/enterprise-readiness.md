<a id="enterprise-readiness"></a>
# Enterprise-Bereitschaft

Kontrollen vom lokalen Hackathonprototyp `nullstate` zum Enterprise-DevSecOps-Tool; vorhandene Durchsetzung getrennt von Anforderungen vor Team-, Cloud- oder Self-hosted-Nutzung.

<a id="current-controls"></a>
## Aktuelle Kontrollen

| Kontrolle | Status | Evidenz |
|---|---|---|
| Deterministische Befunde | implementiert | `src/nullstate/findings.py` |
| Deterministische Abhilfe | implementiert | `src/nullstate/remediation.py` |
| Kopierter Workspace | implementiert | Original-IaC unverändert |
| Eingeschränkter Runner | implementiert | nur Run-`attack.py` |
| Manifestgebundene Eingaben | implementiert | `attack-manifest.json` validiert Szenario, Backend, URL, Ressourcendaten |
| Laufzeitlogs | implementiert | `red-tool` Ausgabe/Zeit |
| Lokalzwang | implementiert | externe HTTP-Ziele standardmäßig abgelehnt |
| Angriffshashes | implementiert | `red-tool` Script-/Manifest-SHA-256 |
| Trunkierung | implementiert | `red-tool` markiert stdout/stderr |
| Nicht destruktive Bereinigung | implementiert | `nullstate scrub` kopiert/schwärzt |
| Upload-Preflight | implementiert | `nullstate upload --dry-run` Status/Warnung |
| Uploadvertrag | implementiert | `docs/schemas/upload-plan.schema.json`, CLI-Validierung |
| Evidenzklassifikation | implementiert | Laufzeit, unklar, offline |
| Dashboard/Bundle | implementiert | `nullstate dashboard`, `nullstate bundle`, `docs/schemas/run-bundle.schema.json` |
| Red-Policy-Gerüst | implementiert | `nullstate policy init`, Presets, `run --policy-file` erzwingen validierte Szenarien, Backends, Phasen, Argumente, Klassen/Hosts, Befehle, Timeout, Ausgabe |
| Policyvalidierung | implementiert | `nullstate policy validate`, optional `policy-validation.json` |
| Integritätsmanifest | implementiert | `nullstate evidence-manifest` SHA-256, optional HMAC |
| Verifikation | implementiert | `nullstate evidence-verify` erkennt fehlend/geändert/kopiert/ungültiges HMAC |
| Release-Provenienz | implementiert | `release-manifest.json`, GitHub-`dist/*`-Attestierung |
| Release-SBOM | implementiert | sauberer Wheelinstall, `sbom.spdx.json` lokal/SPDX geprüft, attestiert |
| Keyless-Signatur | implementiert | Sigstore über GitHub OIDC |
| Releaseprobe | implementiert | `workflow_dispatch` ohne Release |
| Versionsregeln | implementiert | `remediation.json` Version, Szenario, Dateien, IDs, v1-Vertrag |

<a id="required-before-enterprise-claims"></a>
## Vor Enterprise-Aussagen

<a id="local-only-enforcement"></a>
### Nur lokal

Standardziele bleiben lokal:

- `offline://...`
- `local://...`
- `127.0.0.1`
- `localhost`
- `localhost.localstack.cloud`

Externe HTTP-Ziele standardmäßig abgelehnt. Echte Cloud benötigt explizites standardmäßig ausgeschaltetes `--allow-live-cloud`. `events.jsonl` erfasst Zustimmung, Red-Events Gatezustand pro Befehl. `allowed_target_hosts` kann exakte Namen oder `*.domain` verlangen.

<a id="command-allowlist-policy"></a>
### Befehlsallowlist

Templates beibehalten. Szenariopolicy definiert:

- erlaubte Szenarien
- erlaubte Backends
- erlaubten generierten Skriptnamen
- CLI-Argumente
- maximalen Timeout
- maximale stdout-/stderr-Bytes
- Zielklassen/Hostmuster

Modell erklärt Pfade, erzeugt keine beliebigen Shellbefehle.

`nullstate policy init` erzeugt JSON mit `$schema` auf `docs/schemas/nullstate-policy.schema.json`, geprüft vor Schreiben. `nullstate policy init --scenario <name>` enges Paarpreset für CI statt aller Gerüste. `nullstate policy validate` prüft vorher. `nullstate run --policy-file` erzwingt Namen, Backends, Phasen, `attack.py`-Flags, Klassen, Hosts, Policy-IDs, Timeout-/Ausgabegrenzen vor `attack.py`. Enger als vollständige Engine, aber künftiger Vertrag.

`nullstate run --ci` erzeugt `ci-summary.json` mit Entscheidung, Code, Schwelle, Zahlen, Baseline und Vorher-/Nachherstatus, geprüft gegen `docs/schemas/ci-summary.schema.json`.

<a id="event-schema-hardening"></a>
### Events härten

`red-tool` enthält erste Auditmetadaten:

- `schema_version`
- `command_policy_id`
- `attack_script_sha256`
- `manifest_sha256`

Künftig reichere Policydaten; bereits enthalten:

- `stdout_truncated`
- `stderr_truncated`

Außerdem enthalten:

- `live_cloud_allowed`
- reichere `target_classification`, einschließlich `external-http` bei explizitem Gate

Reproduzierbare Evidenz für CI, Support, Compliance.

`nullstate evidence-manifest` erfasst SHA-256/Größen teilbarer Artefakte für Support/Fallstudie/Ingestion ohne Workspaces, Terraform-Interna, Python-Caches, Manifest selbst, Verifikationsausgabe. `$schema` auf `docs/schemas/evidence-manifest.schema.json` geprüft. `--signing-key-env` liefert HMAC-SHA256 aus Umgebung ohne gespeicherten Schlüssel. `nullstate evidence-verify` rechnet neu, schreibt `evidence-verification.json`, Code `2` bei fehlend/geändert/fremder Run-ID/Signaturfehler.

Tags schreiben `release-manifest.json` und `sbom.spdx.json` aus sauberem Wheel. Struktur und `pyspdxtools` vor Manifest/Attestierung. GitHub bindet Provenienz/SPDX an `dist/*`. Sigstore liefert benachbarte `.sigstore.json` für Wheel, sdist, SBOM, Manifest. Supply-Chain-Provenienz ist getrennt von Run-HMAC.

Manuelles `dry_run=true` probt Build, Prüfung, Attestierung, Signatur, Bundles ohne Veröffentlichung.

`remediation.json` neben `remediation.patch` enthält Regelversion, Szenario, Änderungsflag, Dateien, IDs. `$schema` auf `docs/schemas/remediation-metadata.schema.json`, geprüft vor Verbrauch; Patch bleibt exakt zuordenbar.

`run-bundle.json` ist lokal geprüft, `$schema` auf `docs/schemas/run-bundle.schema.json`; `nullstate bundle` scheitert vor Schreiben bei fehlerhaftem Top-Level.

Dashboard zeigt Befunde, Regeln, Schemainfo, Inventar, Timeline, Bericht. Einzelbenutzer/dateibasiert; Teamhistorie, RBAC, Zeitpläne, Compliance bleiben bezahlt.

<a id="artifact-scrubbing"></a>
### Bereinigung

Vor Veröffentlichung/Upload `nullstate scrub`: Kopie mit Entfernung von

- LocalStack-Tokens
- Modellkeys
- Cloud-Konto-IDs
- Azure-Tenant-/Subscription-IDs
- privaten URLs/IP-Karten
- Terraform-State-Werten
- Providercredentials
- rohen Prompts mit Kundenkontext

`scrub-report.json` nennt Dateien und Regelmatches.

`nullstate upload --dry-run` prüft `scrub-report.json`, erfasst `preflight.scrub` in `upload-plan.json`, `$schema` auf `docs/schemas/upload-plan.schema.json`, validiert. Rohe Runs lokal erlaubt, aber `upload_recommended: false` und Warnung.

<a id="evidence-classification"></a>
### Evidenzklassifikation

Nicht übertreiben, Labels:

- `runtime exploit observed`: Ausgabe beweist Objekt-/Blobzugriff.
- `runtime probe did not observe exploit`: Ziel erreicht, Zugriff nach Abhilfe blockiert/unverfügbar.
- `runtime probe inconclusive`: Emulator, Route, Runtime verhindert Beweis.
- `offline deterministic simulation`: keine Liveprobe.

»Ausgenutzt« erfordert Kommandoevidenz oder explizite Offlinesimulation.

<a id="near-term-readiness-tasks"></a>
## Nächste Aufgaben

1. Azure live prüfen und Emulatorgrenzen dokumentieren.
2. Echte Adapter nur mit Providerallowlists und Zustimmung.

<a id="commercial-boundary"></a>
## Kommerzielle Grenze

Open Source behält lokal/offline, LocalStack, Berichte, Bundles, persönliches Dashboard. Bezahlt für Governance:

- zentrale Historie
- RBAC/Audit
- Policy-as-Code
- Managed-Modelle
- Supportbundles
- Complianceexport
- geplante Scans/Alerts
- privates Deployment
