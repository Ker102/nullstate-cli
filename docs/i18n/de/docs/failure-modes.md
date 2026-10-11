<a id="failure-modes"></a>
# Fehlermodi

<a id="localstack-azure-unavailable"></a>
## LocalStack Azure fehlt

Auswirkung: keine Live-Ausführung.

Fallback: `--offline` oder `--target plan-only`.

<a id="missing-docker"></a>
## Docker fehlt

Auswirkung: Sandboxes starten nicht.

Fallback: Plan-only parst und berichtet.

<a id="missing-model-endpoint"></a>
## Modell fehlt

Auswirkung: keine echten Red-/Blue-Aufrufe.

Fallback: Offline-Mocks erhalten den Ablauf.

<a id="unknown-model-provider"></a>
## Unbekannter Provider

Auswirkung: kompatible URL nicht ableitbar.

Fallback: `NULLSTATE_LLM_PROVIDER` auf `custom`, `google`, `claude`; bei eigenen Modellen `NULLSTATE_LLM_BASE_URL` oder Rollen-URLs.

<a id="terraform-provider-mismatch"></a>
## Terraform-Mismatch

Auswirkung: `terraform init` oder `plan` scheitert.

Fallback: statischer Fixture-Parser.

<a id="model-output-is-wrong"></a>
## Modellfehler

Auswirkung: irreführende Erklärung/Abhilfe.

Kontrolle: deterministischer Detektor und Abhilfe maßgeblich für V1.

<a id="report-includes-sensitive-data"></a>
## Sensibler Bericht

Auswirkung: öffentliche Datenleckage.

Kontrolle: prüfen; `nullstate scrub` und `scrub-report.json`.
