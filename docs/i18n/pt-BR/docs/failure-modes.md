<a id="failure-modes"></a>
# Modos de falha

<a id="localstack-azure-unavailable"></a>
## Azure LocalStack indisponível

Impacto: não executa sandbox ao vivo.

Fallback: `--offline` ou `--target plan-only`.

<a id="missing-docker"></a>
## Docker ausente

Impacto: sandbox não inicia.

Fallback: plano ainda analisa e relata.

<a id="missing-model-endpoint"></a>
## Modelo ausente

Impacto: nenhuma chamada real.

Fallback: mock offline preserva demo.

<a id="unknown-model-provider"></a>
## Provider desconhecido

Impacto: URL compatível não inferida.

Fallback: `NULLSTATE_LLM_PROVIDER` em `custom`, `google`, `claude`; modelos próprios também `NULLSTATE_LLM_BASE_URL` ou URLs por papel.

<a id="terraform-provider-mismatch"></a>
## Terraform incompatível

Impacto: `terraform init` ou `plan` falha.

Fallback: parser estático do fixture.

<a id="model-output-is-wrong"></a>
## Modelo errado

Impacto: explicação/correção enganosa.

Controle: detector/correção determinísticos são verdade V1.

<a id="report-includes-sensitive-data"></a>
## Relatório sensível

Impacto: estudo público vaza dados.

Controle: revise, execute `nullstate scrub`, leia `scrub-report.json`.
