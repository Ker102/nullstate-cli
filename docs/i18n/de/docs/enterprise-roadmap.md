<a id="enterprise-and-monetization-roadmap"></a>
# Enterprise- und Monetarisierungsroadmap

`nullstate` als zukünftiges Enterprise-DevSecOps-Produkt, nicht nur Hackathon-CLI.

<a id="product-positioning"></a>
## Positionierung

`nullstate` validiert Cloudangriffspfade evidenzgestützt: IaC und AWS/Azure korrelieren, Identitätszugriff auf Daten/Funktionen bestimmen, kontrolliert beweisen, deterministisch beheben, Evidenz sichern.

Kernaussage:

> Scanner nennen mögliche Fehler. Nullstate beweist, korrigiert und prüft Blockierung.

Keine komplette Konto-IaC nötig. Sollzustand plus Read-only-Inventar, Identitäten, Netzwerk, Logs, Drift ergeben Graphen und minimalen Validierungspfad.

KI-Agenten sind eigene Principals: Agenten-IDs, IAM, Service Principals, Managed-/Workload-IDs, Gateways, Delegation. Blast Radius für kompromittierten Agent, Prompt, Speicher, Connector, MCP, Plugin, Folgecredential berechnen.

Externe Posture als bezahlte Gelegenheit: Bindung, Provenienz, Digests, Attestierung, Patch/Vulnerabilität, Netz, Tools, Aktualität, Logs, Widerruf kontinuierlich prüfen. Mit Daten/Rechten kombinieren statt undurchsichtiger Note.

<a id="target-customers"></a>
## Kunden

<a id="primary"></a>
### Primär

- Terraform-lastiges DevSecOps
- Secure-by-default-IaC-Plattformteams
- Cloud-Sicherheit für Abhilfe-SLAs
- Evidenzbasierte Beratung

<a id="secondary"></a>
### Sekundär

- Regulierte Startups ohne SaaS-Datentransfer
- Unternehmen mit privater Security-KI
- MSPs/Migrationspartner

<a id="core-value-propositions"></a>
## Nutzen

<a id="1-evidence-over-alerts"></a>
### 1. Evidenz statt Warnungen

Scanner stoppen bei Befunden. `nullstate` liefert:

1. Befund
2. Red-Reasoning
3. Sandboxkommando
4. Patch
5. Nachvalidierung
6. Bericht

<a id="2-local-first-and-private"></a>
### 2. Lokal und privat

Sensible IaC, Pläne, Logs bleiben beim Kunden; private kompatible Modelle.

<a id="3-deterministic-security-core"></a>
### 3. Deterministischer Kern

Modell entscheidet nicht Pass/Fail. Erkennung, Abhilfe, Validierung sind reproduzierbar.

<a id="4-devsecops-native-cli"></a>
### 4. DevSecOps-CLI

Lokal, CI, ephemere Validierung.

<a id="enterprise-product-tiers"></a>
## Produktstufen

<a id="open-source-cli"></a>
### Open-Source-CLI

Zweck: Adoption/Vertrauen.

Funktionen:

- lokal/offline
- begrenzte Bibliothek
- Berichte
- beschränkter Runner
- LocalStack-Basis
- Community-Doku

<a id="team-edition"></a>
### Team

Zweck: kleine Teams/Berater.

Funktionen:

- Szenariopacks
- HTML/PDF
- Bereinigung
- Baselines
- Actions/GitLab CI
- Historienexport
- private Endpunktpresets

Möglicher Preis:

- Sitz: 19-49 EUR/Monat
- oder Repo: 49-199 EUR/Monat

<a id="enterprise-edition"></a>
### Enterprise

Zweck: Compliance/private Infrastruktur.

Funktionen:

- Tool-Policy-as-Code
- SSO/SAML/OIDC
- Audit
- zentrale Evidenz
- Rollen/Teams
- privater Betrieb
- Custom-Szenarien
- SLA
- Jira, ServiceNow, Slack, SIEM, GRC

Möglicher Preis:

- Jahresvertrag ab etwa 15k-50k EUR/Jahr
- Szenarien/Support zusätzlich

<a id="monetization-paths"></a>
## Monetarisierung

<a id="path-a-open-core-devsecops-cli"></a>
### A: Open-Core-CLI

Kern offen, monetarisieren:

- Enterprise-Packs
- Cloud-Dashboard
- Evidenzhosting
- privater Support
- Complianceexport

Vorteile:

- Entwickleradoption
- GitHub-Glaubwürdigkeit
- Community-Vertrauen

