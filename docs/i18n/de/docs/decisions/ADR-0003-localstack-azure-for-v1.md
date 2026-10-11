<a id="adr-0003-localstack-azure-for-v1"></a>
# ADR-0003: LocalStack Azure für V1

<a id="status"></a>
## Status

Angenommen.

<a id="context"></a>
## Kontext

Erste Demo Terraform Azure; echtes Azure erhöht Credentials-, Kosten-, Cleanup-, Sicherheitsrisiken.

<a id="decision"></a>
## Entscheidung

Erstes ausführbares Backend LocalStack Azure, Plan-only-Fallback.

<a id="consequences"></a>
## Folgen

- Demo ohne echte Azure-Ressourcen.
- Docker und `LOCALSTACK_AUTH_TOKEN` weiterhin für Live-Ausführung.
- Integration klar von mitgeliefertem LocalStack trennen.
