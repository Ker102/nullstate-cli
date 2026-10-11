<a id="adr-0003-localstack-azure-for-v1"></a>
# ADR-0003: LocalStack Azure para V1

<a id="status"></a>
## Status

Aceito.

<a id="context"></a>
## Contexto

Primeira demo Terraform Azure. Azure real aumenta riscos de credenciais, custo, limpeza, segurança.

<a id="decision"></a>
## Decisão

LocalStack Azure primeiro executável, plano como fallback.

<a id="consequences"></a>
## Consequências

- Demo sem recursos Azure reais.
- Docker e `LOCALSTACK_AUTH_TOKEN` para execução ao vivo.
- Distinguir integração de incluir LocalStack no repo.
