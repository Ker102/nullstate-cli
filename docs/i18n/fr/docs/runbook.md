<a id="runbook"></a>
# Guide d'exploitation

<a id="local-offline-demo"></a>
## Démo locale hors ligne

```powershell
python -m pip install -e .
python -m nullstate doctor --offline
python -m nullstate status
python -m nullstate run examples/azure-public-blob --offline
python -m nullstate report
```

Exécuter tous les scénarios hors ligne avant enregistrement :

```powershell
python -m nullstate run examples/aws-public-s3 --offline
python -m nullstate run examples/k8s-privileged-pod --offline
python -m nullstate run examples/compose-exposed-admin --offline
python -m nullstate run examples/onprem-ssh-password --offline
python -m nullstate run examples/generic-plan-review --offline
```

`run` utilise `--scenario auto` et `--target auto`. Garder `--scenario` et `--target` explicites pour filmer un adaptateur précis.

<a id="sandbox-discovery"></a>
## Découverte des sandboxes

```powershell
python -m nullstate status
python -m nullstate sandbox list
python -m nullstate sandbox status localstack-azure
python -m nullstate sandbox up localstack-azure --dry-run
```

La plupart des commandes affichent `Next`. Utiliser `python -m nullstate status` pour vérifier configuration, accessibilité de la sonde et dernier rapport.

<a id="localstack-azure-setup"></a>
## Configurer LocalStack Azure

Définir :

```powershell
$env:LOCALSTACK_AUTH_TOKEN = "<token>"
```

Puis :

```powershell
python -m nullstate sandbox up localstack-azure
python -m nullstate sandbox status localstack-azure
```

Si `sandbox up localstack-azure` indique un conteneur arrêté, inspecter :

```powershell
docker logs localstack-azure
```

Si Azure Emulator n'est pas activé, arrêter et résoudre l'habilitation avant réessai. L'image est volumineuse et les réessais peuvent consommer beaucoup de disque.

Garder le fichier env du token non suivi. Découverte automatique de `.env.local` puis `.env` :

```powershell
python -m nullstate sandbox up localstack-azure
python -m nullstate sandbox up localstack-aws
```

Utiliser `--env-file` seulement pour un autre emplacement :

```powershell
python -m nullstate sandbox up localstack-aws --env-file .env.local
```

Alternative Docker Compose :

```powershell
$env:LOCALSTACK_AUTH_TOKEN = "<token>"
docker compose -f docker-compose.localstack-azure.yml up
```

Compose lit `${LOCALSTACK_AUTH_TOKEN}` depuis le shell ou `.env` à côté de `docker-compose.localstack-azure.yml` :

```env
LOCALSTACK_AUTH_TOKEN=your-token-here
```

Git ignore `.env`. Ne jamais commiter le token. Autre emplacement possible avec passage explicite :

```powershell
docker compose --env-file .env.local -f docker-compose.localstack-azure.yml up
```

`env_file:` dans un service injecte des variables au conteneur ; ici il faut l'interpolation Compose de `${LOCALSTACK_AUTH_TOKEN}` avant démarrage.

<a id="reports-and-run-lookup"></a>
## Rapports et recherche

Ouvrir le dernier rapport de `runs/` :

```powershell
python -m nullstate report
```

Dernier rapport d'un dossier de preuves nommé :

```powershell
python -m nullstate report --runs-dir runs/live-aws-model
```

ID connu même dans un dossier imbriqué :

```powershell
python -m nullstate report 20260509-200601 --runs-dir runs
```

Créer une copie assainie avant publication, support ou étude publique :

```powershell
python -m nullstate scrub --runs-dir runs
python -m nullstate scrub 20260509-200601 --runs-dir runs --output-dir scrubbed-runs
```

`scrub` copie dans `scrubbed-runs/` sans toucher l'original et refuse d'écraser une copie existante. Revoir `scrub-report.json` avant partage.

<a id="first-tagged-release-checklist"></a>
## Première publication taguée

Utiliser avant le premier tag produit. Le gel hackathon a été levé le 2026-06-18, mais tags/publication exigent encore l'accord explicite du propriétaire. Branches de fonctionnalité et PR protégées pour le travail courant.

Vérifier les checks du PR candidat :

```powershell
gh pr checks 24
```

Répéter le workflow sans créer de release :

```powershell
gh workflow run Release --field dry_run=true
gh run list --workflow Release --limit 1
```

Vérifier l'installation locale de `nullstate` depuis le wheel :

```powershell
python scripts/release/install_smoke.py
```

Après fusion/tag approuvés, inspecter la release :

```powershell
gh release view v0.1.0
gh release download v0.1.0 --dir dist
```

Vérifier provenance et attestations SBOM :

```powershell
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli --predicate-type https://spdx.dev/Document/v2.3
```

Vérifier le bundle Sigstore du wheel :

