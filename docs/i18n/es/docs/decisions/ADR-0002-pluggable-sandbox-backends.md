<a id="adr-0002-pluggable-sandbox-backends"></a>
# ADR-0002: Backends de sandbox conectables

<a id="status"></a>
## Estado

Aceptado.

<a id="context"></a>
## Contexto

nullstate debe soportar con el tiempo IaC de nube, Kubernetes, Compose y configuraciones on-prem.

<a id="decision"></a>
## Decisión

Registro de adaptadores con tres modos:

- sandbox ejecutable
- sandbox gemelo digital
- análisis solo plan

<a id="consequences"></a>
## Consecuencias

- V1 entrega un objetivo ejecutable sólido y muestra disponibilidad futura.
- Modela on-prem sin fingir emuladores perfectos para todos.
- Algunos backends comienzan como esqueletos documentados, no exploits completos.
