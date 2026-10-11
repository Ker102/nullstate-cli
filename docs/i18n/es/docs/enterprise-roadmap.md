<a id="enterprise-and-monetization-roadmap"></a>
# Hoja de ruta empresarial y monetización

Este documento plantea `nullstate` como futuro producto DevSecOps empresarial, no solo CLI del hackathon.

<a id="product-positioning"></a>
## Posicionamiento

`nullstate` es una plataforma de validación de rutas cloud con evidencias. Correlaciona IaC con estado AWS/Azure observado, determina qué identidades alcanzan qué datos/capacidades, demuestra rutas seleccionadas bajo control, aplica remediación determinista y conserva evidencia.

Mensaje central:

> Los scanners indican qué podría estar mal. Nullstate prueba la ruta, corrige y valida bloqueo.

No requiere IaC completa de cuenta/suscripción. IaC aporta estado previsto; descubrimiento de solo lectura, recursos, identidad, red, logs y deriva. Grafo normalizado reconstruye solo camino mínimo relevante.

Los agentes IA son principales de primera clase: identidades dedicadas, IAM, principales de servicio, identidades administradas/de carga, gateways y delegación. Calcule radio efectivo si agente, prompts, memoria, conector, MCP, plugin o credencial posterior se compromete.

Postura externa es oportunidad de pago: recopilar/verificar identidad de carga, procedencia, digests, atestación, parches/vulnerabilidades, red, herramientas, vigencia, logs y revocación. Combine con datos/privilegios accesibles, no score opaco.

<a id="target-customers"></a>
## Clientes

<a id="primary"></a>
### Principales

- DevSecOps con mucho Terraform
- Plataforma con módulos IaC seguros por defecto
- Seguridad cloud verificando SLA de remediación
- Consultoras con informes basados en evidencia

<a id="secondary"></a>
### Secundarios

- Startups reguladas que no pueden enviar IaC a SaaS
- Empresas explorando IA privada de seguridad
- MSP y socios de migración cloud

<a id="core-value-propositions"></a>
## Propuestas de valor

<a id="1-evidence-over-alerts"></a>
### 1. Evidencias, no alertas

Los scanners suelen parar en hallazgos. `nullstate` genera cronología:

1. hallazgo
2. razonamiento rojo
3. comando en sandbox
4. parche
5. validación posterior
6. informe

<a id="2-local-first-and-private"></a>
### 2. Local-first y privado

IaC, planes y logs sensibles permanecen en cliente. Modelos usan endpoints privados compatibles OpenAI.

<a id="3-deterministic-security-core"></a>
### 3. Núcleo determinista

El modelo no decide éxito/fallo. Detección, remediación y validación deterministas mantienen fiabilidad empresarial.

<a id="4-devsecops-native-cli"></a>
### 4. CLI nativa DevSecOps

Primera interfaz local, CI o entorno efímero.

<a id="enterprise-product-tiers"></a>
## Ediciones empresariales

<a id="open-source-cli"></a>
### CLI de código abierto

Propósito: adopción y confianza.

Funciones:

- ejecuciones locales/offline
- biblioteca limitada
- informes
- ejecutor rojo restringido
- adaptadores básicos LocalStack
- docs comunitarias

<a id="team-edition"></a>
### Edición Team

Propósito: equipos pequeños/consultoras.

Funciones:

- packs ampliados
- informes HTML/PDF
- saneado
- comparación baseline
- plantillas GitHub Actions/GitLab CI
- exportación de historial
- presets de endpoints privados

Precio posible:

- por asiento: 19-49 EUR/mes
- o repo: 49-199 EUR/mes

<a id="enterprise-edition"></a>
### Edición Enterprise

Propósito: empresas con cumplimiento e infraestructura privada.

Funciones:

- policy-as-code de herramientas
- SSO/SAML/OIDC
- auditoría
- evidencia central
- permisos equipo/rol
- soporte despliegue privado
- escenarios a medida
- SLA empresarial
- Jira, ServiceNow, Slack, SIEM, GRC

Precio posible:

- contrato anual desde aproximadamente 15k-50k EUR/año
- packs y soporte como extras de pago

<a id="monetization-paths"></a>
## Vías de monetización

<a id="path-a-open-core-devsecops-cli"></a>
### Vía A: CLI DevSecOps open-core

Mantener núcleo abierto. Monetizar:

- packs empresariales
- dashboard cloud
- evidencia alojada
- despliegue privado
- exportaciones de cumplimiento

Ventajas:

- adopción desarrolladora
- credibilidad GitHub
- confianza comunitaria

Inconvenientes:

