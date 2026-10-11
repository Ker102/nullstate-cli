<a id="threat-model---nullstate"></a>
# Modèle de menace - nullstate

<a id="system-overview"></a>
## Vue d'ensemble

nullstate est une CLI locale qui analyse l'IaC, exécute/simule des attaques sandbox, utilise des rôles rouge/bleu, corrige dans une copie et produit des preuves.

<a id="assets"></a>
## Actifs

| Actif | Importance | Sensibilité |
|---|---|---|
| Source IaC | architecture et secrets possibles | moyenne/élevée |
| Workspace | IaC copié et correction | moyenne |
| Clé API modèle | accès à l'endpoint | élevée |
| Token LocalStack | accès à l'image Azure | élevée |
| Rapports | preuves publiques | faible/moyenne après assainissement |
| Graphe identité/délégation | permissions, délégation, outils et systèmes accessibles | élevée |
| Mémoire/configuration outils | instructions, identifiants, données récupérées et intégrations fiables possibles | élevée |

<a id="trust-boundaries"></a>
## Frontières

- Shell utilisateur vers CLI.
- CLI vers Docker/LocalStack/kind.
- CLI vers endpoint modèle.
- Agent IA vers fournisseur d'identité, gateway, service aval et contexte délégué.
- Script généré vers répertoire local.
- Documentation vers internet public.

<a id="actors"></a>
## Acteurs

| Acteur | Objectif | Confiance |
|---|---|---|
| Opérateur | valider l'IaC local | fiable |
| Attaquant externe | abuser des artefacts ou sandbox exposé | non fiable |
| Agent rouge | trouver un chemin sandbox | partielle |
| Agent bleu | générer la correction | partielle |
| Agent IA client | utiliser les ressources avec identité propre/déléguée | partielle |
| Outil/mémoire compromis | influencer ou abuser de l'autorité | non fiable |
| Dépendance compromise | exécuter du code malveillant | non fiable |

<a id="threats"></a>
## Menaces

| Menace | Impact | Probabilité | Contrôle | Preuve |
|---|---|---|---|---|
| Cible cloud réelle touchée accidentellement | Élevé | Moyenne | LocalStack/plan seul par défaut | docs CLI |
| Secret commité | Élevé | Moyenne | `.gitignore`, `.env.example`, SECURITY.md | fichiers repo |
| Agent sort du sandbox | Élevé | Moyenne | commandes autorisées, copie workspace | module sandbox |
| Dépendance compromise | Élevé | Moyenne | Dependabot, pip-audit, revue | workflows |
| Sortie modèle trompeuse | Moyen | Élevée | détecteur/validateur déterministes | tests |
| Agent compromis abuse du cloud | Élevé | Moyenne | graphe identité, moindre privilège, délégation séparée, validation contrôlée | futur adaptateur identité |
| Agent privilégié devient mandataire confus | Élevé | Moyenne | attribution appelant/délégation, politique, autorisation par outil | futur adaptateur identité |
| Identité partagée masque l'attribution | Élevé | Moyenne | preuves distinctes agent/runtime/outil si possibles | futur inventaire |
| Hôte externe compromis avec identité tenant valide | Élevé | Moyenne | posture, fédération courte, gateway, moindre privilège, révocation | futur collecteur |
| Posture falsifiée/périmée acceptée | Élevé | Moyenne | signature, émetteur, timestamps, fraîcheur, refus à fort impact en cas d'échec | futur vérificateur |

<a id="abuse-cases"></a>
## Cas d'abus

- Utilisateur visant accidentellement un état Terraform de production.
- Dépendance lisant l'environnement pendant CI.
- Rapport contenant token réel ou endpoint privé.
- Agent rouge proposant des actions hors LocalStack.
- Conteneur exposant un port imprévu.
- Injection de prompt faisant appeler un outil légitime avec paramètres dangereux.
- Agent pour utilisateur peu privilégié conservant/acquérant des permissions de principal de service plus larges.
- MCP, connecteur, plugin, mémoire ou document compromis redirigeant les actions.
- Plusieurs agents partageant une identité privilégiée et masquant l'auteur.
- Identifiant aval de portée/durée supérieure à la tâche.
- Agent tiers utilisant malicieusement une identité valide depuis un hôte vulnérable.
- Opérateur prenant une signature d'image/attestation matérielle pour garantie de toute l'application.

<a id="residual-risks"></a>
## Risques résiduels

- Docker local dépend de la machine opérateur.
- Couverture Azure LocalStack différente du cloud réel possible.
- Protection des branches non imposable avant configuration GitHub.
- Identités natives et délégation évoluent et nécessitent inventaire/preuves spécifiques.

<a id="next-improvements"></a>
## Prochaines améliorations

- Validation Azure LocalStack en direct après habilitation Azure Emulator.
- Adaptateurs cloud uniquement avec listes fournisseur et approbation.
- Inventaire AWS/Azure des agents natifs, charges classiques, délégations, outils et identifiants aval.
- Preuves externes explicitement vérifiées, observées, attestées par opérateur, inférées ou inconnues.
