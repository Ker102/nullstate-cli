<a id="product-and-validation-model"></a>
# Modèle de produit et de validation

<a id="product-purpose"></a>
## Objectif du produit

Nullstate est une plateforme de validation des chemins d'attaque cloud fondée sur des preuves. Elle corrèle l'infrastructure en tant que code avec l'état observé d'AWS et d'Azure, raisonne sur les relations entre réseau, identités, services et données, valide des chemins d'attaque sélectionnés dans des environnements contrôlés, applique des corrections et rejoue l'attaque.

Le produit n'a pas vocation à exiger une représentation Terraform parfaite de l'intégralité d'un compte cloud. L'IaC décrit la configuration prévue et gérée, tandis que la découverte en lecture seule décrit la réalité déployée. Nullstate devrait combiner les deux dans un graphe d'environnement normalisé et conserver la source et le niveau de confiance de chaque relation.

Le produit open source devrait d'abord servir de framework local de validation DevSecOps pour les humains, les jobs CI et les agents de programmation. `nullstate summary --json` fournit aux agents un résultat d'exécution compact au lieu de les obliger à analyser des rapports Markdown, tandis que `nullstate context validate` et `nullstate context summary --json` définissent un contrat de contexte cloud sûr et en lecture seule avant l'ajout de collecteurs en direct.

<a id="environment-graph"></a>
## Graphe d'environnement

Le graphe d'environnement devrait accepter :

- Terraform, CloudFormation, les exports CDK, Bicep, ARM et les données de plan/d'état des fournisseurs.
- Les inventaires de ressources AWS et Azure en lecture seule.
- Les rôles IAM, les attributions Azure RBAC, les identités managées, les relations de confiance et les identités de charges de travail.
- Les identités d'agents IA, les modèles d'identité d'agent, les identités de charges de travail d'agents, le contexte utilisateur délégué, les identités d'outils et les relations avec les informations d'authentification en aval.
- Les endpoints publics, les réseaux virtuels, les groupes de sécurité, les NSG, les routes, les passerelles, les endpoints privés et les interconnexions de peering.
- La configuration du stockage, des bases de données, de la gestion des secrets, du calcul, du serverless, des conteneurs et de Kubernetes.
- Les constats de sécurité natifs, les journaux d'activité, de flux et d'audit, ainsi que certaines métadonnées runtime.
- Une classification facultative des données fournie par l'utilisateur ou inférée à partir de métadonnées sûres et de jeux de test synthétiques.

Le graphe n'a pas besoin de cloner chaque ressource. Il doit identifier les chemins pertinents pour la sécurité et créer un jumeau minimal du chemin d'attaque contenant uniquement les relations nécessaires pour tester une hypothèse.

L'aperçu actuel du manifeste de contexte est intentionnellement limité au local :

```bash
nullstate context validate examples/cloud-context/aws-readonly-context.json
nullstate context summary examples/cloud-context/aws-readonly-context.json --json
```

Il valide la structure des métadonnées de fournisseur, de compte, d'identité, de ressource, d'exposition publique et de classification des données sans demander d'informations d'authentification cloud. Les futurs collecteurs devraient produire des données conformes à ce contrat à l'aide d'identités cloud en lecture seule et de courte durée.

<a id="evaluation-and-product-metrics"></a>
## Évaluation et métriques du produit

La valeur de Nullstate pour les études de cas devrait être mesurée, et pas seulement décrite. Le dispositif d'évaluation actuel commence par des benchmarks internes reproductibles :

```bash
nullstate eval run examples/eval/iac-security-regression.json --output-dir eval-runs/iac-security-regression
```

Le dispositif enregistre la durée, le nombre de constats, la gravité maximale, l'état de l'attaque avant/après, les totaux de tokens, le nombre d'artefacts et le statut de réussite/échec des attentes. C'est la première étape vers une comparaison de Nullstate avec une revue reposant uniquement sur des scanners, une revue manuelle et une revue par un agent de programmation générique. Tant que ces références n'existent pas, les affirmations devraient se limiter au comportement mesuré de Nullstate plutôt qu'à des déclarations générales de précision ou de gain de temps.

<a id="identity-aware-attack-analysis"></a>
## Analyse des attaques tenant compte des identités

