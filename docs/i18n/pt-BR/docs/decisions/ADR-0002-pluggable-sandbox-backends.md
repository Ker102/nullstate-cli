<a id="adr-0002-pluggable-sandbox-backends"></a>
# ADR-0002: Backends plugáveis

<a id="status"></a>
## Status

Aceito.

<a id="context"></a>
## Contexto

Suportar progressivamente cloud IaC, Kubernetes, Compose, on-premises.

<a id="decision"></a>
## Decisão

Registro de adaptadores em três modos:

- sandbox executável
- gêmeo digital
- análise somente plano

<a id="consequences"></a>
## Consequências

- V1 entrega alvo forte e expõe futuros backends.
- Modela on-premises sem fingir emuladores perfeitos.
- Alguns começam como esqueletos documentados, não exploit completo.
