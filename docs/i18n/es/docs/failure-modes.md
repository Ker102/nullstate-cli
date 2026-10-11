<a id="failure-modes"></a>
# Modos de fallo

<a id="localstack-azure-unavailable"></a>
## LocalStack Azure no disponible

Impacto: no se ejecuta sandbox en vivo.

Alternativa: `--offline` o `--target plan-only`.

<a id="missing-docker"></a>
## Docker ausente

Impacto: no arrancan sandboxes ejecutables.

Alternativa: solo plan sigue analizando IaC y generando informes.

<a id="missing-model-endpoint"></a>
## Endpoint de modelo ausente

Impacto: no hay llamadas reales rojo/azul.

Alternativa: agentes mock offline conservan demo completa.

<a id="unknown-model-provider"></a>
## Proveedor desconocido

Impacto: no puede deducir URL compatible.

Alternativa: `NULLSTATE_LLM_PROVIDER` en `custom`, `google` o `claude`; para modelos propios configure también `NULLSTATE_LLM_BASE_URL` o URLs por rol.

<a id="terraform-provider-mismatch"></a>
## Proveedor Terraform incompatible

Impacto: `terraform init` o `plan` puede fallar.

Alternativa: parser offline sirve para fixture.

<a id="model-output-is-wrong"></a>
## Modelo incorrecto

Impacto: explicación/remediación engañosa.

Control: detector y remediación deterministas son verdad V1.

<a id="report-includes-sensitive-data"></a>
## Informe sensible

Impacto: caso público filtra información.

Control: revise antes de publicar; ejecute `nullstate scrub` y revise `scrub-report.json`.
