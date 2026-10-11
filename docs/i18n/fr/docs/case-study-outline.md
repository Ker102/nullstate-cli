<a id="case-study-outline"></a>
# Plan d'étude de cas

<a id="problem"></a>
## Problème

Les équipes cloud livrent Terraform plus vite que la validation continue d'exploitabilité. Les scanners montrent un risque possible, pas l'utilisation réelle ni le blocage après correction.

<a id="solution"></a>
## Solution

`nullstate` exécute une boucle purple-team locale Terraform :

- Analyser l'infrastructure prévue.
- Tenter l'exploitation rouge.
- Générer la correction bleue.
- Revalider après patch.
- Produire les preuves.

<a id="demo-scenario"></a>
## Démo

Chemin validé : fixture S3 public LocalStack, `nullstate` détecte, sonde en lecture anonyme contrainte, patche et vérifie le blocage. Azure Blob suit la même logique déterministe, mais attend habilitation ou repli stockage Azurite.

<a id="why-amd-mi300x"></a>
## Pourquoi AMD MI300X

Architecture à contexte long : plans JSON, logs, sorties et diffs envoyés localement sans latence API externe ni exposition des données.

<a id="next-steps"></a>
## Suite

- Règles Azure : clés partagées, réseau public, Key Vault public.
- Résoudre accès LocalStack Azure ou ajouter Azurite.
- Adaptateurs Kubernetes/Compose/sur site directs avec mêmes artefacts.
- Preuves GPU AMD avec vLLM `/metrics` et `amd-smi` ou `rocm-smi`.
