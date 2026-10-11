<a id="failure-modes"></a>
# Modes de défaillance

<a id="localstack-azure-unavailable"></a>
## LocalStack Azure indisponible

Impact : pas d'exécution directe.

Repli : `--offline` ou `--target plan-only`.

<a id="missing-docker"></a>
## Docker absent

Impact : pas de démarrage des sandboxes.

Repli : plan seul parse et rapporte.

<a id="missing-model-endpoint"></a>
## Endpoint modèle absent

Impact : pas d'appels rouge/bleu réels.

Repli : agents simulés offline gardent la démo.

<a id="unknown-model-provider"></a>
## Fournisseur inconnu

Impact : URL compatible non déductible.

Repli : `NULLSTATE_LLM_PROVIDER` en `custom`, `google`, `claude` ; pour autohébergé ajouter `NULLSTATE_LLM_BASE_URL` ou URL par rôle.

<a id="terraform-provider-mismatch"></a>
## Provider Terraform incompatible

Impact : `terraform init` ou `plan` échoue.

Repli : parseur statique pour fixture.

<a id="model-output-is-wrong"></a>
## Modèle incorrect

Impact : explication/correction trompeuse.

Contrôle : détecteur/correction déterministes font autorité V1.

<a id="report-includes-sensitive-data"></a>
## Rapport sensible

Impact : fuite dans étude publique.

Contrôle : revoir ; lancer `nullstate scrub`, lire `scrub-report.json`.