Nachteile:

- klare Gratis-/Bezahlgrenze
- Supportlast

<a id="path-b-security-consultancy-tooling"></a>
### B: Beratung

`nullstate` unterscheidet bezahlte Assessments.

Angebot:

- IaC-Purple-Team
- Terraform-Härtung
- Abhilfe-PRs
- auditfähige Packs

Vorteile:

- erste Einnahmen leicht
- kein kompletter SaaS
- Kundenbelege/Fallstudien

Nachteile:

- Service skaliert schlechter

<a id="path-c-enterprise-private-ai-security-platform"></a>
### C: Private Enterprise-KI

Private Validierungsebene für IaC/Cloud.

Vorteile:

- MI300X-/Privatnarrativ
- größere Budgets

Nachteile:

- längerer Vertrieb
- Härtung/Integration

<a id="recommended-near-term-strategy"></a>
## Nahstrategie

A+B:

1. CLI offen.
2. Technische Evidenzmarke.
3. Portfolio/Fallstudie.
4. Assessments/Implementierung zuerst.
5. Wiederkehrende Anforderungen als Produkt.

<a id="product-architecture-cli-local-gui-and-paid-platform"></a>
## CLI, lokale GUI, Bezahlplattform

CLI bleibt offener Engine lokal/CI mit Artefakten/Bundles.

Gratis-GUI Einzelbenutzer: `runs/`, Dashboard, run/report/bundle/sandbox. Kein Cloudlogin oder Team/Compliance/Alerts/Managed-Modelle.

Bezahlte Cloud/Self-hosted ingestiert Bundles: Teams, Modelle, Historie, Support, Zeitpläne, Alerts, Integrationen, RBAC, Audit, Compliance.

`run-bundle.json` verbindet CLI, Gratisviewer, CI, Support, Plattform; `docs/schemas/run-bundle.schema.json` beschreibt v1 und wird geprüft.

`nullstate upload --dry-run` ohne Netz: Endpunkt, Checksum, Anzahl, Tokenpräsenz, Scrub-Status, kein Versand/Tokenwert. `docs/schemas/upload-plan.schema.json` v1 geprüft.

<a id="ci-and-managed-model-inference"></a>
## CI/Managed-Inferenz

Zwei Modi:

- Kunde: `NULLSTATE_LLM_BASE_URL`, `NULLSTATE_LLM_API_KEY` als Secrets.
- Nullstate: `NULLSTATE_CLOUD_TOKEN`, Cloud-Red/Blue.

Managed bezahlt, messbar nach Organisation, Projekt, Run, Modell, Tokens, Latenz, Kosten.

Drei Trigger:

1. IaC/Policy-PR: vorgeschlagen, Baseline, optional Wegwerfprüfung, Policygate.
2. Nach Terraform/CloudFormation/Bicep/anderen: Inventar, Drift, Pfade.
3. Periodisch: Console, unmanaged, Rechte, neue URLs, altes Risiko, außerhalb Git.

Produktion read-only; nicht destruktiv explizit erlaubt. Exploits zu Emulator/Twin/Cluster/dedizierter AWS-/Azure-Umgebung je Fidelity.

<a id="support-automation-and-alerts"></a>
## Support/Automation/Alerts

Bezahlpanel mit bereinigtem Bundle, Version, ID, Szenario, Dashboard am Ticket.

Geplante Repos/IaC-Scans; neue kritische Befunde, Exploitevidenz, Abhilfe-/CI-Fehler, altes Risiko, Modellfehler. Email/Webhooks zuerst, dann Slack, Teams, Jira, GitHub Issues, SIEM.

<a id="brand-direction"></a>
## Marke

<a id="name"></a>
### Name

`nullstate` suggeriert sichere Baseline.

<a id="tagline-options"></a>
### Slogans

- IaC-Risiken beweisen, beheben, prüfen.
- Terraform-Purple-Team.
- Befund zum blockierten Pfad.
- Evidenzgestütztes Cloud-DevSecOps.
- Lokale IaC-Angriffsvalidierung.

Primär:

> Cloudpfade beweisen, beheben, prüfen.

<a id="brand-personality"></a>
### Persönlichkeit

- präzise
- technisch
- vertrauenswürdig
- Sicherheit zuerst
- enterprisebewusst
- kein Hype

Kein autonomer Hacker vor tiefem Tooling. Lieber:

- beschränkte Red-Ausführung
- Evidenzvalidierung
- lokaler Purple-Loop

