<a id="case-study-outline"></a>
# Esquema de caso de estudio

<a id="problem"></a>
## Problema

Los equipos de nube entregan Terraform más rápido de lo que seguridad puede validar continuamente su explotabilidad. Los scanners estáticos muestran riesgo potencial, no prueban que un atacante pueda aprovecharlo o que el parche bloquee la ruta.

<a id="solution"></a>
## Solución

`nullstate` ejecuta un ciclo purple-team local sobre Terraform IaC:

- Analizar infraestructura prevista.
- Intentar un exploit rojo.
- Generar remediación azul.
- Revalidar tras parche.
- Producir informe de evidencias.

<a id="demo-scenario"></a>
## Escenario de demo

La vía validada usa fixture S3 público LocalStack: `nullstate` detecta exposición, realiza lectura anónima restringida, parchea Terraform y comprueba bloqueo. Azure Blob sigue detección/remediación deterministas, pero la prueba LocalStack Azure en vivo espera habilitación o fallback de almacenamiento como Azurite.

<a id="why-amd-mi300x"></a>
## Por qué AMD MI300X

La arquitectura admite evidencias de contexto largo: JSON de planes, logs, salida de exploits y diffs a un endpoint local sin latencia de APIs externas ni exposición de datos.

<a id="next-steps"></a>
## Próximos pasos

- Más reglas Azure: claves compartidas, red pública, Key Vault público.
- Resolver habilitación LocalStack Azure o añadir Azurite para Blob.
- Adaptadores Kubernetes, Compose y on-prem en vivo con mismo modelo de artefactos.
- Evidencia GPU AMD con vLLM `/metrics` y capturas `amd-smi` o `rocm-smi`.
