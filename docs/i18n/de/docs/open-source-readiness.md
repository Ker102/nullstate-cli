<a id="open-source-readiness-milestones"></a>
# Open-Source-Meilensteine

Praktische Ziele vor stabiler CLI statt `nullstate`-Alpha.

GitHub:

- Meilenstein 1: <https://github.com/Ker102/nullstate-cli/milestone/1>
- Meilenstein 2: <https://github.com/Ker102/nullstate-cli/milestone/3>
- Meilenstein 3: <https://github.com/Ker102/nullstate-cli/milestone/2>

<a id="current-status"></a>
## Status

`nullstate` ist für bewusste Alpha-Nutzer experimenteller Backends bereit. AWS live mit beschränkten Befehlen; Azure deterministisch mit Manifest/Offline, live erst nach Emulatorberechtigung.

<a id="milestone-1-alpha-publication-readiness"></a>
## Meilenstein 1: Alpha-Publikation

Ziel: verständlicher nutzbarer Repo für Evaluatoren.

Status: größtenteils fertig.

Kriterien:

- [x] README-Installation aus Quelle/Tag.
- [x] `nullstate` mit `python -m nullstate`-Fallback.
- [x] Lizenz, Beitrag, Verhalten, Sicherheit.
- [x] Sichere Issuetemplates ohne Geheimnisse.
- [x] Offline ohne LocalStack, Terraform-Cloud-Credentials, Modelle.
- [x] Red-Grenzen ehrlich dokumentiert.
- [x] Laufzeit, Simulation, unklare Proben getrennt.
- [x] Bereinigtes Beispiel ohne Docker. Issue #29.

<a id="milestone-2-stable-local-sandbox-validation"></a>
## Meilenstein 2: Stabile Sandbox

Ziel: verlässlicher lokaler Nachweis.

Status: AWS fertig, Azure extern blockiert.

Kriterien:

- [x] Verwundbare AWS-Ressourcen lokal.
- [x] AWS-`attack.py` anonym vorher/nachher.
- [x] Bericht zeigt Zugriff und Blockierung.
- [x] `sandbox up` scheitert bei Containerende statt Falscherfolg.
- [x] Azure-Berechtigung klar erklärt.
- [ ] Berechtigung oder unterstützter Storageemulator.
- [ ] Azure live vorher/nachher beweisen.
- [ ] Ohne Azure Azurite für `azure-public-blob`. Issue #30.

<a id="milestone-3-open-source-stable-cli"></a>
## Meilenstein 3: Stabile CLI

Ziel: extern installierbar und im Umfang vertrauenswürdig.

Status: nicht fertig.

Kriterien:

- [ ] Installation ohne Clone.
- [ ] Release mit Wheel, sdist, SBOM, Manifest, Attestierung, Prüfung.
- [x] Sauber getestete 10-Minuten-Anleitung.
- [x] Bereinigtes Bundle/Dashboard.
- [x] Nicht-live als Offline/Gerüst markiert.
- [x] Audit/akzeptiertes Risiko.
- [ ] Actions-Dry-Run vor Tag.
- [ ] `pip install` liefert `nullstate` Windows/Linux.

Notizen:

- Windows lokal bestanden 2026-07-03 mit `python scripts/release/install_smoke.py --tag v0.1.0-alpha.2`.
- Linux benötigt Runner/Dry-Run-Bestätigung.

<a id="azure-emulator-decision"></a>
## Azure-Emulatorentscheidung

Token aktiviert Cache-/Trial-Lizenz, aber Workspace/Nutzer hat keinen Imagezugang. LocalStack-Lizenzproblem, keine Azure-Cloud-Berechtigung.

Optionen:

1. Supportzugang für `LOCALSTACK_AUTH_TOKEN` anfragen.
2. Azurite für Blob, öffentliche Lesefunktion, nicht ARM.
3. Kleiner interner Demoemulator: geringste Dependencies, höchste Wartung; Simulator statt Azure nennen.
4. Azure Offline lassen, AWS live priorisieren.

Empfehlung:

Bei schneller Berechtigung LocalStack, sonst Azurite Storage-only und ARM später.
