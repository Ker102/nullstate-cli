<a id="cost-report"></a>
# Rapport de coûts

<a id="summary"></a>
## Résumé

V1 vise quasi-zéro coût cloud par défaut. Offline local ; LocalStack dans Docker opérateur ; AMD limité aux preuves modèle hackathon.

<a id="cost-items"></a>
## Postes

| Poste | Coût prévu | Notes |
|---|---:|---|
| CLI nullstate | 0 | Python local |
| Démo offline | 0 | aucun cloud/modèle |
| LocalStack Azure | selon accès | token requis |
| AMD Developer Cloud | crédits hackathon | endpoint MI300X |
| Fireworks | selon fournisseur | repli si GPU retardé |
| GitHub Actions | selon gratuit/faible coût | tests légers |

<a id="controls"></a>
## Contrôles

- Pas d'Azure réel par défaut.
- CLI ne crée pas de ressources cloud durables.
- Arrêt local par `nullstate sandbox down`.

<a id="future-tracking"></a>
## Suivi futur

Consigner temps réel de serving, heures GPU et coûts LocalStack/cloud avant publication.

Consigner offline, inférence managée ou AMD par run pour rester exact si fallback avant accès DigitalOcean/AMD.