Un port ouvert ou un conteneur public ne constitue pas l'ensemble du constat. Nullstate devrait évaluer ce que chaque perspective d'attaquant autorisée peut atteindre :

| Perspective | Exemple |
|---|---|
| Externe | Client internet anonyme |
| Utilisateur du tenant | Utilisateur cloud authentifié mais peu privilégié |
| Développeur | Identité humaine disposant de permissions de déploiement ou de lecture |
| Charge de travail CI | Identité GitHub Actions, GitLab ou d'un système de build |
| Charge de travail compromise | Identité de VM, de conteneur, de fonction ou d'application |
| Rôle cloud | Rôle AWS IAM, principal de service Azure ou identité managée |
| Agent IA | Identité dédiée d'agent, identité de charge de travail d'agent ou rôle runtime d'agent |
| Agent délégué | Agent agissant avec une autorité propagée depuis un utilisateur humain |
| Acteur latéral | Principal obtenu lors d'une étape antérieure du chemin d'attaque |

Chaque résultat observé devrait consigner le principal, les permissions supposées, la méthode d'authentification, la cible, les données ou la capacité atteintes, les preuves issues des commandes et le niveau de confiance.

<a id="ai-agents-as-cloud-principals"></a>
## Les agents IA comme principaux cloud

Les agents IA interagissent de plus en plus avec l'infrastructure, les API cloud, les services internes, les magasins de données, les systèmes de tickets, les dépôts de code source et les outils de déploiement. Ils peuvent fonctionner au moyen :

- d'une identité dédiée créée spécifiquement pour l'agent
- d'un principal de service classique, d'une identité managée, d'un rôle IAM ou d'une identité de charge de travail
- d'une identité runtime ou d'outil partagée par plusieurs agents
- d'une autorité déléguée propagée depuis un utilisateur humain
- d'informations d'authentification acquises pour des outils en aval ou des services tiers

Ces modes ne doivent pas être fusionnés en un seul compte de service générique. Nullstate devrait représenter l'agent, le runtime, l'outil, l'utilisateur délégué, les informations d'authentification et le service cible comme des nœuds distincts du graphe. Cela conserve qui a initié une action, les permissions de qui l'ont autorisée et quel composant pourrait être compromis.

Les chemins d'attaque propres aux agents comprennent :

- une injection de prompt conduisant l'agent à faire un mauvais usage de permissions cloud légitimes
- des outils, plugins, serveurs MCP, mémoires ou contenus récupérés compromis influençant les actions
- une autonomie excessive permettant des opérations destructrices ou modifiant les privilèges en dehors de la tâche prévue
- un chemin de mandataire confus où un utilisateur non fiable amène un agent privilégié à agir en son nom
- une autorité utilisateur déléguée permettant d'atteindre des ressources auxquelles l'identité propre de l'agent ne pourrait pas accéder
- des identités runtime partagées rendant inefficaces l'attribution et le moindre privilège
- une confiance entre agents permettant le mouvement latéral
- des informations d'authentification en aval de longue durée ou de portée étendue augmentant le rayon d'impact

Nullstate devrait évaluer au moins trois vues de permissions distinctes :

1. **Permissions natives de l'agent :** ressources accessibles avec l'identité propre de l'agent.
2. **Permissions déléguées :** ressources accessibles en agissant au nom d'un utilisateur ou d'une catégorie d'utilisateurs spécifique.
3. **Permissions de la chaîne d'outils :** ressources accessibles par les identités runtime, plugins, passerelles, connecteurs et informations d'authentification en aval.

Le rapport devrait expliquer la chaîne de permissions effective et identifier les données et opérations exposées si l'agent, ses instructions, sa mémoire ou l'un de ses outils est compromis. Une validation sûre devrait utiliser des prompts synthétiques, des données synthétiques, des outils contrôlés et des environnements jetables, plutôt que de tenter des injections de prompt incontrôlées contre des agents de production.

Pour les agents hébergés à l'extérieur, l'analyse des identités seule est insuffisante. Nullstate devrait également évaluer la posture runtime : liaison entre charge de travail et identité, provenance des artefacts, empreinte de déploiement, intégrité de l'hôte et du runtime, exposition réseau, contrôles des outils, journalisation, révocation, ainsi que fraîcheur et solidité des preuves à l'appui. La conception détaillée figure dans [Confiance des agents externes et posture runtime](plans/2026-06-22-external-agent-trust-design.md).