```powershell
$wheel = Get-ChildItem dist\nullstate-*.whl | Select-Object -First 1
cosign verify-blob $wheel.FullName --bundle "$($wheel.FullName).sigstore.json" --certificate-identity "https://github.com/Ker102/nullstate-cli/.github/workflows/release.yml@refs/tags/v0.1.0" --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

Confirmer les ressources :

- wheel et distribution source
- `release-manifest.json`
- `sbom.spdx.json`
- bundles `.sigstore.json` adjacents aux artefacts principaux

<a id="model-endpoint-setup"></a>
## Configurer le modèle

Pour vLLM/SGLang autohébergé ou proxy privé compatible OpenAI servant les deux rôles :

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_LLM_BASE_URL = "http://localhost:8000"
$env:NULLSTATE_LLM_API_KEY = "<optional>"
```

Exécuter normalement ensuite.

Google AI Studio / Gemini : preset et clé ; la CLI fournit l'URL compatible :

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
python -m nullstate run examples/azure-public-blob --red-model gemini-3.5-flash --blue-model gemini-3.5-flash
```

Claude : le preset `claude` emploie la compatibilité SDK OpenAI d'Anthropic :

```powershell
$env:NULLSTATE_LLM_PROVIDER = "claude"
$env:NULLSTATE_LLM_API_KEY = "<anthropic-api-key>"
python -m nullstate run examples/azure-public-blob --red-model claude-sonnet-4-6 --blue-model claude-sonnet-4-6
```

Compatibilité expérimentale. Pour des fonctions Claude spécifiques, ajouter un adaptateur natif Anthropic plutôt qu'étirer le wrapper.

Deux conteneurs/tunnels : endpoints par rôle :

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
$env:NULLSTATE_RED_LLM_API_KEY = "<optional-red-token>"
$env:NULLSTATE_BLUE_LLM_API_KEY = "<optional-blue-token>"
python -m nullstate run examples/azure-public-blob --red-model nullstate-red --blue-model nullstate-blue
```

Une exécution accepte `--llm-provider`, `--red-provider`, `--blue-provider`, `--red-base-url`, `--blue-base-url`. Sans valeurs par rôle, repli sur `NULLSTATE_LLM_PROVIDER`, `NULLSTATE_LLM_BASE_URL`, `NULLSTATE_LLM_API_KEY`. URL explicites prioritaires pour gateways/fixtures.

Sans endpoint d'un rôle, réponse simulée déterministe. On peut développer LocalStack avant accès AMD ; l'endpoint sert aux preuves MI300X et métriques tokens/débit, pas à la boucle déterministe.

`--offline` contrôle Terraform/cloud, pas le modèle. Un endpoint partagé/par rôle configuré reste appelé avec analyse statique :

```powershell
$env:NULLSTATE_LLM_BASE_URL = "http://127.0.0.1:8001"
python -m nullstate run examples/azure-public-blob --offline --blue-model nullstate-qwen3-4b --red-model nullstate-qwen3-4b
```

Utiliser `--mock-agents` pour aucun appel modèle :

```powershell
python -m nullstate run examples/azure-public-blob --offline --mock-agents
```

<a id="amd-developer-cloud--digitalocean-path"></a>
## AMD Developer Cloud / DigitalOcean

Suivre [Stratégie AMD](compute-strategy.md). Construire la baseline sans GPU puis raccorder MI300X quand disponible.

Voir [Service des modèles](model-serving.md) pour les deux conteneurs Qwen3.5/Gemma 4.

<a id="fireworks-fallback"></a>
## Repli Fireworks

Si l'accès AMD tarde, diriger `NULLSTATE_LLM_BASE_URL` vers l'endpoint managé sans changer le flux. Étiqueter comme inférence managée, pas GPU privé.

<a id="metrics-evidence"></a>
## Preuves métriques

Endpoint configuré : tentative de collecte :

```text
<NULLSTATE_LLM_BASE_URL>/metrics
<NULLSTATE_RED_LLM_BASE_URL>/metrics
<NULLSTATE_BLUE_LLM_BASE_URL>/metrics
```

Si métriques Prometheus vLLM disponibles, écrit :

- `vllm-metrics-before.prom`
- `vllm-metrics-after.prom`
- `vllm-metrics-red-before.prom` et snapshots par rôle si endpoints différents
- compteurs analysés dans `metrics.json`

Snapshot GPU local avec `amd-smi` puis `rocm-smi`. Sans outils, `metrics.json` indique `status: unavailable` sans échec.

<a id="work-you-can-do-before-amd-gpu-access"></a>
## Travail avant accès AMD

Pendant l'attente du support :

- projet DigitalOcean et firewall
- clés SSH et moindre privilège
- droplet sans GPU pour smoke tests
- Docker et politique de mise à jour
- noms des secrets/environnements GitHub
- `.env` local d'après `.env.example`
- captures assainies des workflows, checks PR et démo offline
- token/accès Azure LocalStack si disponible

<a id="artifact-review-before-publishing"></a>
## Revue avant publication

Vérifier :

- `runs/<id>/report.md`
- `runs/<id>/findings.json`
- `runs/<id>/events.jsonl`
- `runs/<id>/remediation.json`
- `runs/<id>/metrics.json`
- `runs/<id>/vllm-metrics-before.prom`
- `runs/<id>/vllm-metrics-after.prom`
- `runs/<id>/remediation.patch`

Ne pas publier secrets, vrais IDs tenant/abonnement, endpoints privés ou état Terraform.
