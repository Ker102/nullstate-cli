<a id="enterprise-readiness"></a>
# Préparation entreprise

Contrôles pour passer `nullstate` du prototype hackathon local à DevSecOps entreprise, en séparant l'existant des exigences avant offres team, cloud ou autohébergées.

<a id="current-controls"></a>
## Contrôles actuels

| Contrôle | État | Preuve |
|---|---|---|
| Détection déterministe | implémenté | `src/nullstate/findings.py` |
| Correction déterministe | implémenté | `src/nullstate/remediation.py` |
| Workspace copié | implémenté | original intact |
| Runner rouge contraint | implémenté | uniquement `attack.py` du run |
| Entrées à manifeste | implémenté | `attack-manifest.json` valide scénario, backend, URL et indices de ressources |
| Journal runtime | implémenté | `red-tool` avec sortie/temps |
| Cibles locales | implémenté | HTTP distant refusé par défaut |
| Hashes d'attaque | implémenté | `red-tool` SHA-256 script/manifeste |
| Troncature | implémenté | `red-tool` indique stdout/stderr tronqués |
| Assainissement non destructif | implémenté | `nullstate scrub` copie/expurge |
| Précontrôle upload | implémenté | `nullstate upload --dry-run` consigne l'état et avertit sur brut |
| Contrat upload | implémenté | `docs/schemas/upload-plan.schema.json` et validation CLI |
| Classification | implémenté | runtime, inconclusif, simulation |
| Dashboard/bundle local | implémenté | `nullstate dashboard`, `nullstate bundle`, `docs/schemas/run-bundle.schema.json` |
| Politique rouge | implémenté | `nullstate policy init`, presets, `run --policy-file` imposent scénario, backend, étape, arguments, classe/hôte, commande, timeout, sortie validés |
| Validation politique | implémenté | `nullstate policy validate`, `policy-validation.json` optionnel |
| Manifeste d'intégrité | implémenté | `nullstate evidence-manifest` inventaire SHA-256 validé, HMAC optionnel |
| Vérification | implémenté | `nullstate evidence-verify` détecte absence, changement, copie, HMAC invalide |
| Provenance release | implémenté | tags : `release-manifest.json`, attestations `dist/*` |
| SBOM | implémenté | wheel propre, `sbom.spdx.json` vérifié localement/SPDX, attesté |
| Signature sans clé | implémenté | Sigstore via GitHub OIDC |
| Répétition release | implémenté | `workflow_dispatch` valide sans release |
| Règles versionnées | implémenté | `remediation.json` version, scénario, fichiers, IDs, contrat v1 validé |

<a id="required-before-enterprise-claims"></a>
## Avant les promesses entreprise

<a id="local-only-enforcement"></a>
### Local uniquement

Les cibles par défaut restent locales :

- `offline://...`
- `local://...`
- `127.0.0.1`
- `localhost`
- `localhost.localstack.cloud`

HTTP distant refusé par défaut. Le cloud réel exige `--allow-live-cloud` explicite, désactivé par défaut ; `events.jsonl` consigne l'accord et les événements rouges l'état du gate par commande. `allowed_target_hosts` peut imposer hôtes exacts ou suffixes `*.domain`.

<a id="command-allowlist-policy"></a>
### Commandes autorisées

Le runner reste basé sur templates. Politique définissant :

- scénarios autorisés
- backends autorisés
- nom de script généré autorisé
- arguments CLI autorisés
- timeout maximal
- octets stdout/stderr maximaux
- classes cibles et motifs d'hôtes autorisés

Le modèle explique le chemin, sans commandes shell arbitraires.

`nullstate policy init` crée JSON avec `$schema` vers `docs/schemas/nullstate-policy.schema.json`, validé avant écriture. `nullstate policy init --scenario <name>` limite à un couple connu, utile aux CI n'autorisant pas toutes les ébauches. `nullstate policy validate` contrôle avant exécution. `nullstate run --policy-file` impose scénarios, backends, étapes, flags du `attack.py`, classes, hôtes, IDs, plafonds timeout/sortie avant `attack.py`. Ce n'est pas un moteur complet, mais le contrat pour les futures politiques.

