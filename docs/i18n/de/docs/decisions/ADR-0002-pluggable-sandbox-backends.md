<a id="adr-0002-pluggable-sandbox-backends"></a>
# ADR-0002: Austauschbare Sandbox-Backends

<a id="status"></a>
## Status

Angenommen.

<a id="context"></a>
## Kontext

Künftig Cloud-IaC, Kubernetes, Compose, On-Premises unterstützen.

<a id="decision"></a>
## Entscheidung

Adapterregistry mit drei Modi:

- ausführbare Sandbox
- digitaler Zwilling
- Plan-only-Analyse

<a id="consequences"></a>
## Folgen

- V1 mit starkem Ziel und sichtbarer künftiger Verfügbarkeit.
- On-Premises ohne behauptete perfekte Emulatoren.
- Einige Backends zunächst dokumentierte Gerüste, keine Voll-Exploits.
