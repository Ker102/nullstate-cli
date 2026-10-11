<a id="cost-report"></a>
# Kostenbericht

<a id="summary"></a>
## Zusammenfassung

V1 zielt standardmäßig auf fast null Cloudkosten. Offline lokal, LocalStack im Betreiber-Docker, AMD nur für Hackathon-Serving-Evidenz.

<a id="cost-items"></a>
## Posten

| Posten | Erwartete Kosten | Hinweise |
|---|---:|---|
| CLI | 0 | lokales Python |
| Offline-Demo | 0 | keine Cloud/Modelle |
| LocalStack Azure | zugangsabhängig | Token nötig |
| AMD Developer Cloud | Hackathoncredits | MI300X |
| Fireworks | providerabhängig | GPU-Fallback |
| GitHub Actions | tarifabhängig niedrig/gratis | leichte Tests |

<a id="controls"></a>
## Kontrollen

- Keine echte Azure-Ausführung standardmäßig.
- Keine langfristigen Cloud-Ressourcen durch CLI.
- Lokal stoppen mit `nullstate sandbox down`.

<a id="future-tracking"></a>
## Künftige Erfassung

Tatsächliche Serving-Dauer, GPU-Stunden, LocalStack-/Cloudkosten vor Veröffentlichung erfassen.

Pro Run Offline, Managed oder AMD markieren, damit Fallback vor Zugang nicht falsch dargestellt wird.