- límite gratis/pago claro
- carga de soporte creciente

<a id="path-b-security-consultancy-tooling"></a>
### Vía B: Herramientas de consultoría

Use `nullstate` como diferenciador de evaluaciones de pago.

Ofrecer:

- evaluación IaC purple-team
- endurecimiento módulos Terraform
- PR de remediación
- paquetes auditables

Ventajas:

- primeros ingresos más fáciles
- sin SaaS completo
- casos y pruebas de clientes

Inconvenientes:

- servicios escalan peor

<a id="path-c-enterprise-private-ai-security-platform"></a>
### Vía C: Plataforma privada IA empresarial

Capa de validación IA privada para IaC/controles cloud.

Ventajas:

- narrativa MI300X/privado alineada
- presupuestos mayores

Inconvenientes:

- ventas largas
- más endurecimiento/integraciones

<a id="recommended-near-term-strategy"></a>
## Estrategia cercana

Híbrido A+B:

1. CLI abierto.
2. Marca técnica fuerte de validación IaC con evidencias.
3. Contenido portfolio/casos para atención.
4. Primero servicios de evaluación/implementación.
5. Convertir necesidades repetidas en funciones Team/Enterprise.

<a id="product-architecture-cli-local-gui-and-paid-platform"></a>
## Arquitectura: CLI, GUI local y plataforma de pago

CLI permanece motor abierto, local/CI, artefactos y exportación portable.

GUI gratis es visor/operador monousuario: lee `runs/`, genera dashboards, inicia run/report/bundle/sandbox. Sin login cloud ni equipos/cumplimiento/alertas/modelos administrados.

App cloud/autoalojada de pago ingiere paquetes y da paneles de equipo, modelos alojados, historial, soporte, automatización, alertas, integración, RBAC, auditoría y cumplimiento.

`run-bundle.json` es contrato entre CLI, dashboard gratis, CI, soporte y futuro pago. `docs/schemas/run-bundle.schema.json` describe v1; CLI valida antes de escribir.

`nullstate upload --dry-run` crea plan sin red: intención endpoint, checksum, artefactos, token presente, preflight, sin datos ni valores secretos. `docs/schemas/upload-plan.schema.json` describe v1 y CLI valida.

<a id="ci-and-managed-model-inference"></a>
## CI e inferencia administrada

Dos modos:

- Modelo del cliente: secretos `NULLSTATE_LLM_BASE_URL` y `NULLSTATE_LLM_API_KEY`.
- Modelo Nullstate: secreto `NULLSTATE_CLOUD_TOKEN`, razonamiento rojo/azul por Cloud.

Modo administrado es pago por medición de organización, proyecto, ejecución, modelo, tokens, latencia y coste.

Tres disparadores:

1. PR por IaC/políticas/manifiestos: analiza propuesta, baseline, opcional prueba de alto riesgo desechable y bloquea por política.
2. Tras Terraform, CloudFormation, Bicep u otro despliegue: inventario vivo, deriva, rutas afectadas.
3. Programado: cambios consola, no gestionados, permisos, endpoints, riesgo antiguo y cambios fuera Git.

Producción se descubre solo lectura. Checks no destructivos necesitan aprobación de política. Exploits se dirigen a emulador/gemelo/clúster/cuenta AWS/suscripción Azure dedicados según fidelidad.

<a id="support-automation-and-alerts"></a>
## Soporte, automatización y alertas

Pago con panel de soporte/comentarios. Tickets adjuntan bundle saneado, versión, ID, escenario y link dashboard.

Escaneos de repos conectados o IaC subido; alertas por nuevos críticos, exploits observados, remediación/CI fallida, riesgo antiguo y endpoints fallidos. Primero email/webhooks, luego Slack, Teams, Jira, GitHub Issues, SIEM.

<a id="brand-direction"></a>
## Marca

<a id="name"></a>
### Nombre

`nullstate` sugiere volver el riesgo de infraestructura a baseline segura.

<a id="tagline-options"></a>
### Lemas

- Probar, corregir y validar riesgo IaC.
- Validación purple-team Terraform.
- Del hallazgo IaC a ruta bloqueada.
- DevSecOps cloud con evidencias.
- Validación local-first de ataques IaC.

Lema principal recomendado:

> Probar, corregir y validar rutas cloud.

<a id="brand-personality"></a>
### Personalidad

- precisa
- técnica
- confiable
- seguridad primero
- consciente de empresa
- sin exageración

Evite «hacker autónomo» antes de herramientas rojas profundas. Prefiera:

- ejecución roja restringida
- validación con evidencias
- ciclo purple-team local-first