<a id="enterprise-reliability-requirements"></a>
## Zuverlässigkeit

Vor Unternehmenseinsatz:

1. Echte Kernproben.
2. Simuliert/abgeleitet/beobachtet trennen.
3. Policyallowlists; validierte Szenario-/Backend-/Phasen-/Argument-/Klassen-/Host-/Command-/Timeout-/Ausgabekontrollen vorhanden.
4. Bereinigung.
5. Stabile Manifestschemas vor Ausführung geprüft.
6. Maschinen-CI; `nullstate run --ci` und geprüftes `ci-summary.json` vorhanden.
7. SARIF/JSON/Policyresult vorhanden.
8. `nullstate evidence-manifest` SHA-256/HMAC, v1 geprüft, später `nullstate evidence-verify`.
9. Releasechecksums, sauberes Wheel-SBOM, `sbom.spdx.json`, GitHub-Paket-/SBOM-Attestierungen, Sigstore, Dry-Run.
10. `remediation.json` Version, Dateien, IDs, `$schema`, v1-Prüfung.
11. Echte Cloud nur explizit.

<a id="next-feature-priorities"></a>
## Prioritäten

<a id="p0-trust-and-correctness"></a>
### P0: Vertrauen

- echte S3-Leseprobe
- Runtimebericht
- Scrubber
- `ci-summary.json` Verdict/Codes

<a id="p1-cicd-adoption"></a>
### P1: CI/CD

- `nullstate run --ci`
- `nullstate sarif`
- Actions-Vorlage
- `nullstate baseline`, `--baseline-file`
- `nullstate upload --dry-run`
- `docs/schemas/upload-plan.schema.json`
- `docs/schemas/attack-manifest.schema.json`

<a id="p2-enterprise-controls"></a>
### P2: Enterprise

- Policy für Szenarien/Backends/Phasen/Klassen/Hosts/Befehle/Timeout/Ausgabe
- `nullstate policy init`-Presets
- `docs/schemas/nullstate-policy.schema.json`
- Org-Konfig
- `nullstate evidence-manifest`
- `docs/schemas/evidence-manifest.schema.json`
- `nullstate evidence-verify`
- HMAC optional
- GitHub-Provenienz
- GitHub-SBOM
- Sigstore
- Ersttag-Checkliste
- geprüftes `remediation.json`
- KI-IDs AWS/Azure
- Agent/Delegation/Runtime/Tool/Credential trennen
- synthetische Injection-/Excessive-Agency-Tests
- Agententrust/shared IDs
- externe Posture/Freshness
- Signatur/Digest/SLSA/SPIFFE/SPIRE/Hardware
- Gateway reduziert ohne aktuelle Evidenz

<a id="p3-growth-and-brand"></a>
### P3: Wachstum

- Portfolio
- Video
- Blog
- Scannervergleich
- CLI-GIF-Landing

<a id="case-study-angle"></a>
## Fallstudie

Nicht nur Scanner, sondern:

> Lokale CLI wandelt Terraformbefunde in reproduzierbare Erkennung, Reasoning, beschränkten Befehl, deterministische Korrektur, Blockierung und Evidenz.

Ehrlicher Vorbehalt:

> Sichere Commandgrenze im Hackathon; künftig echte Sandbox-Exploits statt Healthprobes.

Das schafft Glaubwürdigkeit.

<a id="success-metrics"></a>
## Erfolg

Technik:

- beobachtete Szenarien
- Fixture-Falschpositive
- Abhilferate
- Reproduzierbarkeit
- Kommandoevidenz

Business:

- Stars/Forks
- Videofertigstellung
- eingehende Gespräche
- Piloten
- bezahlte Leads
- regelmäßige CI

<a id="90-day-roadmap"></a>
## 90 Tage

<a id="days-1-14"></a>
### Tage 1-14

- echtes S3
- Runtimebericht
- Scrubber
- Walkthrough verbessern
- Fallstudie publizieren

<a id="days-15-30"></a>
### Tage 15-30

- Azureprobe/klare Grenzen
- CI über Baseline/Schwelle
- SARIF/JSON
- Actions-Beispiel

<a id="days-31-60"></a>
### Tage 31-60

- AWS-/Azure-Packs
- Policy Commands/Klassen/Hosts
- Integritätsmanifest
- Signaturprüfung
- Fallstudienlanding

<a id="days-61-90"></a>
### Tage 61-90

- erster Designpartner
- Assessmentangebot
- Team-/Evidenzprototyp
- Enterprisearchitektur
