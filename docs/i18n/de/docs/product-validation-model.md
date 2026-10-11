<a id="product-and-validation-model"></a>
# Produkt- und Validierungsmodell

<a id="product-purpose"></a>
## Produktzweck

Nullstate ist eine evidenzgestützte Plattform zur Validierung von Cloud-Angriffspfaden. Sie korreliert Infrastructure as Code mit dem beobachteten AWS- und Azure-Zustand, analysiert Beziehungen zwischen Netzwerken, Identitäten, Diensten und Daten, validiert ausgewählte Angriffspfade in kontrollierten Umgebungen, wendet Abhilfemaßnahmen an und wiederholt den Angriff.

Das Produkt soll keine perfekte Terraform-Abbildung eines gesamten Cloud-Kontos voraussetzen. IaC beschreibt die beabsichtigte und verwaltete Konfiguration, während schreibgeschützte Erfassung die tatsächlich bereitgestellte Realität beschreibt. Nullstate sollte beides in einem normalisierten Umgebungsgraphen zusammenführen und die Quelle sowie die Konfidenz jeder Beziehung bewahren.

Das Open-Source-Produkt sollte zunächst als lokales DevSecOps-Validierungsframework für Menschen, CI-Jobs und Coding-Agenten dienen. `nullstate summary --json` liefert Agenten ein kompaktes Ausführungsergebnis, statt sie zum Parsen von Markdown-Berichten zu zwingen. `nullstate context validate` und `nullstate context summary --json` definieren einen sicheren, schreibgeschützten Cloud-Kontextvertrag, bevor Live-Kollektoren hinzugefügt werden.

<a id="environment-graph"></a>
## Umgebungsgraph

Der Umgebungsgraph sollte Folgendes akzeptieren:

- Terraform, CloudFormation, CDK-Exporte, Bicep, ARM sowie Plan-/State-Daten der Provider.
- Schreibgeschütztes AWS- und Azure-Ressourceninventar.
- IAM-Rollen, Azure-RBAC-Zuweisungen, Managed Identities, Vertrauensbeziehungen und Workload-Identitäten.
- KI-Agentenidentitäten, Agentenidentitäts-Blueprints, Agenten-Workload-Identitäten, delegierten Nutzerkontext, Werkzeugidentitäten und Beziehungen zu nachgelagerten Zugangsdaten.
- Öffentliche Endpunkte, virtuelle Netzwerke, Sicherheitsgruppen, NSGs, Routen, Gateways, private Endpunkte und Peering.
- Konfiguration von Speicher, Datenbanken, Geheimnisverwaltung, Compute, Serverless, Containern und Kubernetes.
- Native Sicherheitsbefunde, Aktivitätslogs, Flow-Logs, Audit-Logs und ausgewählte Laufzeitmetadaten.
- Optionale Datenklassifizierung, die der Nutzer bereitstellt oder die aus sicheren Metadaten und synthetischen Testdaten abgeleitet wird.

Der Graph muss nicht jede Ressource klonen. Er muss sicherheitsrelevante Pfade erkennen und einen minimalen Angriffspfad-Zwilling erstellen, der nur die zum Testen einer Hypothese erforderlichen Beziehungen enthält.

Die aktuelle Vorschau des Kontextmanifests ist bewusst auf lokale Ausführung beschränkt:

```bash
nullstate context validate examples/cloud-context/aws-readonly-context.json
nullstate context summary examples/cloud-context/aws-readonly-context.json --json
```

Sie validiert die Struktur der Metadaten zu Provider, Konto, Identität, Ressource, öffentlicher Exposition und Datenklassifizierung, ohne Cloud-Zugangsdaten anzufordern. Künftige Kollektoren sollten Daten gemäß diesem Vertrag mithilfe kurzlebiger, schreibgeschützter Cloud-Identitäten ausgeben.

<a id="evaluation-and-product-metrics"></a>
## Evaluation und Produktmetriken

