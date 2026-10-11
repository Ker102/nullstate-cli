<a id="technical-walkthrough"></a>
# Parcours technique

Ce document explique le fonctionnement de `nullstate`, de la première commande CLI à l'artefact final du rapport. Il s'adresse aux personnes qui examinent le projet et souhaitent comprendre le chemin d'implémentation, les limites de sécurité et les points d'extension actuels.

<a id="what-nullstate-runs"></a>
## Ce qu'exécute Nullstate

`nullstate` est une boucle d'équipe violette pour l'infrastructure en tant que code, privilégiant l'exécution locale. L'implémentation actuelle se concentre sur les scénarios d'exposition du stockage avec Terraform :

- Blocage de l'accès public AWS S3 désactivé
- Accès public aux conteneurs Azure Blob

Elle inclut également des squelettes de scénarios hors ligne pour Kubernetes, Docker Compose, les jumeaux numériques sur site et la revue générique de plans.

La CLI combine trois couches :

1. Logique de sécurité déterministe pour les constats, la remédiation et la validation de réussite ou d'échec.
2. Adaptateurs de sandbox pour les cibles d'exécution locales telles que LocalStack.
3. Raisonnement des équipes rouge et bleue assisté par modèle via des endpoints compatibles avec OpenAI.

Le modèle aide au raisonnement et à l'explication. Il n'est pas la source de vérité pour déterminer si la vulnérabilité existe ou si la remédiation a fonctionné.

<a id="demo-command-flow"></a>
## Enchaînement des commandes de démonstration

Enchaînement hors ligne typique :

```powershell
nullstate
nullstate status
nullstate run examples/aws-public-s3 --offline
nullstate report
```

Enchaînement typique d'exécution réelle avec LocalStack AWS :

```powershell
nullstate sandbox up localstack-aws
nullstate sandbox status localstack-aws
nullstate run examples/aws-public-s3 --target localstack-aws
nullstate report
```

Enchaînement typique d'exécution réelle avec LocalStack Azure :

```powershell
nullstate sandbox up localstack-azure
nullstate sandbox status localstack-azure
nullstate run examples/azure-public-blob --target localstack-azure
nullstate report
```

Lorsqu'un endpoint de modèle auto-hébergé est disponible, utiliser le fournisseur personnalisé et définir un endpoint partagé :

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_LLM_BASE_URL = "http://127.0.0.1:8000"
```

Ou définir des endpoints propres à chaque rôle :

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
```

