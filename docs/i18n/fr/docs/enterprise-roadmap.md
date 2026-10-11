<a id="enterprise-and-monetization-roadmap"></a>
# Feuille de route entreprise et monétisation

`nullstate` est envisagé comme futur DevSecOps entreprise, pas seulement CLI hackathon.

<a id="product-positioning"></a>
## Positionnement

`nullstate` valide des chemins cloud par preuves : corréler IaC/AWS/Azure, identifier qui atteint données/capacités, prouver sous contrôle, corriger déterministement et conserver les preuves.

Message :

> Les scanners signalent le possible. Nullstate prouve, corrige et valide le blocage.

Pas d'IaC exhaustive d'un compte : intention IaC plus découverte en lecture seule des ressources, identités, réseau, logs, dérive. Graphe normalisé et reconstruction minimale.

Agents IA comme principaux : identités dédiées, IAM, service principals, identités managées/workload, gateways, délégation. Calculer le rayon si agent, prompts, mémoire, connecteur, MCP, plugin ou credential aval est compromis.

Posture externe : opportunité payante de collecte/vérification continue de binding, provenance, digest, attestation, patchs, réseau, outils, fraîcheur, logs, révocation. Combiner avec données/privilèges sans score opaque.

<a id="target-customers"></a>
## Clients

<a id="primary"></a>
### Principaux

- DevSecOps à forte présence Terraform
- Plateformes de modules IaC sûrs par défaut
- Sécurité cloud vérifiant SLA de correction
- Consultancies à preuves

<a id="secondary"></a>
### Secondaires

- Startups régulées sans envoi IaC au SaaS
- Entreprises IA privée sécurité
- MSP/migration

<a id="core-value-propositions"></a>
## Valeur

<a id="1-evidence-over-alerts"></a>
### 1. Preuves plutôt qu'alertes

Les scanners s'arrêtent souvent aux constats. `nullstate` produit :

1. constat
2. raisonnement rouge
3. commande sandbox
4. patch
5. validation après
6. rapport

<a id="2-local-first-and-private"></a>
### 2. Local et privé

IaC, plans, logs sensibles restent chez le client ; modèles sur endpoints privés compatibles.

<a id="3-deterministic-security-core"></a>
### 3. Déterminisme

Le modèle ne décide pas succès/échec ; détection, correction, validation fiables.

<a id="4-devsecops-native-cli"></a>
### 4. CLI DevSecOps

Interface locale, CI ou environnements éphémères.

<a id="enterprise-product-tiers"></a>
## Éditions

<a id="open-source-cli"></a>
### CLI open source

But : adoption/confiance.

Fonctions :

- local/offline
- bibliothèque limitée
- rapports
- runner contraint
- adaptateurs LocalStack
- docs communauté

<a id="team-edition"></a>
### Team

But : petites équipes/consultants.

Fonctions :

- packs étendus
- HTML/PDF
- assainissement
- baselines
- Actions/GitLab CI
- export historique
- presets modèles privés

Prix possible :

- siège : 19-49 EUR/mois
- ou repo : 49-199 EUR/mois

<a id="enterprise-edition"></a>
### Enterprise

But : grandes sociétés, conformité, privé.

Fonctions :

- policy-as-code outils
- SSO/SAML/OIDC
- audit
- preuves centralisées
- rôles/équipes
- support privé
- scénarios custom
- SLA
- Jira, ServiceNow, Slack, SIEM, GRC

Prix possible :

- annuel dès environ 15k-50k EUR/an
- scénarios/support en supplément

<a id="monetization-paths"></a>
## Monétisation

<a id="path-a-open-core-devsecops-cli"></a>
### A : CLI open-core

Garder le cœur ouvert. Vendre :

- scénarios entreprise
- dashboard cloud
- preuves hébergées
- support privé
- conformité

Avantages :

- adoption développeurs
- crédibilité GitHub
- confiance communauté

Inconvénients :

