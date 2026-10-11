<a id="adr-0002-pluggable-sandbox-backends"></a>
# ADR-0002 : Backends de sandbox modulaires

<a id="status"></a>
## État

Accepté.

<a id="context"></a>
## Contexte

Support progressif d'IaC cloud, Kubernetes, Compose et configurations sur site.

<a id="decision"></a>
## Décision

Registre d'adaptateurs avec trois modes :

- sandbox exécutable
- sandbox jumeau numérique
- analyse de plans seuls

<a id="consequences"></a>
## Conséquences

- V1 peut livrer une cible solide et montrer les futurs backends.
- Modéliser le sur site sans prétendre à un émulateur parfait pour chaque provider.
- Certains backends commencent comme ébauches documentées, sans exploitation complète.
