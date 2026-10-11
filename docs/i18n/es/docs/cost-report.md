<a id="cost-report"></a>
# Informe de costes

<a id="summary"></a>
## Resumen

V1 busca coste de nube cercano a cero por defecto. Offline es local; LocalStack es Docker del operador; AMD se limita a evidencia de modelos del hackathon.

<a id="cost-items"></a>
## Partidas

| Partida | Coste previsto | Notas |
|---|---:|---|
| CLI nullstate | 0 | paquete Python local |
| Demo offline | 0 | sin nube ni endpoint modelo |
| LocalStack Azure | depende del acceso | requiere token |
| AMD Developer Cloud | créditos hackathon | endpoint MI300X |
| Fireworks | según proveedor | alternativa si GPU se retrasa |
| GitHub Actions | depende de nivel gratuito/bajo | pruebas ligeras |

<a id="controls"></a>
## Controles

- Sin Azure real por defecto.
- CLI no crea recursos cloud persistentes.
- Detener sandboxes con `nullstate sandbox down`.

<a id="future-tracking"></a>
## Seguimiento futuro

Registre duración real de servicio de modelos, horas GPU y costes LocalStack/nube antes de publicar.

Registre si cada demo fue offline, inferencia administrada o GPU AMD. Mantiene honestidad si usa fallback antes del acceso DigitalOcean/AMD.
