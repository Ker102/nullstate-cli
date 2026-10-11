<a id="adr-0003-localstack-azure-for-v1"></a>
# ADR-0003 : LocalStack Azure pour V1

<a id="status"></a>
## État

Accepté.

<a id="context"></a>
## Contexte

Première cible Terraform Azure. Azure réel accroît risques d'identifiants, coûts, nettoyage, sécurité.

<a id="decision"></a>
## Décision

LocalStack Azure premier backend exécutable, plan seul en repli.

<a id="consequences"></a>
## Conséquences

- Démo sans ressources Azure réelles.
- Docker et `LOCALSTACK_AUTH_TOKEN` requis en direct.
- Distinguer intégration LocalStack de distribution de ses binaires.