`nullstate run --ci` écrit `ci-summary.json` avec décision, code, seuil, comptes, baseline et états avant/après ; vérifié contre `docs/schemas/ci-summary.schema.json` avant écriture.

<a id="event-schema-hardening"></a>
### Durcir les événements

`red-tool` contient les premiers champs d'audit :

- `schema_version`
- `command_policy_id`
- `attack_script_sha256`
- `manifest_sha256`

Ajouter des champs politiques enrichis ; déjà présents :

- `stdout_truncated`
- `stderr_truncated`

Également présents :

- `live_cloud_allowed`
- `target_classification` enrichi dont `external-http` si gate explicitement activé

Ces champs rendent l'audit CI/support/conformité reproductible.

`nullstate evidence-manifest` inventorie hashes SHA-256 et tailles partageables pour support/cas/ingestion, excluant workspaces, internes Terraform, caches Python, manifeste lui-même, sortie de vérification. `$schema` vers `docs/schemas/evidence-manifest.schema.json` validé. `--signing-key-env` ajoute HMAC-SHA256 via environnement sans clé enregistrée. `nullstate evidence-verify` recalcule, écrit `evidence-verification.json`, code `2` si absent, modifié, autre identité de run ou signature invalide.

Tags : `release-manifest.json` SHA-256 et `sbom.spdx.json` du wheel propre. Structure et `pyspdxtools` vérifiés avant attestations. GitHub couvre provenance et SPDX pour `dist/*` ; Sigstore publie `.sigstore.json` adjacents au wheel, sdist, SBOM et manifeste. Provenance de supply chain distincte du HMAC des runs.

Manuel `dry_run=true` répète build, validation, attestations, signatures et bundles sans release GitHub.

`remediation.json` accompagne `remediation.patch` et consigne version, scénario, indicateur, fichiers, IDs. `$schema` vers `docs/schemas/remediation-metadata.schema.json`, validé avant rapports/bundles pour rattacher le patch au contrat exact.

`run-bundle.json` validé localement : `$schema` vers `docs/schemas/run-bundle.schema.json`, `nullstate bundle` échoue avant écriture si contrat top-level invalide.

Dashboard : constats, règles, métadonnées, inventaire, timeline, extrait. Toujours fichier mono-utilisateur ; historique équipe, RBAC, scans planifiés et conformité relèvent du payant.

<a id="artifact-scrubbing"></a>
### Assainissement

Avant publier/uploader/joindre, `nullstate scrub` copie et expurge :

- tokens LocalStack
- clés modèle
- IDs comptes cloud
- IDs Azure tenant/abonnement
- endpoints privés/cartes IP
- valeurs Terraform
- identifiants provider
- prompts bruts contenant contexte client

`scrub-report.json` liste fichiers traités et règles correspondantes.

`nullstate upload --dry-run` vérifie `scrub-report.json`, enregistre `preflight.scrub` dans `upload-plan.json`, `$schema` vers `docs/schemas/upload-plan.schema.json` validé. Brut permis pour planning local mais `upload_recommended: false` et avertissement.

<a id="evidence-classification"></a>
### Classification

Sans surpromesse, utiliser :

- `runtime exploit observed` : sortie prouve l'accès objet/blob.
- `runtime probe did not observe exploit` : cible atteinte, accès bloqué/indisponible après correction.
- `runtime probe inconclusive` : émulateur, route ou support empêche la preuve.
- `offline deterministic simulation` : aucun probe direct.

« Exploité » exige une preuve de commande ou mention explicite de simulation offline.

<a id="near-term-readiness-tasks"></a>
## Tâches proches

1. Valider Azure directement et documenter les limites.
2. Adaptateurs cloud avec listes fournisseur et approbation uniquement.

<a id="commercial-boundary"></a>
## Frontière commerciale

CLI ouverte : local/offline, probes LocalStack, rapports, bundles, dashboard personnel. Payant pour gouvernance :

- historique central
- RBAC/audit
- allowlists policy-as-code
- modèles managés
- workflow support
- exports conformité
- scans/alertes planifiés
- déploiement privé
