<a id="first-10-minutes"></a>
# Die ersten 10 Minuten

Dies ist der sicherste Einstieg für neue Open-Source-Nutzer: Offline-AWS-S3, Mock-Agenten und lokale Artefakte.

Docker, LocalStack, Modellendpunkt und echte Cloud-Zugangsdaten werden nicht benötigt.

<a id="1-install-from-a-checkout"></a>
## 1. Aus einem Checkout installieren

```powershell
git clone https://github.com/Ker102/nullstate-cli.git
cd nullstate-cli
python -m pip install -e .
```

Ist `nullstate` nicht in `PATH`, dieselben Befehle mit `python -m nullstate` verwenden.

<a id="2-check-the-local-environment"></a>
## 2. Lokale Umgebung prüfen

```powershell
nullstate doctor --offline
nullstate status
```

Erwartet:

- CLI zeigt Nullstate-Start-/Statusausgabe
- fehlendes Docker, Terraform, LocalStack oder Modellendpunkte sind hier akzeptabel

<a id="3-run-a-deterministic-offline-scan"></a>
## 3. Deterministischen Offline-Scan ausführen

Vor eigener Ausführung ein bereits bereinigtes Beispiel prüfen:

```powershell
nullstate report --runs-dir examples/sample-runs
nullstate summary --runs-dir examples/sample-runs --json
```

Das Beispiel enthält `report.md`, `run-bundle.json` und `dashboard.html` zur Prüfung der Kernartefakte vor dem Scan.

```powershell
nullstate run examples/aws-public-s3 --offline --mock-agents
```

Erwartet:

- ein S3-Befund zu öffentlichem Zugriff mit hoher Schwere
- Rot vorher: Erfolg
- Rot nachher: blockiert
- Artefakte unter `runs/<run-id>/`

<a id="4-open-the-report"></a>
## 4. Bericht öffnen

```powershell
nullstate report
```

Prüfen:

- Befundzusammenfassung
- Angriffsreasoning
- Abhilfepatch
- Validierungsergebnis
- Laufzeitevidenzklassifikation

<a id="5-build-shareable-local-artifacts"></a>
## 5. Teilbare lokale Artefakte bauen

```powershell
nullstate bundle
nullstate dashboard --open
nullstate sarif
nullstate evidence-manifest
nullstate evidence-verify
```

Generierte Artefakte:

- `run-bundle.json`
- `dashboard.html`
- `nullstate.sarif`
- `evidence-manifest.json`
- `evidence-verification.json`

<a id="6-scrub-before-sharing"></a>
## 6. Vor dem Teilen bereinigen

```powershell
nullstate scrub
```

Kopie aus `scrubbed-runs/` teilen, nicht das rohe `runs/`.

<a id="7-optional-github-actions-gate"></a>
## 7. Optionales GitHub-Actions-Gate

```powershell
nullstate init-ci github --scenario aws-public-s3 --iac-path examples/aws-public-s3
```

Generierte Dateien:

- `.github/workflows/nullstate.yml`
- `nullstate-policy.json`

Beide committen, um das Offline-Gate auf PRs auszuführen. `--iac-path` vor echter Nutzung auf das Terraform-Verzeichnis anpassen.

<a id="8-optional-live-aws-localstack-path"></a>
## 8. Optionaler AWS-LocalStack-Live-Pfad

Nur nach Docker-/LocalStack-Einrichtung verwenden:

```powershell
nullstate sandbox up localstack-aws
nullstate sandbox status localstack-aws
nullstate run examples/aws-public-s3 --target localstack-aws --mock-agents
nullstate report
nullstate sandbox down localstack-aws
```

AWS ist der derzeit belegte lokale Laufzeitpfad. Er deployt die verwundbare Fixture in LocalStack AWS, führt die eingeschränkte anonyme Objektleseprobe aus, korrigiert deterministisch und wiederholt die Probe.

<a id="current-azure-note"></a>
## Aktueller Azure-Hinweis

Azure Blob bietet deterministische Offline-Validierung; live benötigt der LocalStack-Workspace/Nutzer Azure-Emulator-Berechtigung. Endet `localstack/localstack-azure-alpha` mit Code `55`, `docker logs localstack-azure` prüfen; wahrscheinlich ist der Emulator für das Konto nicht aktiviert.
