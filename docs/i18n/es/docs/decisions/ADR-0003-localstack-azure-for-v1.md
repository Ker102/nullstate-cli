<a id="adr-0003-localstack-azure-for-v1"></a>
# ADR-0003: LocalStack Azure para V1

<a id="status"></a>
## Estado

Aceptado.

<a id="context"></a>
## Contexto

Primera demo Terraform Azure. Azure real aumenta riesgos de credenciales, coste, limpieza y seguridad.

<a id="decision"></a>
## Decisión

Primer backend ejecutable LocalStack Azure con fallback solo plan.

<a id="consequences"></a>
## Consecuencias

- Demo sin recursos Azure reales.
- Docker y `LOCALSTACK_AUTH_TOKEN` siguen necesarios para Azure LocalStack en vivo.
- Distinguir integración LocalStack de incluir sus binarios.