Les préconfigurations de fournisseurs gérés peuvent éviter la configuration des endpoints aux utilisateurs qui fournissent leurs propres clés :

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
```

La préconfiguration `claude` est également disponible via la couche de compatibilité avec le SDK OpenAI d'Anthropic, mais elle doit être considérée comme expérimentale tant qu'il n'existe pas d'adaptateur Claude natif.

<a id="runtime-modes"></a>
## Modes d'exécution

<a id="offline-mode"></a>
### Mode hors ligne

`--offline` ignore l'exécution de Terraform et les appels à l'émulateur cloud. La CLI utilise une analyse statique de l'IaC et un comportement déterministe des scénarios. Ce mode sert aux démonstrations reproductibles, aux tests et au développement sans Docker, LocalStack ou GPU.

Détail important : `--offline` ne désactive pas automatiquement les appels aux modèles. Si les variables d'environnement des endpoints de modèles sont configurées, les appels des agents rouge et bleu utilisent toujours ces endpoints. Utiliser `--mock-agents` lorsque le comportement attendu doit être entièrement déterministe et sans modèle.

<a id="live-localstack-mode"></a>
### Mode d'exécution réelle avec LocalStack

Le mode réel copie le projet Terraform dans un espace de travail d'exécution, lance les commandes d'automatisation Terraform, cible LocalStack, exécute la boucle rouge/bleue, applique la remédiation dans l'espace de travail copié et valide de nouveau.

Le répertoire Terraform d'origine n'est pas modifié. La remédiation a lieu dans :

```text
runs/<run-id>/workspace/
```

<a id="model-endpoint-mode"></a>
### Mode endpoint de modèle

L'endpoint de modèle doit exposer une API compatible avec OpenAI. Cela permet à la même intégration CLI de fonctionner avec vLLM local, SGLang, des préconfigurations de fournisseurs gérés ou un proxy personnalisé.

La résolution du fournisseur suit cet ordre :

1. options CLI ou valeurs d'environnement propres au rôle
2. options CLI ou valeurs d'environnement partagées
3. URL par défaut de la préconfiguration du fournisseur
4. repli sur un agent simulé déterministe lorsqu'aucun endpoint n'est configuré

La préconfiguration `google` correspond à l'endpoint de Gemini compatible avec OpenAI. La préconfiguration `claude` correspond à l'endpoint de compatibilité avec le SDK OpenAI d'Anthropic. Les modes `custom` et `openai-compatible` nécessitent une URL de base, sauf si une URL propre au rôle est fournie.

La CLI enregistre le nombre de tokens du modèle et la latence à partir des champs `usage` de la réponse, lorsqu'ils sont disponibles. Elle tente également de collecter les `/metrics` de style Prometheus de l'endpoint et écrit les instantanés bruts des métriques dans le répertoire d'exécution.

<a id="end-to-end-execution-path"></a>
## Chemin d'exécution de bout en bout

<a id="1-command-entry"></a>
### 1. Entrée de la commande

Point d'entrée :

```text
src/nullstate/cli.py
```

La commande `run` reçoit :

- le répertoire Terraform
- le backend cible, ou `auto`
- le scénario, ou `auto`
- les options hors ligne ou de simulation
- le répertoire des artefacts d'exécution
- les paramètres des modèles rouge et bleu

Si aucune commande n'est fournie, la CLI affiche l'écran de lancement aux couleurs du produit et les commandes suivantes probables.

<a id="2-scenario-inference"></a>
### 2. Inférence du scénario

Fichiers concernés :

```text
src/nullstate/scenario_detection.py
src/nullstate/scenarios.py
```

Lorsque `--scenario auto` est utilisé, la CLI inspecte le répertoire IaC et associe l'entrée à un scénario connu. Par exemple :

- `examples/aws-public-s3` correspond à `aws-public-s3`
- `examples/azure-public-blob` correspond à `azure-public-blob`

La définition du scénario choisit le backend de sandbox par défaut. Les utilisateurs peuvent toujours remplacer ce choix avec `--target`.

<a id="3-sandbox-backend-selection"></a>
### 3. Sélection du backend de sandbox

Fichier concerné :

```text
src/nullstate/sandbox.py
```

Les backends de sandbox définissent :

- le nom du backend
- le type d'IaC cible
- le mode d'exécution
- l'image Docker
- les commandes de démarrage et d'arrêt
- les sondes d'exécution

Les backends actuels comprennent :

| Backend | Objectif |
|---|---|
| `localstack-aws` | Exécution réelle de scénarios de stockage de type AWS |
| `localstack-azure` | Exécution réelle de scénarios de stockage de type Azure |
| `kind-kubernetes` | Squelette de scénario Kubernetes |
| `docker-compose` | Squelette de jumeau numérique Docker Compose |
| `microvm-onprem` | Squelette de jumeau numérique sur site |
| `plan-only` | Mode d'analyse sans exécution |

`nullstate sandbox up` démarre le backend. `nullstate sandbox status` vérifie Docker et l'accessibilité HTTP lorsque cela s'applique.

<a id="4-run-workspace-creation"></a>
### 4. Création de l'espace de travail d'exécution

La CLI crée un nouveau répertoire d'exécution :

```text
runs/<run-id>/
```

Elle copie le répertoire Terraform fourni en entrée dans :

```text
runs/<run-id>/workspace/
```

Cela conserve le projet d'origine intact. L'état Terraform, `.terraform`, les plans en cache et les répertoires d'exécution sont exclus de la copie.

<a id="5-terraform-plan-loading"></a>
### 5. Chargement du plan Terraform

Fichier concerné :

```text
src/nullstate/terraform.py
```

En mode réel, le flux Terraform suit des commandes adaptées à l'automatisation :

```text
terraform init -input=false
terraform plan -out=tfplan -input=false
terraform show -json tfplan
```

En mode hors ligne, la CLI utilise un analyseur Terraform statique pour les jeux de données de démonstration pris en charge. Cela garantit la reproductibilité des tests et des démonstrations, même sans dépendances d'exécution externes.

Les résultats des commandes Terraform sont écrits dans :

```text
runs/<run-id>/events.jsonl
```

<a id="6-finding-detection"></a>
### 6. Détection des constats

Fichier concerné :

```text
src/nullstate/findings.py
```

Le détecteur déterministe identifie les configurations risquées prises en charge. Exemples :

- Le conteneur Azure Blob présente `container_access_type = "blob"` ou `"container"`
- Le compte de stockage Azure autorise les éléments publics imbriqués
- Les contrôles de blocage de l'accès public AWS S3 sont désactivés

Les constats sont écrits sous forme de JSON structuré :

```text
runs/<run-id>/findings.json
```

Ces données de constats déterministes constituent la source de vérité pour le reste de l'exécution.

<a id="7-red-team-model-reasoning"></a>
### 7. Raisonnement du modèle de l'équipe rouge

Fichier concerné :

```text
src/nullstate/agents.py
```

L'agent rouge reçoit des instructions internes et des preuves du scénario. L'utilisateur ne fournit pas manuellement de prompt au modèle pendant l'exécution.

Le modèle rouge renvoie un raisonnement sur l'attaque, par exemple :

- un chemin de lecture anonyme d'objet S3
- un chemin de lecture anonyme de conteneur Azure Blob
- les preuves qu'il serait pertinent de collecter

Si aucun endpoint n'est configuré, le rôle se replie sur une sortie simulée déterministe.

<a id="8-constrained-attack-script-execution"></a>
### 8. Exécution contrainte du script d'attaque

Fichiers concernés :

```text
src/nullstate/attack.py
src/nullstate/attack_runner.py
```

`nullstate` écrit un artefact d'attaque généré :

```text
runs/<run-id>/attack.py
runs/<run-id>/attack-manifest.json
```

Le manifeste consigne le scénario, le backend, l'URL cible et les indications sur les ressources que les sondes du scénario peuvent utiliser sans donner au modèle le pouvoir de construire des commandes arbitraires. Il inclut un pointeur `$schema` vers `docs/schemas/attack-manifest.schema.json`, et `nullstate run` valide le manifeste avant l'exécution contrainte des sondes.

L'exécuteur contraint exécute ensuite uniquement ce script généré. Il impose les limites suivantes :

- le nom du script doit être exactement `attack.py`
- le script doit se trouver directement dans le répertoire de l'exécution en cours
- l'exécution utilise l'interpréteur Python courant
- aucune commande shell arbitraire n'est acceptée
- les entrées dynamiques se limitent à `--target-url`, `--stage` et au `attack-manifest.json` généré dans le répertoire d'exécution

L'exécuteur consigne les preuves des commandes avant et après remédiation :

```json
{
  "phase": "red-tool",
  "message": "Allowlisted attack command completed",
  "data": {
    "command": ["python", "attack.py", "--target-url", "...", "--stage", "before", "--manifest", "..."],
    "target_url": "...",
    "stage": "before",
    "returncode": 0,
    "stdout": "...",
    "stderr": "",
    "started_at": "...",
    "ended_at": "...",
    "duration_seconds": 0.123
  }
}
```

Cela fournit au rapport de véritables preuves de commandes tout en évitant un accès non restreint de l'agent rouge aux outils.

Garde-fous d'entreprise pour cette couche :

- La politique de commandes repose sur des modèles de scénarios. Le modèle peut raisonner sur le chemin d'attaque, mais il ne peut pas choisir une commande shell arbitraire.
- `nullstate policy init` crée un fichier de politique référencé par un schéma et le valide avant écriture ; `policy init --scenario <name>` crée une préconfiguration plus restreinte pour une paire scénario/backend. `run --policy-file` impose avant exécution les scénarios, backends et étapes autorisés, les options du `attack.py` généré, les classifications des cibles, les listes d'hôtes cibles autorisés, les identifiants de politiques de commandes et les plafonds de délai et de taille de sortie.
- `nullstate policy validate` vérifie un fichier de politique sans exécuter de scénario et peut écrire `policy-validation.json` comme preuve pour la CI.
- Les cibles d'exécution restent des endpoints de sandbox locaux, sauf si `--allow-live-cloud` est explicitement fourni et consigné.
- Les événements `red-tool` incluent une version du schéma de commande et des empreintes de reproductibilité pour le `attack.py` généré et le manifeste.
- La sortie standard et la sortie d'erreur des sondes doivent être plafonnées avant téléversement, ajout à un ticket ou conservation à long terme des preuves.
- Les rapports doivent distinguer les preuves observées à l'exécution de la simulation déterministe et des sondes non concluantes dans l'émulateur.

<a id="9-deterministic-remediation"></a>
### 9. Remédiation déterministe

Fichier concerné :

```text
src/nullstate/remediation.py
```

Le modèle bleu explique la remédiation, mais le correctif lui-même est produit par la logique de remédiation déterministe.

Pour l'exposition Azure Blob, la remédiation définit :

```hcl
allow_nested_items_to_be_public = false
container_access_type           = "private"
```

Pour l'exposition AWS S3, la remédiation définit les contrôles de blocage de l'accès public à `true` :

```hcl
block_public_acls       = true
block_public_policy     = true
ignore_public_acls      = true
restrict_public_buckets = true
```

Le diff est écrit dans :

```text
runs/<run-id>/remediation.patch
```

<a id="10-re-plan-and-validation"></a>
### 10. Nouveau plan et validation

Après remédiation, la CLI charge de nouveau l'espace de travail corrigé. En mode réel, elle exécute les étapes de planification et d'application Terraform sur l'espace de travail copié. En mode hors ligne, elle analyse de nouveau les fichiers mis à jour.

Le détecteur s'exécute de nouveau. Si le constat a disparu, la simulation d'attaque déterministe renvoie :

```text
Red after: blocked
```

Le script d'attaque contraint s'exécute également une seconde fois avec :

```text
--stage after
```

La sortie de cette commande après remédiation est consignée comme un autre événement `red-tool`.

<a id="11-report-and-metrics"></a>
### 11. Rapport et métriques

Fichiers concernés :

```text
src/nullstate/report.py
src/nullstate/metrics.py
```

Chaque exécution écrit :

| Artefact | Objectif |
|---|---|
| `events.jsonl` | Chronologie complète des événements |
| `findings.json` | Constats de vulnérabilités structurés |
| `attack.py` | Artefact d'attaque contraint généré |
| `attack-manifest.json` | Scénario, backend, URL cible et indications sur les ressources validés par schéma pour les sondes contraintes |
| `remediation.patch` | Diff de remédiation Terraform |
| `remediation.json` | Métadonnées du jeu de règles de remédiation déterministe validées par schéma |
| `metrics.json` | Appels aux modèles, nombres de tokens, latence, métriques des endpoints |
| `ci-summary.json` | Verdict CI lisible par machine et validé par schéma lorsque `--ci` est utilisé |
| `policy-result.json` | Décision de politique JSON autonome pour une exécution existante |
| `report.md` | Résumé lisible par un humain |
| `evidence-manifest.json` | Inventaire SHA-256 des preuves d'exécution partageables lorsque `nullstate evidence-manifest` est utilisé |
| `evidence-verification.json` | Résultat de vérification d'un manifeste lorsque `nullstate evidence-verify` est utilisé |
| `upload-plan.json` | Plan de téléversement sans réseau lorsque `nullstate upload --dry-run` est utilisé |
| `workspace/` | Espace de travail IaC copié et corrigé |

`nullstate report` ouvre le rapport le plus récent par défaut, y compris les rapports imbriqués sous des répertoires d'exécution nommés.

`remediation.json` inclut un pointeur `$schema` vers `docs/schemas/remediation-metadata.schema.json`, et les métadonnées de remédiation générées sont validées avant d'être utilisées par les rapports, les bundles et les artefacts d'exécution.

`nullstate bundle` écrit `run-bundle.json`, le contrat portable de preuves pour les tableaux de bord locaux, les téléversements CI, les bundles de support et la future ingestion par Nullstate Cloud. Le bundle inclut un pointeur `$schema` vers `docs/schemas/run-bundle.schema.json`, et la CLI valide sa structure avant écriture. Le bundle inclut aussi les métadonnées de `remediation.json` lorsqu'elles sont disponibles, afin que les outils en aval puissent afficher la version du jeu de règles de remédiation et les identifiants des règles.

`nullstate dashboard` écrit `dashboard.html`, un tableau de bord local gratuit pour une seule exécution, qui peut être ouvert sans connexion au cloud. Il résume les constats, les métadonnées de remédiation, les métadonnées du schéma du bundle, l'inventaire des artefacts, la chronologie des preuves et l'extrait du rapport.

`nullstate sarif` écrit `nullstate.sarif`, un export SARIF 2.1.0 avec un résultat par constat pour les téléversements CI et d'analyse de code.

`nullstate run --ci` écrit `ci-summary.json` et quitte avec le code `2` lorsque les constats initiaux de l'exécution atteignent ou dépassent `--fail-on-severity`. Le résumé inclut un pointeur `$schema` vers `docs/schemas/ci-summary.schema.json` et est validé avant écriture, ce qui fournit à la CI un contrôle de politique stable sans modifier le rapport destiné aux humains.

`nullstate baseline` écrit une référence JSON des identités de constats. Lorsque `nullstate run --ci --baseline-file` est utilisé, les constats connus de la référence restent visibles, mais le seuil d'échec CI n'est évalué que sur les nouveaux constats.

`nullstate policy-result` écrit le même type de décision de seuil et de référence pour une exécution existante, sans réexécuter le scénario.

`nullstate evidence-manifest` écrit `evidence-manifest.json`, un inventaire d'intégrité déterministe pour les artefacts d'exécution partageables. Le manifeste inclut un pointeur `$schema` vers `docs/schemas/evidence-manifest.schema.json`, et la CLI valide sa structure avant écriture. Il exclut les espaces de travail copiés, les éléments internes de Terraform, les caches Python, le fichier manifeste lui-même et la sortie de vérification. Utiliser `--signing-key-env` pour joindre une signature de preuve HMAC-SHA256 à clé partagée provenant d'un secret d'environnement ; il s'agit d'une signature des preuves d'exécution, et non d'une attestation de provenance de paquet à clé publique.

`nullstate evidence-verify` écrit `evidence-verification.json` après avoir recalculé les empreintes et les tailles de fichiers des artefacts consignés. Il ne vérifie que les artefacts répertoriés dans le manifeste, ignore les nouveaux fichiers sans rapport, vérifie les signatures HMAC lorsque `--signing-key-env` est fourni et quitte avec le code `2` lorsqu'un artefact consigné manque, a changé, a été copié depuis une autre exécution ou présente une signature invalide.

`nullstate upload --dry-run` écrit `upload-plan.json`, actualise `run-bundle.json`, consigne l'endpoint prévu et la variable d'environnement du token, puis confirme l'existence du token sans enregistrer sa valeur. Le plan inclut un pointeur `$schema` vers `docs/schemas/upload-plan.schema.json`, et la CLI valide sa structure avant écriture. Il consigne aussi l'état du contrôle préalable de nettoyage : les exécutions brutes avertissent avec `upload_recommended: false`, tandis que les copies nettoyées disposant de `scrub-report.json` sont marquées comme prêtes au téléversement pour la future ingestion.

`nullstate scrub` crée une copie nettoyée d'une exécution sous `scrubbed-runs/` et écrit `scrub-report.json`. Il laisse l'exécution d'origine intacte et refuse d'écraser une copie nettoyée existante.

<a id="security-boundaries"></a>
## Limites de sécurité

Les limites importantes sont les suivantes :

- Aucune cible cloud réelle par défaut.
- Les modifications Terraform ont lieu dans un espace de travail copié.
- Le modèle rouge ne reçoit aucun accès au shell.
- L'exécuteur d'attaque exécute uniquement le `attack.py` généré dans le répertoire d'exécution.
- Les secrets sont chargés depuis les variables d'environnement ou les fichiers env locaux ignorés.
- Les artefacts d'exécution doivent être examinés avant publication.
- `nullstate scrub` doit être exécuté avant la publication d'études de cas publiques, le téléversement CI ou le partage de bundles de support.
- `--allow-live-cloud` est requis avant de cibler un endpoint cloud non local.

<a id="extension-points"></a>
## Points d'extension

<a id="new-scenario"></a>
### Nouveau scénario

Ajouter ou mettre à jour :

```text
src/nullstate/scenarios.py
src/nullstate/scenario_detection.py
src/nullstate/findings.py
src/nullstate/remediation.py
src/nullstate/attack.py
examples/<scenario-name>/
tests/
```

<a id="new-sandbox-backend"></a>
### Nouveau backend de sandbox

Ajouter les métadonnées et les commandes du backend dans :

```text
src/nullstate/sandbox.py
```

Puis ajouter des tests pour :

- `sandbox list`
- `sandbox status`
- `sandbox up --dry-run`
- `sandbox down`

<a id="richer-red-tooling"></a>
### Outillage rouge plus riche

La prochaine extension sûre n'est pas un accès libre au shell. Elle doit reposer sur une liste d'autorisations par scénario :

- sondes Python générées
- modèles de commandes fixes
- URL cibles exclusivement locales
- délai d'expiration strict
- journalisation complète des événements
- aucun héritage d'identifiants cloud réels

Voir [Préparation à l'entreprise](enterprise-readiness.md) pour la liste des contrôles à compléter avant de présenter les sondes d'exécution comme des preuves pour une équipe ou une entreprise.

<a id="test-coverage"></a>
## Couverture des tests

Commandes principales de validation :

```powershell
python -m unittest discover -s tests -v
python -m ruff check src tests
python -m mypy src
```

Test de fumée utile :

```powershell
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --runs-dir runs/red-tool-smoke
python -m nullstate report --runs-dir runs/red-tool-smoke
```

L'exécution de fumée doit montrer :

- un constat avant remédiation
- `Red before: success`
- `Red after: blocked`
- deux événements `red-tool` dans `events.jsonl`
