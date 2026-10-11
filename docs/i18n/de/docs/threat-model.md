<a id="threat-model---nullstate"></a>
# Bedrohungsmodell - nullstate

<a id="system-overview"></a>
## Systemüberblick

nullstate analysiert lokal IaC, führt Sandbox-Angriffe aus oder simuliert sie, nutzt Red-/Blue-Modelle, korrigiert in einer Kopie und liefert Evidenz.

<a id="assets"></a>
## Assets

| Asset | Bedeutung | Sensibilität |
|---|---|---|
| IaC-Quelle | kann Architektur/Geheimnisse zeigen | mittel/hoch |
| Workspace | kopiertes IaC und Abhilfe | mittel |
| Modell-API-Key | Endpunktzugriff | hoch |
| LocalStack-Token | Azure-Image-Zugang | hoch |
| Berichte | öffentliche Evidenz | niedrig/mittel nach Bereinigung |
| Identitäts-/Delegationsgraph | Rechte, Delegation, Tools und erreichbare Systeme | hoch |
| Agentenspeicher/Tools | mögliche Anweisungen, Credentials, abgerufene Daten, Integrationsdetails | hoch |

<a id="trust-boundaries"></a>
## Vertrauensgrenzen

- Nutzershell zur CLI.
- CLI zu Docker/LocalStack/kind.
- CLI zum Modell.
- KI-Agent zu Cloud-Identität, Gateway, Folgedienst und Delegationskontext.
- Generiertes Skript zum lokalen Ausführungsverzeichnis.
- Dokumentation zum öffentlichen Internet.

<a id="actors"></a>
## Akteure

| Akteur | Ziel | Vertrauen |
|---|---|---|
| Betreiber | lokale IaC-Sicherheit prüfen | vertraut |
| Externer Angreifer | Artefakte/Sandbox missbrauchen | unvertraut |
| Red-Agent | Angriffspfad finden | teilweise |
| Blue-Agent | Abhilfe erzeugen | teilweise |
| Kunden-KI | Cloud über eigene/delegierte Identität bedienen | teilweise |
| Kompromittiertes Tool/Speicher | Entscheidungen beeinflussen/Befugnisse missbrauchen | unvertraut |
| Kompromittierte Abhängigkeit | Schadcode ausführen | unvertraut |

<a id="threats"></a>
## Bedrohungen

| Bedrohung | Auswirkung | Wahrscheinlichkeit | Kontrolle | Evidenz |
|---|---|---|---|---|
| Versehentlich echtes Cloud-Ziel | Hoch | Mittel | LocalStack/Plan-only-Standard | CLI-Doku |
| Geheimnis committet | Hoch | Mittel | `.gitignore`, `.env.example`, SECURITY.md | Dateien |
| Sandbox-Ausbruch | Hoch | Mittel | erlaubte Befehle, Kopie | Sandboxmodul |
| Dependency-Kompromittierung | Hoch | Mittel | Dependabot, pip-audit, Review | Workflows |
| Irreführende Modellausgabe | Mittel | Hoch | deterministischer Detektor/Patchvalidator | Tests |
| KI missbraucht Cloud-Befugnis | Hoch | Mittel | Identitätsgraph, Minimalrechte, Delegationstrennung, kontrollierte Validierung | künftiger Identitätsadapter |
| Privilegierter Agent als verwirrter Stellvertreter | Hoch | Mittel | Aufrufer-/Delegationsattribution, Policy, Toolautorisierung | künftiger Adapter |
| Gemeinsame Identität verbirgt Attribution | Hoch | Mittel | getrennte Agent-/Runtime-/Tool-Evidenz wo unterstützt | künftiges Inventar |
| Externer Host kompromittiert, Tenant-ID gültig | Hoch | Mittel | Posture, kurze Föderation, Gateway, Minimalrechte, Widerruf | künftiger Collector |
| Gefälschte/veraltete Posture akzeptiert | Hoch | Mittel | Signatur, Aussteller, Zeitstempel, Aktualität, fail-closed bei hoher Wirkung | künftiger Verifier |

<a id="abuse-cases"></a>
## Missbrauchsfälle

- Nutzer richtet auf Produktions-State.
- Schadabhängigkeit liest CI-Umgebung.
- Bericht enthält echten Token/privaten Endpunkt.
- Red-Agent schlägt Aktionen außerhalb LocalStack vor.
- Container öffnet unerwarteten Port.
- Prompt Injection führt legitimes Tool mit schädlichen Parametern aus.
- Agent für schwachen Nutzer behält/gewinnt breitere Service-Principal-Rechte.
- Kompromittiertes MCP, Connector, Plugin, Speicher oder Dokument lenkt um.
- Mehrere Agenten teilen privilegierte Runtime-ID und verbergen Initiator.
- Nachgelagerte Credentials überschreiten Task-Reichweite/Lebensdauer.
- Fremdagent nutzt gültige Identität eines verwundbaren Hosts böswillig.
- Betreiber versteht Image-Signatur/Hardwareattestierung als Gesamtsicherheitsbeweis.

<a id="residual-risks"></a>
## Restrisiken

- Docker hängt vom Betreibergerät ab.
- LocalStack Azure kann von echtem Azure abweichen.
- CI erzwingt Branchschutz erst nach GitHub-Konfiguration.
- Native Agentenidentitäten/Delegation entwickeln sich und benötigen providerspezifische Evidenz.

<a id="next-improvements"></a>
## Nächste Verbesserungen

- Live-Azure-Validierung bei Emulatorberechtigung.
- Echte Adapter nur mit Providerallowlists und Zustimmung.
- AWS-/Azure-Inventar für native Agenten, Workloads, Delegation, Tools und Folgecredentials.
- Externe Posture explizit verifiziert, beobachtet, betreiberbestätigt, abgeleitet oder unbekannt.