Der Fallstudienwert von Nullstate sollte gemessen und nicht nur beschrieben werden. Das aktuelle Evaluationsframework beginnt mit wiederholbaren internen Benchmarks:

```bash
nullstate eval run examples/eval/iac-security-regression.json --output-dir eval-runs/iac-security-regression
```

Das Framework erfasst Dauer, Befundanzahl, höchsten Schweregrad, Angriffsstatus vorher/nachher, Token-Gesamtzahlen, Artefaktanzahl sowie den Erfüllt/Nicht-erfüllt-Status der Erwartungen. Dies ist der erste Schritt zum Vergleich von Nullstate mit rein scannerbasiertem Review, manuellem Review und Review durch generische Coding-Agenten. Solange diese Vergleichsbaselines fehlen, sollten sich Aussagen auf gemessenes Nullstate-Verhalten beschränken, statt allgemeine Genauigkeit oder Zeitersparnis zu behaupten.

<a id="identity-aware-attack-analysis"></a>
## Identitätsbewusste Angriffsanalyse

Ein offener Port oder ein öffentlicher Container ist nicht der gesamte Befund. Nullstate sollte bewerten, was aus jeder autorisierten Angreiferperspektive erreichbar ist:

| Perspektive | Beispiel |
|---|---|
| Extern | Anonymer Internetclient |
| Tenant-Nutzer | Authentifizierter Cloud-Nutzer mit geringen Rechten |
| Entwickler | Menschliche Identität mit Deployment- oder Leserechten |
| CI-Workload | GitHub-Actions-, GitLab- oder Build-System-Identität |
| Kompromittierter Workload | VM-, Container-, Funktions- oder Anwendungsidentität |
| Cloud-Rolle | AWS-IAM-Rolle, Azure Service Principal oder Managed Identity |
| KI-Agent | Dedizierte Agentenidentität, Agenten-Workload-Identität oder Agenten-Laufzeitrolle |
| Delegierter Agent | Agent, der mit von einem menschlichen Nutzer weitergegebenen Befugnissen handelt |
| Lateraler Akteur | Principal, der durch einen früheren Schritt im Angriffspfad erlangt wurde |

Jedes beobachtete Ergebnis sollte Principal, angenommene Berechtigungen, Authentifizierungsmethode, Ziel, erreichte Daten oder Fähigkeit, Befehlsevidenz und Konfidenz festhalten.

<a id="ai-agents-as-cloud-principals"></a>
## KI-Agenten als Cloud-Principals

KI-Agenten interagieren zunehmend mit Infrastruktur, Cloud-APIs, internen Diensten, Datenspeichern, Ticketsystemen, Quellcode-Repositories und Deployment-Werkzeugen. Dabei können sie Folgendes verwenden:

- eine dedizierte, speziell für den Agenten erstellte Identität
- einen herkömmlichen Service Principal, eine Managed Identity, eine IAM-Rolle oder eine Workload-Identität
- eine von mehreren Agenten gemeinsam genutzte Laufzeit- oder Werkzeugidentität
- delegierte Befugnisse, die von einem menschlichen Nutzer weitergegeben werden
- Zugangsdaten, die für nachgelagerte Werkzeuge oder Drittanbieterdienste erworben wurden

Diese Modi dürfen nicht zu einem einzigen generischen Dienstkonto zusammengefasst werden. Nullstate sollte Agent, Laufzeit, Werkzeug, delegierenden Nutzer, Zugangsdaten und Zieldienst als separate Graphknoten darstellen. So bleibt erhalten, wer eine Aktion eingeleitet hat, wessen Berechtigungen sie autorisiert haben und welche Komponente kompromittiert werden könnte.

Agentenspezifische Angriffspfade umfassen:

- Prompt Injection, die den Agenten zum Missbrauch legitimer Cloud-Berechtigungen veranlasst
- kompromittierte Werkzeuge, Plugins, MCP-Server, Speicher oder abgerufene Inhalte, die Aktionen beeinflussen
- übermäßige Autonomie, die destruktive oder privilegienändernde Operationen außerhalb der vorgesehenen Aufgabe ermöglicht
- einen Confused-Deputy-Pfad, bei dem ein nicht vertrauenswürdiger Nutzer einen privilegierten Agenten dazu bringt, in seinem Auftrag zu handeln
- delegierte Nutzerbefugnisse, mit denen Ressourcen erreichbar werden, auf die die eigene Identität des Agenten nicht zugreifen könnte
- gemeinsame Laufzeitidentitäten, die Zuordnung und das Prinzip der geringsten Rechte unwirksam machen
- Vertrauen zwischen Agenten, das laterale Bewegung ermöglicht
- langlebige oder weitreichende nachgelagerte Zugangsdaten, die den Schadensradius vergrößern

Nullstate sollte mindestens drei getrennte Berechtigungssichten bewerten:

1. **Agenteneigene Berechtigungen:** Ressourcen, die mit der eigenen Identität des Agenten erreichbar sind.
2. **Delegierte Berechtigungen:** Ressourcen, die beim Handeln im Auftrag eines bestimmten Nutzers oder einer bestimmten Nutzerklasse erreichbar sind.
3. **Werkzeugketten-Berechtigungen:** Ressourcen, die über Laufzeitidentitäten, Plugins, Gateways, Konnektoren und nachgelagerte Zugangsdaten erreichbar sind.

Der Bericht sollte die effektive Berechtigungskette erklären und die exponierten Daten und Operationen identifizieren, falls der Agent, seine Anweisungen, sein Speicher oder eines seiner Werkzeuge kompromittiert wird. Sichere Validierung sollte synthetische Prompts, synthetische Daten, kontrollierte Werkzeuge und wegwerfbare Umgebungen verwenden, statt unkontrollierte Prompt Injection gegen Produktionsagenten zu versuchen.

Bei extern gehosteten Agenten reicht Identitätsanalyse allein nicht aus. Nullstate sollte auch die Laufzeit-Sicherheitslage bewerten: Bindung zwischen Workload und Identität, Artefaktprovenienz, Deployment-Digest, Host- und Laufzeitintegrität, Netzwerkexposition, Werkzeugkontrollen, Protokollierung, Widerruf sowie Aktualität und Stärke der unterstützenden Evidenz. Der detaillierte Entwurf steht in [Vertrauen in externe Agenten und Laufzeit-Sicherheitslage](plans/2026-06-22-external-agent-trust-design.md).

Die aktuelle CLI enthält eine erste deterministische Vorschau dieses Modells:

```bash
nullstate agent posture verify examples/agent-trust/external-agent-manifest.json
nullstate agent blast-radius examples/agent-trust/external-agent-manifest.json
```

Diese Befehle arbeiten mit einem lokalen Manifest, nicht mit Live-Kollektoren der Provider. Sie sollen zunächst den Datenvertrag härten: fehlende, veraltete oder unbekannte Evidenz zur Sicherheitslage muss sichtbar bleiben, und delegierte Nutzerbefugnisse müssen von der eigenen Identität des Agenten getrennt werden.

<a id="exposed-data-and-impact"></a>
## Exponierte Daten und Auswirkungen

Cloud-Administratoren können einen erreichbaren Dienst bewusst akzeptieren, weil sie glauben, dass er nichts Kritisches enthält. Nullstate sollte dennoch feststellen, ob der Pfad Folgendes exponiert:

- Objektnamen, Verzeichnislisten, Konto-IDs, Tenant-IDs, Hostnamen oder interne Topologie
- Anwendungslogs, Backups, Diagnoseinformationen, Build-Artefakte, Source Maps oder Deployment-Pakete
- Zugangsdaten, Tokens, Verbindungszeichenfolgen, Konfiguration oder Geheimnisreferenzen
- personenbezogene, finanzielle, regulierte, Kunden- oder proprietäre Daten
- Fähigkeiten zum Schreiben, Löschen, Handeln unter fremder Identität, Ausführen oder Ändern von Richtlinien
- Informationen, die Angriffe auf Zugangsdaten, laterale Bewegung, Privilegieneskalation oder gezieltes Social Engineering ermöglichen