<a id="enterprise-reliability-requirements"></a>
## Fiabilidad empresarial

Antes de depender comercialmente:

1. Sondeos exploit reales principales.
2. Distinguir simulado, inferido, observado.
3. Allowlists por política. Ya disponibles campos validados de escenario, backend, etapa, argumentos, clasificación/host, comando, timeout y salida.
4. Saneado.
5. Esquema estable. Manifiestos generados ya tienen esquema y validación previa.
6. CI con códigos legibles. Ya `nullstate run --ci` y `ci-summary.json` validado.
7. SARIF/JSON; exportación y policy-result disponibles.
8. Manifiestos reproducibles. `nullstate evidence-manifest` SHA-256/HMAC opcional, v1 validado; `nullstate evidence-verify` verifica.
9. Procedencia release: checksum, wheel en entorno SBOM limpio, `sbom.spdx.json`, atestaciones de paquete/SBOM, Sigstore sin clave y ensayo manual.
10. Reglas versionadas. `remediation.json` versión, archivos, IDs deterministas, `$schema` y contrato v1 validado.
11. Nunca nube real salvo habilitación explícita.

<a id="next-feature-priorities"></a>
## Prioridades

<a id="p0-trust-and-correctness"></a>
### P0: Confianza y exactitud

- sondeo S3 real
- sección runtime en informes
- saneador
- veredicto/códigos vía `ci-summary.json` validado

<a id="p1-cicd-adoption"></a>
### P1: Adopción CI/CD

- `nullstate run --ci`
- SARIF `nullstate sarif`
- plantilla Actions
- baseline/severidad con `nullstate baseline` y `--baseline-file`
- plan `nullstate upload --dry-run`
- validar `docs/schemas/upload-plan.schema.json`
- validar `docs/schemas/attack-manifest.schema.json`

<a id="p2-enterprise-controls"></a>
### P2: Controles empresariales

- política de escenarios/backends/etapas/clases/hosts/comandos/timeouts/salida
- presets baseline/específicos `nullstate policy init`
- validar `docs/schemas/nullstate-policy.schema.json`
- config organización
- integridad `nullstate evidence-manifest`
- validar `docs/schemas/evidence-manifest.schema.json`
- hashes `nullstate evidence-verify`
- firmas HMAC opcionales
- procedencia GitHub
- SBOM GitHub
- Sigstore
- lista primera etiqueta en runbook
- metadatos `remediation.json` validados
- inventario IA AWS/Azure
- separar agente, usuario delegado, runtime, herramienta, credenciales posteriores
- inyección/exceso de agencia con datos sintéticos y herramientas controladas
- confianza entre agentes/identidad compartida
- postura externa y vigencia
- firma, digest, SLSA, SPIFFE/SPIRE, hardware
- gateway reduce privilegio si falta/caduca evidencia

<a id="p3-growth-and-brand"></a>
### P3: Crecimiento y marca

- caso portfolio
- vídeo
- artículo técnico
- comparación scanners
- landing con GIF CLI

<a id="case-study-angle"></a>
## Enfoque de caso

No «hice un scanner», sino:

> Una CLI DevSecOps local que convierte hallazgos Terraform en ciclo reproducible: detectar, razonar, comando restringido, remediación determinista, bloqueo y evidencia.

Salvedad honesta:

> Hackathon ya tiene frontera segura de ejecución. Siguiente iteración amplía scripts de salud a exploits reales de sandbox.

Esta honestidad mejora credibilidad ante revisores.

<a id="success-metrics"></a>
## Métricas

Técnicas:

- escenarios con exploit observado
- falsos positivos en fixtures
- éxito remediación
- reproducibilidad
- integridad de evidencia de comandos

Negocio:

- estrellas/forks
- finalización vídeo
- conversaciones entrantes
- pilotos
- leads evaluación de pago
- uso CI recurrente

<a id="90-day-roadmap"></a>
## Hoja de ruta 90 días

<a id="days-1-14"></a>
### Días 1-14

- exploit S3 real
- sección runtime
- saneador
- pulir recorrido técnico
- publicar caso portfolio

<a id="days-15-30"></a>
### Días 15-30

- sondeo Azure real o límites explícitos
- CI más allá baseline/severidad
- SARIF/JSON
- ejemplo Actions

<a id="days-31-60"></a>
### Días 31-60

- pack AWS/Azure
- política comandos/clases/hosts
- manifiesto integridad
- verificar firmado
- landing por caso

<a id="days-61-90"></a>
### Días 61-90

- contactar primer socio de diseño
- oferta evaluación de pago
- prototipo panel/evidencia
- arquitectura empresarial