- frontière gratuit/payant
- charge support

<a id="path-b-security-consultancy-tooling"></a>
### B : Consulting

Différencier les évaluations payantes avec `nullstate`.

Offrir :

- assessment purple-team
- durcissement Terraform
- PR correctifs
- preuves auditables

Avantages :

- premier revenu facile
- pas de SaaS complet
- cas/validation clients

Inconvénients :

- services moins scalables

<a id="path-c-enterprise-private-ai-security-platform"></a>
### C : IA privée entreprise

Couche privée de validation IaC/cloud.

Avantages :

- récit MI300X aligné
- budgets supérieurs

Inconvénients :

- ventes longues
- durcissement/intégrations

<a id="recommended-near-term-strategy"></a>
## Stratégie proche

Hybride A+B :

1. CLI ouverte.
2. Marque technique de validation étayée.
3. Portfolio/cas pour attirer.
4. Services d'abord.
5. Besoins récurrents convertis en fonctions Team/Enterprise.

<a id="product-architecture-cli-local-gui-and-paid-platform"></a>
## Architecture CLI, GUI et plateforme

CLI moteur ouvert local/CI, artefacts et bundles portables.

GUI gratuite mono-utilisateur lit `runs/`, dashboards, actions run/report/bundle/sandbox. Pas de login cloud ni team/conformité/alertes/modèles managés.

Application payante cloud/autohébergée ingère bundles et fournit équipes, modèles, historique, support, automation, alertes, intégrations, RBAC, audit, conformité.

`run-bundle.json` relie CLI, viewer gratuit, CI, support, futur payant. `docs/schemas/run-bundle.schema.json` définit v1, validé avant écriture.

`nullstate upload --dry-run` sans réseau : endpoint, checksum, comptes, présence token, précontrôle sans envoi/valeur. `docs/schemas/upload-plan.schema.json` définit v1 validé.

<a id="ci-and-managed-model-inference"></a>
## CI et inférence

Deux modes :

- Client : secrets `NULLSTATE_LLM_BASE_URL` et `NULLSTATE_LLM_API_KEY`.
- Nullstate : `NULLSTATE_CLOUD_TOKEN` et raisonnement Cloud.

Managé payant car mesurable par organisation/projet/run/modèle/tokens/latence/coût.

Trois déclencheurs :

1. PR IaC/policy : proposé, baseline, validation jetable optionnelle, gate.
2. Après Terraform/CloudFormation/Bicep/autre : inventaire, dérive, chemins.
3. Planifié : console, non géré, permissions, nouveaux endpoints, risque ancien, hors Git.

Production découverte en lecture seule ; checks non destructifs approuvés. Exploits vers émulateur/twin/cluster/compte AWS/abonnement Azure dédié selon fidélité.

<a id="support-automation-and-alerts"></a>
## Support/alertes

Panel payant ; ticket avec bundle assaini, version, ID, scénario et dashboard.

Scans planifiés repos connectés/IaC uploadé ; alertes critiques nouvelles, exploit observé, correction/CI échoué, risque ancien, endpoint modèle. Email/webhooks puis Slack, Teams, Jira, GitHub Issues, SIEM.

<a id="brand-direction"></a>
## Marque

<a id="name"></a>
### Nom

`nullstate` évoque une baseline sûre.

<a id="tagline-options"></a>
### Slogans

- Prouver, corriger, valider le risque IaC.
- Purple-team Terraform.
- Du constat au chemin bloqué.
- DevSecOps cloud étayé.
- Validation locale IaC.

Slogan principal :

> Prouver, corriger, valider les chemins cloud.

<a id="brand-personality"></a>
### Personnalité

- précise
- technique
- fiable
- sécurité d'abord
- entreprise
- sans hype

Pas d'agent hacker autonome avant maturité. Préférer :

- exécution rouge contrainte
- validation par preuves
- boucle locale

<a id="enterprise-reliability-requirements"></a>
## Fiabilité

