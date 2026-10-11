<a id="cicd"></a>
# CI/CD

<a id="when-nullstate-runs"></a>
## Ausführungszeitpunkte

Drei Sicherheitsfeedbackschleifen sind vorgesehen:

1. **PR-CI:** bei Terraform-, CloudFormation-, Bicep-, Helm-, Policy- oder Infrastrukturänderungen. Sollzustand analysieren, Baseline vergleichen, optional wegwerfbar validieren, SARIF veröffentlichen und nach Schwere fehlschlagen.
2. **Nach Deployment:** nach Erfolg oder relevantem Providerereignis. Istzustand aktualisieren, Drift erkennen, betroffene Pfade prüfen. Destruktive Proben außerhalb Produktion.
3. **Geplante Prüfung:** manuelle Änderungen, unmanaged Ressourcen, Berechtigungsdrift, neue Dienste und Pfade außerhalb Git periodisch erkennen.

PR-CI fragt nach sicherem Merge; Post-Deployment nach erwarteter Realität; periodische Prüfung nach Drift seit letzter Review.

Kunden-CI kann schreibgeschützte AWS-/Azure-ID und privaten Endpunkt oder Managed-Credentials bereitstellen. Künftige Cloud-Integration kann bereinigte Bundles, Inferenz, Historie, Zeitpläne und Alerts bieten.

<a id="branching-model"></a>
## Branchmodell

- `main` geschützt.
- Branches wie `feat/sandbox-localstack`.
- PR für alle Änderungen.
- Tags `vMAJOR.MINOR.PATCH`.

<a id="pull-request-checks"></a>
## PR-Checks

Workflow führt aus:

- Unit-Tests
- Ruff-Lint
- mypy-Typprüfung
- pip-audit

<a id="nullstate-ci-export"></a>
## CI-Export

Ohne Sandbox Offline für deterministische PR-Evidenz verwenden:

```powershell
python -m nullstate policy validate nullstate-policy.json --output artifacts/policy-validation.json
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --ci --fail-on-severity none --runs-dir runs/ci
python -m nullstate policy-result --runs-dir runs/ci --fail-on-severity high
python -m nullstate sarif --runs-dir runs/ci --output artifacts/nullstate.sarif
python -m nullstate evidence-manifest --runs-dir runs/ci --output artifacts/evidence-manifest.json
python -m nullstate evidence-verify --runs-dir runs/ci --manifest artifacts/evidence-manifest.json --output artifacts/evidence-verification.json
python -m nullstate bundle --runs-dir runs/ci
python -m nullstate upload --runs-dir runs/ci --dry-run
```

`--ci` schreibt `ci-summary.json`, Rückgabe `2` bei ursprünglichen Befunden ab `--fail-on-severity`. Schwellen `none`, `low`, `medium`, `high`, `critical`. `$schema` auf `docs/schemas/ci-summary.schema.json`, vor Schreiben validiert.

`nullstate policy-result` schreibt `policy-result.json` aus bestehender Ausführung ohne Wiederholung.

`nullstate policy validate` prüft ohne Szenario, bei `--output` `policy-validation.json`; ungültig/fehlerhaft ergibt `2`.

Demo/Upload: `--fail-on-severity none`. Gates: `--fail-on-severity high` oder `--fail-on-severity critical`. Für Fehler und SARIF-Upload `continue-on-error` behandeln oder Export/Enforcement trennen.

Bei akzeptierten Befunden geprüfte Baseline erstellen:

```powershell
python -m nullstate baseline --runs-dir runs/ci --output nullstate-baseline.json
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --ci --baseline-file nullstate-baseline.json --runs-dir runs/ci-next
python -m nullstate policy-result --runs-dir runs/ci-next --baseline-file nullstate-baseline.json
```

`--baseline-file` erfasst bekannte/neue Zahlen in `ci-summary.json` und wertet nur neue gegen Schwelle aus, bei gleichem validiertem Vertrag.

`nullstate sarif` liest neuesten Run oder ID. SARIF 2.1.0 enthält pro Befund Ergebnis mit Schwere, Evidenz, Abhilfe und logischer IaC-Adresse. `artifacts/nullstate.sarif` zu GitHub oder SARIF-Werkzeug hochladen.