La CLI actuelle inclut un premier aperçu déterministe de ce modèle :

```bash
nullstate agent posture verify examples/agent-trust/external-agent-manifest.json
nullstate agent blast-radius examples/agent-trust/external-agent-manifest.json
```

Ces commandes opèrent sur un manifeste local, et non sur des collecteurs de fournisseurs en direct. Elles visent d'abord à renforcer le contrat de données : les preuves de posture manquantes, périmées ou inconnues doivent rester visibles, et l'autorité utilisateur déléguée doit être séparée de l'identité propre de l'agent.

<a id="exposed-data-and-impact"></a>
## Données exposées et impact

Les administrateurs cloud peuvent accepter intentionnellement un service accessible parce qu'ils pensent qu'il ne contient rien de critique. Nullstate devrait néanmoins identifier si le chemin expose :

- des noms d'objets, listes de répertoires, ID de comptes, ID de tenants, noms d'hôtes ou une topologie interne
- des journaux d'application, sauvegardes, diagnostics, artefacts de build, source maps ou paquets de déploiement
- des informations d'authentification, tokens, chaînes de connexion, configurations ou références à des secrets
- des données personnelles, financières, réglementées, de clients ou propriétaires
- des capacités d'écriture, de suppression, d'usurpation d'identité, d'exécution ou de modification de politiques
- des informations permettant des attaques contre les informations d'authentification, du mouvement latéral, de l'élévation de privilèges ou de l'ingénierie sociale ciblée

Les rapports doivent distinguer :

- la configuration suggère une exposition
- des métadonnées sûres ont été observées
- des données de preuve synthétiques ont été récupérées
- une capacité privilégiée a été démontrée
- le contenu sensible de production n'a volontairement pas été consulté

<a id="why-not-attack-production-directly"></a>
## Pourquoi ne pas attaquer directement la production ?

La découverte en lecture seule et une validation non destructrice dont l'approbation est strictement délimitée peuvent s'exécuter contre la production. L'exploitation autonome devrait se faire par défaut dans un environnement contrôlé, car :

1. Les exploits peuvent modifier, supprimer, corrompre ou exposer des données réelles.
2. Les sondes peuvent provoquer une limitation de débit, des interruptions, des verrouillages de comptes, une mise en quarantaine ou l'activation de la réponse aux incidents.
3. Les tests IAM peuvent créer des informations d'authentification persistantes, des relations de confiance ou des changements de privilèges.
4. Les tests d'exfiltration peuvent enfreindre des exigences de confidentialité, contractuelles, réglementaires et de résidence des données.
5. Les dépendances de production peuvent affecter des clients et des tiers hors du périmètre approuvé.
6. Le nettoyage ne peut pas garantir la restauration exacte de l'état précédent.
7. La validation CI répétée doit être déterministe et suffisamment sûre pour s'exécuter sans qu'un spécialiste des tests d'intrusion supervise chaque exécution.

Le modèle d'exploitation sûr est le suivant :

1. Découvrir la production au moyen d'API de fournisseurs en lecture seule.
2. Construire et classer les hypothèses d'attaque.
3. Exécuter des vérifications non destructrices inscrites sur une liste d'autorisation contre la production uniquement lorsque la politique le permet.
4. Reconstruire le chemin pertinent minimal avec des données synthétiques dans un environnement jetable.
5. Exécuter des attaques contraintes contre cet environnement.
6. Appliquer une correction et rejouer la même attaque.
7. Conserver les preuves et convertir le chemin démontré en test de régression.

<a id="aws-and-azure-first"></a>
## AWS et Azure en premier

AWS et Azure devraient être les premiers fournisseurs cloud, car ils couvrent une grande part de l'infrastructure d'entreprise et disposent tous deux d'écosystèmes IaC matures. Terraform reste une entrée de premier ordre, pas une cible concurrente : Terraform pour AWS et Terraform pour Azure fournissent la topologie et la configuration prévues, tandis que la découverte auprès du fournisseur fournit l'état en direct et la dérive non gérée.

