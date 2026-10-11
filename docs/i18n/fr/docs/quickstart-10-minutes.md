<a id="first-10-minutes"></a>
# Les 10 premières minutes

Ce guide est le chemin le plus sûr pour un nouvel utilisateur open source : scénario AWS S3 hors ligne, agents simulés et artefacts locaux.

Aucun Docker, LocalStack, endpoint modèle ou identifiant cloud réel nécessaire.

<a id="1-install-from-a-checkout"></a>
## 1. Installer depuis un checkout

```powershell
git clone https://github.com/Ker102/nullstate-cli.git
cd nullstate-cli
python -m pip install -e .
```

Si `nullstate` n'est pas dans `PATH`, utiliser `python -m nullstate` pour les mêmes commandes.

<a id="2-check-the-local-environment"></a>
## 2. Vérifier l'environnement local

```powershell
nullstate doctor --offline
nullstate status
```

Résultat attendu :

- la CLI affiche le lancement/statut Nullstate
- l'absence de Docker, Terraform, LocalStack ou endpoints modèle est acceptable ici

<a id="3-run-a-deterministic-offline-scan"></a>
## 3. Lancer une analyse déterministe hors ligne

Pour inspecter un exemple assaini avant de générer une exécution :

```powershell
nullstate report --runs-dir examples/sample-runs
nullstate summary --runs-dir examples/sample-runs --json
```

L'exemple inclut `report.md`, `run-bundle.json` et `dashboard.html` pour examiner les artefacts essentiels avant l'analyse.

```powershell
nullstate run examples/aws-public-s3 --offline --mock-agents
```

Résultat attendu :

- un constat d'accès public S3 de sévérité élevée
- rouge avant : succès
- rouge après : bloqué
- artefacts sous `runs/<run-id>/`

<a id="4-open-the-report"></a>
## 4. Ouvrir le rapport

```powershell
nullstate report
```

Rechercher :

- résumé des constats
- raisonnement d'attaque
- patch correctif
- résultat de validation
- classification des preuves runtime

<a id="5-build-shareable-local-artifacts"></a>
## 5. Construire des artefacts locaux partageables

```powershell
nullstate bundle
nullstate dashboard --open
nullstate sarif
nullstate evidence-manifest
nullstate evidence-verify
```

Artefacts générés :

- `run-bundle.json`
- `dashboard.html`
- `nullstate.sarif`
- `evidence-manifest.json`
- `evidence-verification.json`

<a id="6-scrub-before-sharing"></a>
## 6. Assainir avant partage

```powershell
nullstate scrub
```

Partager la copie de `scrubbed-runs/`, pas le répertoire brut `runs/`.

<a id="7-optional-github-actions-gate"></a>
## 7. Gate GitHub Actions facultatif

```powershell
nullstate init-ci github --scenario aws-public-s3 --iac-path examples/aws-public-s3
```

Fichiers générés :

- `.github/workflows/nullstate.yml`
- `nullstate-policy.json`

Commiter les deux pour exécuter le gate hors ligne sur les PR. Ajuster `--iac-path` au répertoire Terraform avant usage réel.

<a id="8-optional-live-aws-localstack-path"></a>
## 8. Chemin AWS LocalStack en direct facultatif

Utiliser seulement après configuration de Docker et LocalStack :

```powershell
nullstate sandbox up localstack-aws
nullstate sandbox status localstack-aws
nullstate run examples/aws-public-s3 --target localstack-aws --mock-agents
nullstate report
nullstate sandbox down localstack-aws
```

Ce chemin AWS est le scénario local d'exécution actuellement prouvé. Il déploie le fixture vulnérable dans LocalStack AWS, lance la lecture anonyme contrainte, applique la correction déterministe et relance la sonde.

<a id="current-azure-note"></a>
## Note Azure actuelle

Azure Blob fonctionne en validation déterministe hors ligne, mais LocalStack Azure en direct nécessite l'habilitation Azure Emulator du workspace/utilisateur. Si `localstack/localstack-azure-alpha` sort avec le code `55`, consulter `docker logs localstack-azure` ; Azure Emulator n'est probablement pas activé.