Avant usage métier :

1. Probes réels centraux.
2. Distinguer simulation/inférence/observation.
3. Commandes autorisées par politique ; champs scénario/backend/étape/arguments/classe/hôte/commande/timeout/sortie déjà validés.
4. Assainissement.
5. Schémas stables : manifests générés validés avant probe.
6. CI machine ; `nullstate run --ci`, `ci-summary.json` validé disponibles.
7. SARIF/JSON et policy-result disponibles.
8. Manifestes reproductibles : `nullstate evidence-manifest` SHA-256/HMAC, v1 validé, `nullstate evidence-verify`.
9. Release : checksum, wheel propre, `sbom.spdx.json`, attestations package/SBOM, Sigstore, dry-run.
10. `remediation.json` version/fichiers/IDs, `$schema` et validation v1.
11. Pas de vrai cloud sans activation.

<a id="next-feature-priorities"></a>
## Priorités

<a id="p0-trust-and-correctness"></a>
### P0 : Confiance

- lecture S3 réelle
- preuves runtime rapport
- assainissement
- verdict/codes `ci-summary.json`

<a id="p1-cicd-adoption"></a>
### P1 : CI/CD

- `nullstate run --ci`
- `nullstate sarif`
- template Actions
- `nullstate baseline`, `--baseline-file`
- `nullstate upload --dry-run`
- `docs/schemas/upload-plan.schema.json`
- `docs/schemas/attack-manifest.schema.json`

<a id="p2-enterprise-controls"></a>
### P2 : Entreprise

- policy scénarios/backends/étapes/classes/hôtes/commandes/timeouts/sortie
- presets `nullstate policy init`
- `docs/schemas/nullstate-policy.schema.json`
- config organisation
- `nullstate evidence-manifest`
- `docs/schemas/evidence-manifest.schema.json`
- `nullstate evidence-verify`
- HMAC optionnel
- provenance GitHub
- SBOM GitHub
- Sigstore
- checklist premier tag
- `remediation.json` validé
- identités IA AWS/Azure
- séparer agent/délégation/runtime/tool/credentials
- injections/excessive agency synthétiques et contrôlées
- confiance interagents/identités partagées
- posture externe/fraîcheur
- signature/digest/SLSA/SPIFFE/SPIRE/hardware
- gateway réduit si preuves absentes/périmées

<a id="p3-growth-and-brand"></a>
### P3 : Croissance

- portfolio
- vidéo
- blog technique
- comparaison scanners
- landing GIF CLI

<a id="case-study-angle"></a>
## Étude de cas

Pas « scanner construit », mais :

> CLI locale transforme Terraform en boucle reproductible : détecter, raisonner, commande contrainte, corriger, bloquer, conserver.

Réserve honnête :

> Frontière sûre déjà en place. Prochaine itération élargit probes de santé en exploits réels sandbox.

Cette honnêteté renforce la crédibilité.

<a id="success-metrics"></a>
## Mesures

Technique :

- scénarios observés
- faux positifs fixtures
- succès correction
- reproductibilité
- preuves complètes

Métier :

- étoiles/forks
- vidéo complète
- conversations entrantes
- pilotes
- leads payants
- CI récurrent

<a id="90-day-roadmap"></a>
## 90 jours

<a id="days-1-14"></a>
### Jours 1-14

- vrai S3
- section runtime
- scrubber
- walkthrough soigné
- cas publié

<a id="days-15-30"></a>
### Jours 15-30

- Azure réel ou limites
- CI au-delà baseline/seuil
- SARIF/JSON
- Actions exemple

<a id="days-31-60"></a>
### Jours 31-60

- packs AWS/Azure
- policy commande/classe/hôte
- intégrité
- signature vérifiée
- landing par cas

<a id="days-61-90"></a>
### Jours 61-90

- premier partenaire
- offre assessment
- prototype team/preuves
- architecture entreprise
