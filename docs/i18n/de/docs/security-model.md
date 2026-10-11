<a id="security-model"></a>
# Sicherheitsmodell

<a id="assets"></a>
## Assets

| Asset | Bedeutung | Sensibilität |
|---|---|---|
| Terraform-Eingabe | Infrastruktur und mögliche Geheimnisse | mittel/hoch |
| Artefakte | Befunde, Logs, Patches, Modellevidenz | mittel |
| Modellschlüssel | LLM-Zugang | hoch |
| LocalStack-Token | startet Azure-Emulator | hoch |
| Terraform-State | mögliche sensible Infrastrukturinformationen | hoch |

<a id="trust-boundaries"></a>
## Vertrauensgrenzen

- Betreibershell zur nullstate-CLI.
- CLI zum Sandbox-Backend.
- CLI zum Modellendpunkt.
- Agentenanweisungen zur erlaubten Werkzeugausführung.
- Lokale Artefakte zur öffentlichen Dokumentation.

<a id="identities"></a>
## Identitäten

- Betreiber: vertrauenswürdiger Mensch an der CLI.
- Red-Agent: teilweise vertrauenswürdiger Angreifer, lokal beschränkt.
- Blue-Agent: teilweise vertrauenswürdige Abhilferolle.
- Externer Modellserver: nur bezüglich konfiguriertem Endpunktverhalten vertraut.
- CI-Runner: kurzlebige Identität mit Minimalrechten.
- Kunden-KI-Agent: teilweise vertrauter nichtmenschlicher Principal mit eigener Agenten-/Workload-Identität, Service Principal, IAM-Rolle, Managed Identity oder Nutzerdelegation.
- Werkzeug-/Laufzeitidentität: eigener Principal für Host, Gateway, Connector, Plugin, MCP-Server oder nachgelagertes Werkzeug.

Identitätsanalyse muss unterscheiden:

- eigene Identität und Rechte des Agenten
- anfordernder Mensch oder Workload
- delegierte/im Auftrag genutzte Befugnisse
- Laufzeit- und Werkzeugidentitäten
- nachgelagerte Zugangsdaten und Token-Audiences
- finale Ressource und Operation

Delegierte Aktionen nicht nur Mensch oder Agent zuschreiben, wenn beide zur Autorisierung beitrugen.

Für externe Agenten ist gültige föderierte Identität notwendig, aber nicht ausreichend. Hochwirksame Autorisierung sollte auf verfügbarer Laufzeitevidenz beruhen:

- Workload-Identität an erwartete Attribute gebunden
- Deployment-Digest entspricht genehmigtem signiertem Artefakt
- Build-Provenienz und Aussteller geprüft
- erforderliche Laufzeit-/Hardwareattestierung aktuell und gültig
- Netzwerk-/Werkzeugrichtlinien entsprechen genehmigtem Profil
- Widerruf und Audit betriebsbereit

Evidenz als kryptografisch verifiziert, providerbeobachtet, betreiberbestätigt, abgeleitet oder unbekannt klassifizieren. Unbekannt nicht stillschweigend zu vertrauenswürdig erheben.

<a id="network-controls"></a>
## Netzwerkkontrollen

V1 nutzt standardmäßig Offline-Modus oder lokale LocalStack-Endpunkte. Echte Cloud-Ausführung ist standardmäßig außerhalb des Umfangs.

Proben zielen standardmäßig nur auf `offline://...`, `local://...`, `127.0.0.1`, `localhost` oder `localhost.localstack.cloud`. Nicht lokale HTTP(S)-Ziele erfordern explizites `--allow-live-cloud` mit protokollierter Zustimmung. Bei `run --policy-file` kann `allowed_target_hosts` genaue Hostnamen oder `*.domain`-Suffixe verlangen. Integrierte Szenarien bleiben bis zum echten Adapter lokal/offline; Berichte dürfen nur bei passender Ziel- und Ereignisevidenz echte Cloud-Validierung behaupten.

<a id="secret-handling"></a>
## Geheimnisse

- Aus Umgebungsvariablen lesen.
- `.env` und Terraform-State ignoriert.
- `.env.example` dokumentiert Namen ohne Werte.
- Artefaktprüfung vor Fallstudie, Support-Bundle, Screenshot oder Demoarchiv zwingend.
- `nullstate scrub` erzeugt bereinigte Kopien vor Upload, Support oder Veröffentlichung.

<a id="container-security"></a>
## Containersicherheit

LocalStack und andere Sandboxes sind Laufzeitabhängigkeiten, keine mitgelieferten Binärdateien. Vertrauenswürdige Images laden und beliebigen Red-Code außerhalb generierter Workspaces vermeiden.

<a id="red-team-command-execution"></a>
## Red-Team-Befehle

Der V1-Runner ist bewusst beschränkt:

- Nur generiertes `attack.py` ausführen.
- `attack.py` liegt direkt im Ausführungsverzeichnis.
- Bei Manifestnutzung auch `attack-manifest.json` direkt dort.
- Aktueller Python-Interpreter, keine beliebige Shell.
- Dynamisch nur `--target-url`, `--stage` und generierter Manifestpfad.
- Protokoll: Befehl, stdout, stderr, Rückgabecode, URL, Phase, Start, Ende, Dauer.
- Proben per Template erlaubt, nicht vom Modell zur Laufzeit generiert.
- Kurze Timeouts und begrenzte Ausgabe vor Enterprise-Upload oder Langzeitspeicherung.

Dies demonstriert echte lokale Befehle ohne uneingeschränkten Modellwerkzeugzugriff.

Enterprise-Härtung sollte ergänzen:

- explizite Richtlinie je Szenario-/Backend-Paar
- Hostallowlists für Cloud-HTTP(S)-Adapter
- Bereinigung zur Veröffentlichung mit Organisationsregeln
- `--allow-live-cloud` standardmäßig aus

<a id="cicd-security"></a>
## CI/CD-Sicherheit

- PR: Tests, Lint, Typprüfung, Abhängigkeitsaudit.
- CodeQL auf PRs, Pushes und wöchentlich.
- Dependency Review auf PRs.
- Release nur aus Semver-Tags mit GitHub-Attestierungen für Distributionen und `sbom.spdx.json`.
- Minimalrechte in Workflows.

<a id="data-protection"></a>
## Datenschutz

Vor Veröffentlichung prüfen. Keine Tokens, echten Mandanten-/Subscription-IDs, privaten IP-Karten oder Cloud-State veröffentlichen.

<a id="known-risks"></a>
## Bekannte Risiken

- Einige Adapter sind Gerüste, keine Vollbackends.
- LocalStack Azure benötigt externe Einrichtung und Token.
- Offline-Metriken melden null Tokens, weil kein Modell aufgerufen wird.
- Skripte sind bewusst enge Proben; reichere Exploits müssen erlaubt und sandboxbeschränkt bleiben.

<a id="future-improvements"></a>
## Künftige Verbesserungen

- Vollständigere SBOMs aufgelöster Abhängigkeiten aus Lockfiles.
- Breitere organisationsspezifische Schwärzungsregeln.
- Policy-as-Code für Agentenwerkzeuge.
- Cloud-Zustimmung mit auditierbarer Betreiberabsicht.
- Providerspezifische Inventare/Pfadkontrollen für KI-Identitäten, Delegation, Tools und Agentenvertrauen.