`nullstate evidence-manifest` liefert SHA-256-Inventar vor Tickets/Support/Fallstudie. `$schema` auf `docs/schemas/evidence-manifest.schema.json`, lokal geprüft. `--signing-key-env NULLSTATE_EVIDENCE_SIGNING_KEY` signiert HMAC-SHA256 aus CI-Secret ohne Schlüsselwert. `nullstate evidence-verify` prüft aktuelle Dateien und Signatur bei Key, schreibt `evidence-verification.json`, gibt `2` bei fehlenden/geänderten/fremden Artefakten oder ungültiger Signatur.

Beispiel `.github/workflows/nullstate-sarif.yml` läuft AWS offline mit `--ci --fail-on-severity none`, lädt die verwundbare Demo per `github/codeql-action/upload-sarif` hoch und speichert Artefakte. Für echte Gates auf `high`/`critical` ändern.

Für strikteren Workflow Bootstrap nutzen:

```bash
nullstate init-ci github --scenario aws-public-s3 --iac-path examples/aws-public-s3
```

Schreibt `.github/workflows/nullstate.yml` und `nullstate-policy.json`. Vorlage `docs/templates/github-actions/nullstate-enforcing.yml`, Befehl `nullstate run --ci --fail-on-severity high` mit `continue-on-error: true` erzeugt SARIF, Entscheidung, Manifest, Bundle und Dry-Run, danach Jobfehler bei Gatefehler. Vor Commit `--iac-path`, `--scenario`, `--fail-on-severity` anpassen.

Vor öffentlichem Anhängen oder Support `nullstate scrub` ausführen.

`nullstate upload --dry-run` schreibt `upload-plan.json` beim Bundle für künftige Ingestion ohne Netzwerk/Tokenwerte. `$schema` auf `docs/schemas/upload-plan.schema.json`, lokal validiert, Scrub-Preflight und Warnung ohne `scrub-report.json`.

<a id="security-checks"></a>
## Sicherheitschecks

- CodeQL Python auf PRs, main und wöchentlich.
- Dependency Review bei PR-Änderungen.
- Dependabot für Python/Actions.

<a id="release-flow"></a>
## Releasefluss

```text
manual workflow_dispatch dry_run=true
-> release workflow rehearses package build, SBOM validation, attestations, signing, and signature checks
-> no GitHub release is created
merge to main
-> update CHANGELOG.md
-> tag v0.1.0
-> release workflow builds package
-> release workflow smoke-installs the built wheel and runs nullstate doctor --offline
-> sbom.spdx.json records the installed wheel and runtime dependency versions
-> SBOM validation checks required package fields and root-package relationships
-> SPDX tools validate the generated SBOM document
-> release-manifest.json records SHA-256 digests and sizes
-> GitHub artifact attestations bind provenance and SBOM data to dist/*
-> Sigstore keyless signing writes .sigstore.json bundles beside primary release assets
-> GitHub release created with generated notes
```

Nach Tag Provenienz und SBOM-Predicate per GitHub CLI prüfen:

```powershell
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli --predicate-type https://spdx.dev/Document/v2.3
```

`release-manifest.json` neben Wheel, sdist, `sbom.spdx.json` ist Checksumindex; Attestierungen binden Provenienz/SPDX. SBOM aus sauber installiertem Wheel in `.sbom-venv` erfasst Runtime-Versionen. Workflow prüft SPDX, Felder, Root, Beziehungen und `pyspdxtools` aus `spdx-tools==0.8.5` vor Manifest/Attestierung.

Sigstore-Keyless via GitHub OIDC signiert Wheel, sdist, SBOM und Manifest. Fehlendes angrenzendes `.sigstore.json` führt vor Release zum Fehler.

Vor Tag manuelles `Release` mit `dry_run=true`: Build/Validierung, kein `gh release create`; Veröffentlichung nur bei Tagpush.

Cosign-Prüfung: Tag in `--certificate-identity` ersetzen:

```powershell
$wheel = Get-ChildItem dist\nullstate-*.whl | Select-Object -First 1
cosign verify-blob $wheel.FullName --bundle "$($wheel.FullName).sigstore.json" --certificate-identity "https://github.com/Ker102/nullstate-cli/.github/workflows/release.yml@refs/tags/v0.1.0" --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

<a id="required-repository-settings"></a>
## Erforderliche Einstellungen

Nach Veröffentlichung GitHub konfigurieren:

- `main` schützen
- PR-Review verlangen
- PR Checks und CodeQL verlangen
- Force-Push blockieren
- signierte Commits wenn möglich
- Secret Scanning/Push Protection aktivieren
