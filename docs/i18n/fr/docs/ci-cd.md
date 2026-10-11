<a id="cicd"></a>
# CI/CD

<a id="when-nullstate-runs"></a>
## Quand Nullstate s'exécute

Trois boucles de retour de sécurité sont visées :

1. **CI de pull request :** changements Terraform, CloudFormation, Bicep, Helm, politiques ou infrastructure. Analyse du proposé, baseline, validation optionnelle en environnement jetable, SARIF et échec selon sévérité.
2. **Validation après déploiement :** succès de déploiement ou événement fournisseur pertinent. Actualiser le cloud observé, détecter la dérive, valider les chemins affectés. Sondes destructives hors production.
3. **Assurance planifiée :** détecter changements manuels, ressources non gérées, dérive des permissions, services exposés et chemins hors Git.

CI demande si la fusion est sûre ; après déploiement si l'état est attendu ; assurance périodique si une dérive existe depuis la dernière revue.

CI client peut fournir identité AWS/Azure en lecture seule et endpoint privé ou identifiants managés. Futur Nullstate Cloud peut recevoir bundles assainis, fournir inférence, historique, planning et alertes.

<a id="branching-model"></a>
## Branches

- `main` protégée.
- Branches comme `feat/sandbox-localstack`.
- PR pour tous les changements.
- Tags `vMAJOR.MINOR.PATCH`.

<a id="pull-request-checks"></a>
## Checks PR

Le workflow lance :

- tests unitaires
- lint Ruff
- types mypy
- audit pip-audit

<a id="nullstate-ci-export"></a>
## Export CI

Sans sandbox, utiliser hors ligne pour preuves déterministes :

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

`--ci` écrit `ci-summary.json` et sort `2` si les constats initiaux atteignent `--fail-on-severity`. Seuils : `none`, `low`, `medium`, `high`, `critical`. Pointeur `$schema` vers `docs/schemas/ci-summary.schema.json`, validation avant écriture.

`nullstate policy-result` produit `policy-result.json` depuis une exécution existante, sans la relancer.

`nullstate policy validate` contrôle sans scénario ; `--output` écrit `policy-validation.json`, code `2` si mal formé/invalide.

Démo/upload seul : `--fail-on-severity none`. Gate : `--fail-on-severity high` ou `--fail-on-severity critical`. Pour échouer et uploader SARIF, gérer `continue-on-error` ou séparer export et enforcement.

Créer une baseline revue si des constats sont acceptés :

```powershell
python -m nullstate baseline --runs-dir runs/ci --output nullstate-baseline.json
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --ci --baseline-file nullstate-baseline.json --runs-dir runs/ci-next
python -m nullstate policy-result --runs-dir runs/ci-next --baseline-file nullstate-baseline.json
```

`--baseline-file` fait compter connus/nouveaux dans `ci-summary.json` et appliquer le seuil aux nouveaux seulement, avec le même contrat validé.

`nullstate sarif` lit le dernier run ou ID. Écrit SARIF 2.1.0, un résultat par constat, avec sévérité, preuves, correction et adresse IaC logique. Uploader `artifacts/nullstate.sarif` vers GitHub ou outil SARIF.

`nullstate evidence-manifest` inventorie SHA-256 avant ticket/support/cas. Pointeur `$schema` vers `docs/schemas/evidence-manifest.schema.json`, validé localement. `--signing-key-env NULLSTATE_EVIDENCE_SIGNING_KEY` signe HMAC-SHA256 via secrets CI sans écrire la clé. `nullstate evidence-verify` compare les fichiers, vérifie la signature si clé fournie, écrit `evidence-verification.json` et sort `2` en cas d'absence, changement, autre run ou signature invalide.

Exemple `.github/workflows/nullstate-sarif.yml` : AWS S3 hors ligne avec `--ci --fail-on-severity none` pour uploader la démo vulnérable via `github/codeql-action/upload-sarif` et conserver les artefacts. Passer à `high`/`critical` pour IaC réel.

Pour plus strict, préférer l'initialisation :

```bash
nullstate init-ci github --scenario aws-public-s3 --iac-path examples/aws-public-s3
```

Écrit `.github/workflows/nullstate.yml` et `nullstate-policy.json` ciblé. D'après `docs/templates/github-actions/nullstate-enforcing.yml`, lance `nullstate run --ci --fail-on-severity high` avec `continue-on-error: true` pour générer SARIF, décision, manifeste, bundle, dry-run, puis fait échouer le job si le gate a échoué. Régler `--iac-path`, `--scenario`, `--fail-on-severity` avant commit.

Exécuter `nullstate scrub` avant pièces jointes publiques/support/cas.

`nullstate upload --dry-run` écrit `upload-plan.json` près du bundle pour l'ingestion future sans réseau ni valeurs de tokens. `$schema` vers `docs/schemas/upload-plan.schema.json`, validation locale, précontrôle d'assainissement, avertissement sans `scrub-report.json`.

<a id="security-checks"></a>
## Sécurité

- CodeQL Python sur PR, pushes main et hebdomadaire.
- Dependency Review sur changements PR.
- Dependabot pour Python/Actions.

<a id="release-flow"></a>
## Publication

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

Après tag, vérifier provenance et prédicat SBOM via GitHub CLI :

```powershell
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli --predicate-type https://spdx.dev/Document/v2.3
```

`release-manifest.json` accompagne wheel, sdist, `sbom.spdx.json` comme index checksums ; les attestations lient provenance/SPDX aux assets. SBOM issu du wheel installé proprement dans `.sbom-venv` avec versions runtime. Validation SPDX, champs, racine, relations puis `pyspdxtools` de `spdx-tools==0.8.5` avant manifeste/attestation.

Signature Sigstore sans clé via GitHub OIDC pour wheel, sdist, SBOM, manifeste. Échec avant release si bundle adjacent `.sigstore.json` absent.

Avant tag, `Release` manuel avec `dry_run=true` exécute build/validation mais pas `gh release create`, réservé aux pushes de tags.

Vérifier avec Cosign et remplacer le tag de `--certificate-identity` :

```powershell
$wheel = Get-ChildItem dist\nullstate-*.whl | Select-Object -First 1
cosign verify-blob $wheel.FullName --bundle "$($wheel.FullName).sigstore.json" --certificate-identity "https://github.com/Ker102/nullstate-cli/.github/workflows/release.yml@refs/tags/v0.1.0" --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

<a id="required-repository-settings"></a>
## Réglages requis

Configurer GitHub après publication :

- protéger `main`
- exiger revue PR
- exiger PR Checks et CodeQL
- bloquer force pushes
- commits signés si possible
- activer secret scanning et push protection