Les adaptateurs de fournisseurs devraient également inventorier les nouveaux systèmes d'identité d'agent. Microsoft Entra Agent ID fournit des identités d'agent spécialisées et des modèles d'identité, tandis qu'Amazon Bedrock AgentCore Identity représente les agents par des mécanismes d'identité d'agent/de charge de travail. Nullstate devrait ingérer ces relations aux côtés des principaux de service classiques, des identités managées et des rôles IAM, sans supposer que chaque organisation utilise une plateforme d'agents native du fournisseur.

La précision par rapport aux fournisseurs devrait être graduée et explicite :

| Niveau | Source de preuve | Objectif |
|---|---|---|
| Statique | IaC, plans, politiques et configuration exportée | Analyse rapide avant déploiement |
| Observé | Inventaire et journaux du fournisseur en lecture seule | Comprendre l'état réellement déployé |
| Émulé | LocalStack, émulateurs de services, conteneurs ou jumeaux numériques | Validation sûre et reproductible avec des limites de fidélité connues |
| Sandbox réel | Compte AWS ou abonnement Azure jetable | Validation d'exploits avec la plus haute fidélité |

Chaque rapport devrait préciser le niveau utilisé. Les preuves issues d'un émulateur ne doivent jamais être présentées comme démontrant un comportement identique du fournisseur.

<a id="ci-cloud-event-and-scheduled-execution"></a>
## Exécution CI, sur événements cloud et planifiée

Nullstate devrait prendre en charge trois déclencheurs complémentaires.

<a id="pull-request-and-iac-ci"></a>
### CI des pull requests et de l'IaC

Déclencher lorsque des fichiers Terraform, CloudFormation, Bicep, Helm, de politique ou d'infrastructure associés changent.

Le pipeline :

1. Analyser la configuration proposée avant le déploiement.
2. Comparer les constats à une référence approuvée.
3. Créer facultativement un environnement de validation jetable pour les changements à haut risque.
4. Exécuter les tests de régression des chemins d'attaque sélectionnés.
5. Exporter SARIF, un résultat de politique lisible par machine et des artefacts de preuve.
6. Bloquer la fusion lorsque les seuils de la politique ne sont pas respectés.

C'est la boucle de retour la plus rapide, qui empêche les configurations vulnérables d'atteindre le cloud.

<a id="post-deployment-validation"></a>
### Validation après déploiement

Déclencher après la réussite d'un workflow de déploiement ou après un événement du fournisseur.

Les exemples comprennent un job Terraform apply, un déploiement CloudFormation, un déploiement Azure ou un événement cloud indiquant un changement de ressource ou de politique pertinent pour la sécurité. Nullstate actualise le graphe d'environnement observé, recherche les dérives et n'exécute que les validations sûres concernées. La validation potentiellement destructrice est dirigée vers un sandbox jetable plutôt que vers l'environnement de production mis à jour.

<a id="scheduled-assurance"></a>
### Assurance planifiée

Exécuter toutes les heures, tous les jours ou toutes les semaines pour détecter les changements manuels dans la console, les ressources non gérées, la dérive des permissions, les endpoints nouvellement publics, les risques acceptés devenus obsolètes et les chemins d'attaque créés par des changements en dehors de Git.

Ces modes résolvent des problèmes différents :

- La CI des PR valide le changement prévu avant déploiement.
- La validation après déploiement confirme que l'état observé correspond aux attentes.
- L'assurance planifiée détecte la dérive et les changements hors des circuits habituels.

La plateforme payante mature peut coordonner les trois, conserver l'historique, notifier les équipes et fournir une inférence de modèles managée. La CLI open source conserve la capacité de s'exécuter localement et en CI avec les informations d'authentification et les endpoints de modèles fournis par le client.

<a id="provider-references"></a>
## Références des fournisseurs

- [Microsoft Entra Agent ID](https://learn.microsoft.com/en-us/entra/agent-id/)
- [Concepts d'identité d'agent dans Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-identity)
- [Amazon Bedrock AgentCore Identity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity-overview.html)
- [Recommandations AWS sur l'identité d'agent et la gestion des permissions](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentsec03.html)
