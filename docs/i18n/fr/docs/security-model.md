<a id="security-model"></a>
# Modèle de sécurité

<a id="assets"></a>
## Actifs

| Actif | Importance | Sensibilité |
|---|---|---|
| Entrée Terraform | infrastructure et secrets possibles | moyenne/élevée |
| Artefacts | constats, logs, patches et preuves modèle | moyenne |
| Clé d'endpoint modèle | accès LLM | élevée |
| Token LocalStack | démarrage de l'émulateur Azure | élevée |
| État Terraform | données d'infrastructure sensibles possibles | élevée |

<a id="trust-boundaries"></a>
## Frontières de confiance

- Shell opérateur vers CLI nullstate.
- CLI vers backend sandbox.
- CLI vers endpoint modèle.
- Instructions d'agent vers outils autorisés.
- Artefacts locaux vers documentation publique.

<a id="identities"></a>
## Identités

- Opérateur : humain de confiance exécutant la CLI.
- Agent rouge : attaquant partiellement fiable limité au sandbox local.
- Agent bleu : rôle correctif partiellement fiable.
- Serveur modèle externe : fiable seulement pour le comportement configuré.
- Runner CI : identité éphémère à permissions minimales.
- Agent IA client : principal non humain partiellement fiable, avec identité dédiée, identité de charge, principal de service, rôle IAM, identité managée ou délégation utilisateur.
- Identité outil/runtime : principal distinct d'hôte, passerelle, connecteur, plugin, serveur MCP ou outil aval.

L'analyse doit distinguer :

- identité et permissions propres de l'agent
- humain ou charge demandant l'action
- autorité déléguée/au nom d'autrui
- identités runtime et outils
- identifiants aval et audiences des tokens
- ressource et opération finales

Ne pas attribuer une action déléguée seulement à l'humain ou l'agent lorsque les deux ont participé à l'autorisation.

Pour les agents externes, une identité fédérée valide est nécessaire mais insuffisante. L'autorisation à fort impact devrait dépendre de preuves runtime disponibles :

- identité de charge liée aux attributs attendus
- empreinte déployée correspondant à un artefact signé approuvé
- provenance et émetteur vérifiés
- attestation runtime/matérielle fraîche et valide si requise
- politiques réseau/outils conformes au profil approuvé
- révocation et audit opérationnels

Classer les preuves comme vérifiées cryptographiquement, observées par fournisseur, attestées par opérateur, inférées ou inconnues. Une posture inconnue ne devient pas implicitement fiable.

<a id="network-controls"></a>
## Contrôles réseau

V1 utilise par défaut le mode hors ligne ou les endpoints locaux LocalStack. Le cloud réel est hors périmètre par défaut.

Les sondes visent par défaut seulement `offline://...`, `local://...`, `127.0.0.1`, `localhost` ou `localhost.localstack.cloud`. Les cibles HTTP(S) non locales exigent `--allow-live-cloud` explicite et l'approbation journalisée. Avec `run --policy-file`, `allowed_target_hosts` peut imposer un hôte exact ou suffixe `*.domain`. Les scénarios intégrés restent locaux/hors ligne jusqu'à un adaptateur réel ; ne pas annoncer une validation cloud réelle sans preuve de cible et d'événements.

<a id="secret-handling"></a>
## Secrets

- Secrets lus depuis l'environnement.
- `.env` et état Terraform ignorés.
- `.env.example` documente les noms, sans valeurs.
- Revue d'artefacts obligatoire avant étude publique, bundle support, capture ou archive de démo.
- `nullstate scrub` crée une copie expurgée avant upload, support ou publication.

<a id="container-security"></a>
## Sécurité des conteneurs

LocalStack et autres sandboxes sont des dépendances runtime, pas des binaires distribués dans le projet. Utiliser des images fiables et éviter le code rouge arbitraire hors workspaces générés.

<a id="red-team-command-execution"></a>
## Exécution des commandes rouges

L'exécuteur V1 est contraint par conception :

- Il exécute seulement `attack.py` généré.
- `attack.py` doit être directement dans le répertoire d'exécution.
- Si utilisé, `attack-manifest.json` doit aussi être directement dans ce répertoire.
- Lancement avec l'interpréteur Python courant, pas un shell arbitraire.
- Entrées dynamiques limitées à `--target-url`, `--stage` et chemin du manifeste généré.
- Journal : commande, stdout, stderr, code retour, URL, étape, début, fin, durée.
- Sondes autorisées par template, pas générées par le modèle à l'exécution.
- Timeouts courts et capture stdout/stderr bornée avant upload entreprise ou rétention longue.

Cela démontre des commandes réelles locales sans accès illimité du modèle aux outils.

Le durcissement entreprise devrait ajouter :

- politique explicite par couple scénario/backend
- liste d'hôtes autorisés pour adaptateurs cloud HTTP(S)
- assainissement à la publication avec règles organisationnelles
- gate `--allow-live-cloud`, désactivé par défaut

<a id="cicd-security"></a>
## Sécurité CI/CD

- PR : tests, lint, types et audit des dépendances.
- CodeQL sur PR, pushes et chaque semaine.
- Revue des dépendances sur PR.
- Publication déclenchée uniquement par tags semver et attestations GitHub des distributions et `sbom.spdx.json`.
- Workflows à privilèges minimaux.

<a id="data-protection"></a>
## Protection des données

Revoir avant publication. Ne pas publier tokens, vrais IDs tenant/abonnement, cartographies IP privées ou état cloud.

<a id="known-risks"></a>
## Risques connus

- Certains adaptateurs restent des ébauches.
- Azure LocalStack nécessite configuration externe et token.
- Les métriques hors ligne indiquent zéro token car aucun modèle n'est appelé.
- Scripts volontairement étroits ; les exploits plus riches restent autorisés explicitement et limités au sandbox.

<a id="future-improvements"></a>
## Améliorations futures

- SBOM enrichi à partir des lockfiles.
- Règles d'expurgation organisationnelles élargies.
- Garde-fous policy-as-code pour outils d'agents.
- Approbation cloud réelle avec intention opérateur auditable.
- Inventaire et contrôles spécifiques fournisseur pour identités IA, délégation, outils et confiance entre agents.