Berichte müssen unterscheiden:

- die Konfiguration deutet auf Exposition hin
- sichere Metadaten wurden beobachtet
- synthetische Evidenzdaten wurden abgerufen
- eine privilegierte Fähigkeit wurde nachgewiesen
- auf sensible Produktionsinhalte wurde bewusst nicht zugegriffen

<a id="why-not-attack-production-directly"></a>
## Warum nicht die Produktion direkt angreifen?

Schreibgeschützte Erfassung und eng begrenzt genehmigte, nicht destruktive Validierung können gegen die Produktion laufen. Autonome Ausnutzung sollte standardmäßig in einer kontrollierten Umgebung erfolgen, weil:

1. Exploits echte Daten verändern, löschen, beschädigen oder offenlegen können.
2. Proben Drosselung, Ausfälle, Kontosperren, Quarantäne oder die Aktivierung der Incident Response verursachen können.
3. IAM-Tests persistente Zugangsdaten, Vertrauensbeziehungen oder Privilegienänderungen erzeugen können.
4. Exfiltrationstests Datenschutz-, Vertrags-, Regulierungs- und Datenresidenzanforderungen verletzen können.
5. Produktionsabhängigkeiten Kunden und Dritte außerhalb des genehmigten Umfangs betreffen können.
6. Die Bereinigung keine exakte Wiederherstellung des vorherigen Zustands garantieren kann.
7. Wiederholte CI-Validierung deterministisch und sicher genug sein muss, um ohne Überwachung jeder Ausführung durch einen Penetrationstester zu laufen.

Das sichere Betriebsmodell lautet:

1. Produktion über schreibgeschützte Provider-APIs erfassen.
2. Angriffshypothesen entwickeln und priorisieren.
3. Nicht destruktive Prüfungen aus einer Freigabeliste nur dann gegen die Produktion ausführen, wenn die Richtlinie dies erlaubt.
4. Den minimalen relevanten Pfad mit synthetischen Daten in einer wegwerfbaren Umgebung rekonstruieren.
5. Eingeschränkte Angriffe gegen diese Umgebung ausführen.
6. Abhilfe anwenden und denselben Angriff wiederholen.
7. Evidenz bewahren und den nachgewiesenen Pfad in einen Regressionstest umwandeln.

<a id="aws-and-azure-first"></a>
## AWS und Azure zuerst

AWS und Azure sollten die ersten Cloud-Provider sein, weil sie einen großen Anteil der Unternehmensinfrastruktur abdecken und beide reife IaC-Ökosysteme haben. Terraform bleibt eine erstklassige Eingabe, kein konkurrierendes Ziel: Terraform für AWS und Terraform für Azure liefern beabsichtigte Topologie und Konfiguration, während die Provider-Erfassung den Live-Zustand und nicht verwaltete Drift liefert.

Die Provider-Adapter sollten auch neue Agentenidentitätssysteme inventarisieren. Microsoft Entra Agent ID liefert spezialisierte Agentenidentitäten und Identitäts-Blueprints, während Amazon Bedrock AgentCore Identity Agenten über Agenten-/Workload-Identitätsmechanismen repräsentiert. Nullstate sollte diese Beziehungen neben herkömmlichen Service Principals, Managed Identities und IAM-Rollen aufnehmen, ohne anzunehmen, dass jede Organisation eine provider-native Agentenplattform nutzt.

Die Genauigkeit bezüglich der Provider sollte abgestuft und explizit sein:

| Stufe | Evidenzquelle | Zweck |
|---|---|---|
| Statisch | IaC, Pläne, Richtlinien und exportierte Konfiguration | Schnelle Analyse vor dem Deployment |
| Beobachtet | Schreibgeschütztes Provider-Inventar und Logs | Tatsächlich bereitgestellten Zustand verstehen |
| Emuliert | LocalStack, Dienstemulatoren, Container oder digitale Zwillinge | Sichere, wiederholbare Validierung mit bekannten Grenzen der Wiedergabetreue |
| Echte Sandbox | Wegwerfbares AWS-Konto oder Azure-Abonnement | Exploit-Validierung mit höchster Wiedergabetreue |

Jeder Bericht sollte die verwendete Stufe nennen. Emulatorevidenz darf niemals als Beweis für identisches Provider-Verhalten dargestellt werden.

<a id="ci-cloud-event-and-scheduled-execution"></a>
## CI-, Cloud-Ereignis- und geplante Ausführung

Nullstate sollte drei sich ergänzende Auslöser unterstützen.

<a id="pull-request-and-iac-ci"></a>
### Pull-Request- und IaC-CI

Auslösen, wenn sich Terraform-, CloudFormation-, Bicep-, Helm-, Richtlinien- oder zugehörige Infrastrukturdateien ändern.

Die Pipeline:

1. Die vorgeschlagene Konfiguration vor dem Deployment analysieren.
2. Befunde mit einer genehmigten Baseline vergleichen.
3. Optional eine wegwerfbare Validierungsumgebung für risikoreiche Änderungen erstellen.
4. Ausgewählte Angriffspfad-Regressionstests ausführen.
5. SARIF, ein maschinenlesbares Richtlinienergebnis und Evidenzartefakte exportieren.
6. Den Merge blockieren, wenn Richtlinienschwellen nicht erfüllt werden.

Dies ist die schnellste Rückkopplungsschleife und verhindert, dass verwundbare Konfigurationen in die Cloud gelangen.

<a id="post-deployment-validation"></a>
### Validierung nach dem Deployment

Nach einem erfolgreichen Deployment-Workflow oder einem Provider-Ereignis auslösen.

Beispiele sind ein Terraform-apply-Job, ein CloudFormation-Deployment, ein Azure-Deployment oder ein Cloud-Ereignis, das eine sicherheitsrelevante Ressourcen- oder Richtlinienänderung anzeigt. Nullstate aktualisiert den beobachteten Umgebungsgraphen, prüft auf Drift und führt nur betroffene sichere Validierungen aus. Potenziell destruktive Validierung wird an eine wegwerfbare Sandbox statt an die aktualisierte Produktionsumgebung geleitet.

<a id="scheduled-assurance"></a>
### Geplante Sicherheitsüberprüfung

Stündlich, täglich oder wöchentlich ausführen, um manuelle Konsolenänderungen, nicht verwaltete Ressourcen, Berechtigungsdrift, neu öffentliche Endpunkte, veraltete Risikoakzeptanzen und durch Änderungen außerhalb von Git entstandene Angriffspfade zu erkennen.

Diese Modi lösen unterschiedliche Probleme:

- PR-CI validiert die beabsichtigte Änderung vor dem Deployment.
- Validierung nach dem Deployment bestätigt, dass der beobachtete Zustand den Erwartungen entspricht.
- Geplante Sicherheitsüberprüfung erkennt Drift und Änderungen außerhalb der üblichen Abläufe.

Die ausgereifte kostenpflichtige Plattform kann alle drei koordinieren, Verlauf aufbewahren, Teams benachrichtigen und verwaltete Modellinferenz bereitstellen. Die Open-Source-CLI bleibt zur lokalen und CI-Ausführung mit kundenseitig bereitgestellten Zugangsdaten und Modellendpunkten fähig.

<a id="provider-references"></a>
## Provider-Referenzen

- [Microsoft Entra Agent ID](https://learn.microsoft.com/en-us/entra/agent-id/)
- [Agentenidentitätskonzepte in Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-identity)
- [Amazon Bedrock AgentCore Identity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity-overview.html)
- [AWS-Leitfaden zu Agentenidentität und Berechtigungsverwaltung](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentsec03.html)
