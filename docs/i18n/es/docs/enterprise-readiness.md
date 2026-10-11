<a id="enterprise-readiness"></a>
# Preparación empresarial

Esta lista sigue los controles para pasar `nullstate` de prototipo local del hackathon a herramienta DevSecOps empresarial. Separa lo ya impuesto de lo que falta antes del uso de pago en equipos, nube o autoalojado.

<a id="current-controls"></a>
## Controles actuales

| Control | Estado | Evidencia |
|---|---|---|
| Fuente de verdad determinista | implementado | detectores en `src/nullstate/findings.py` |
| Remediación determinista | implementado | lógica en `src/nullstate/remediation.py` |
| Workspace copiado | implementado | no modifica IaC original |
| Ejecutor rojo restringido | implementado | solo `attack.py` del directorio de ejecución |
| Entradas de sondeo por manifiesto | implementado | `attack-manifest.json` contiene escenario, backend, URL e indicios de recursos validados por esquema |
| Logs runtime | implementado | eventos `red-tool` con salida y tiempos |
| Imposición local | implementado | rechaza HTTP no local por defecto |
| Hashes de ataque | implementado | eventos `red-tool` con SHA-256 de script y manifiesto |
| Metadatos de truncado | implementado | `red-tool` indica stdout/stderr truncados |
| Saneado no destructivo | implementado | `nullstate scrub` copia y redacta |
| Preflight de subida | implementado | `nullstate upload --dry-run` registra saneado y advierte de originales |
| Contrato de plan | implementado | `docs/schemas/upload-plan.schema.json` describe dry-run; CLI valida planes |
| Clasificación de evidencias | implementado | runtime, inconcluso y simulación offline separados |
| Panel y paquete local | implementado | `nullstate dashboard`, `nullstate bundle`, `docs/schemas/run-bundle.schema.json` |
| Política roja inicial | implementado | `nullstate policy init`, presets y `run --policy-file` imponen campos validados de escenario, backend, etapa, argumentos, clase/host objetivo, comando, timeout y salida |
| Artefacto de validación | implementado | `nullstate policy validate` escribe opcional `policy-validation.json` |
| Integridad de evidencias | implementado | `nullstate evidence-manifest` inventaría SHA-256 validado y firma HMAC opcional |
| Verificación de manifiesto | implementado | `nullstate evidence-verify` detecta falta/cambio, copias y firmas HMAC inválidas |
| Procedencia de versión | implementado | workflow etiquetado escribe `release-manifest.json` y atesta `dist/*` |
| SBOM de versión | implementado | wheel en entorno limpio; `sbom.spdx.json` validado localmente y SPDX, atestado GitHub |
| Firma sin clave | implementado | recursos principales firmados Sigstore vía GitHub OIDC |
| Ensayo de publicación | implementado | `workflow_dispatch` manual valida sin crear release |
| Reglas versionadas | implementado | `remediation.json` registra versión, escenario, archivos e IDs con contrato v1 validado |

<a id="required-before-enterprise-claims"></a>
## Antes de afirmar preparación empresarial

<a id="local-only-enforcement"></a>
### Imposición de solo local

Los objetivos runtime predeterminados siguen locales:

- `offline://...`
- `local://...`
- `127.0.0.1`
- `localhost`
- `localhost.localstack.cloud`

El ejecutor rechaza HTTP no local por defecto. Nube real requiere `--allow-live-cloud` explícito, apagado por defecto. La aprobación queda en `events.jsonl` y eventos rojos indican si se habilitó para el comando. `allowed_target_hosts` restringe además HTTP(S) a nombres exactos o sufijos `*.domain`.

<a id="command-allowlist-policy"></a>
### Política de comandos permitidos

El ejecutor debe seguir basado en plantillas. La política debe definir:

- nombres de escenarios permitidos
- backends permitidos
- nombre de script generado permitido
- argumentos CLI permitidos
- timeout máximo
- bytes stdout/stderr máximos
- clasificaciones y patrones de host permitidos

El modelo puede explicar la ruta, pero no crear comandos shell arbitrarios.

`nullstate policy init` crea JSON con `$schema` a `docs/schemas/nullstate-policy.schema.json` y valida antes de escribir. `nullstate policy init --scenario <name>` restringe a un par conocido, útil si CI no debe permitir todos los esqueletos. `nullstate policy validate` comprueba antes de CI/escenarios. `nullstate run --policy-file` impone escenario, backend, etapa, flags de `attack.py`, clases, hosts, IDs de política, timeout y salida antes de ejecutar `attack.py`. No es un motor completo, pero establece contrato para políticas futuras por escenario.

`nullstate run --ci` escribe `ci-summary.json` con esquema, decisión, código, umbral, recuentos, división baseline y estados antes/después. Valida contra `docs/schemas/ci-summary.schema.json` para automatización fiable.

<a id="event-schema-hardening"></a>
### Endurecimiento del esquema de eventos

Los eventos `red-tool` incluyen primeros metadatos de auditoría:

- `schema_version`
- `command_policy_id`
- `attack_script_sha256`
- `manifest_sha256`

Con el tiempo deben añadir más políticas. Ya incluyen:

- `stdout_truncated`
- `stderr_truncated`

También incluyen:

- `live_cloud_allowed`
- valores `target_classification` ampliados, incluido `external-http` al habilitar explícitamente nube en vivo

Estos campos facilitan reproducibilidad y auditoría en CI, soporte y cumplimiento.

`nullstate evidence-manifest` añade inventario para soporte/casos/ingestión. SHA-256 y tamaños de artefactos compartibles excluyen workspaces, internos Terraform, cachés Python, propio manifiesto y verificación. Incluye `$schema` a `docs/schemas/evidence-manifest.schema.json`, validado antes de escribir. `--signing-key-env` firma HMAC-SHA256 con secreto de entorno nunca escrito. `nullstate evidence-verify` recalcula y escribe `evidence-verification.json`; código `2` ante falta, cambio, identidad de otra ejecución o firma inválida.

Las versiones etiquetadas generan `release-manifest.json` con SHA-256 y `sbom.spdx.json` desde wheel limpio. Validan estructura y `pyspdxtools` antes de manifiesto/atestación. GitHub atesta procedencia y predicado SPDX para `dist/*`. Sigstore publica `.sigstore.json` junto a wheel, sdist, SBOM y manifiesto. Es procedencia de suministro, distinta de HMAC de evidencias.

El workflow manual con `dry_run=true` ensaya construcción, validación, atestación, firma y comprobaciones sin crear release GitHub.

Cada ejecución escribe `remediation.json` junto a `remediation.patch`: versión determinista, escenario, bandera de cambio, archivos e IDs. Incluye `$schema` a `docs/schemas/remediation-metadata.schema.json`, validado antes de informes/paquetes/artefactos para relacionar parche con contrato exacto.

`run-bundle.json` tiene esquema y validación local: `$schema` apunta a `docs/schemas/run-bundle.schema.json`; `nullstate bundle` falla antes de escribir si contrato superior malformado.

El panel muestra hallazgos, reglas, esquema, inventario, cronología y extracto. Sigue monousuario basado en archivos; historial de equipos, RBAC, escaneos programados y cumplimiento son plataforma de pago.

<a id="artifact-scrubbing"></a>
### Saneado de artefactos

Antes de publicar/subir/adjuntar ejecute `nullstate scrub`. Copia saneada redacta:

- tokens LocalStack
- claves de modelos
- IDs de cuentas cloud
- IDs Azure de inquilino/suscripción
- endpoints privados y mapas IP
- valores de estado Terraform
- credenciales del proveedor
- prompts crudos con contexto cliente

Escribe `scrub-report.json` con archivos y reglas coincidentes.

`nullstate upload --dry-run` comprueba `scrub-report.json` y registra `preflight.scrub` en `upload-plan.json`. Incluye `$schema` a `docs/schemas/upload-plan.schema.json`, validado. Permite originales para planificación local, pero `upload_recommended: false` y advertencia.

<a id="evidence-classification"></a>
### Clasificación de evidencias

Evite exageraciones empresariales. Use:

- `runtime exploit observed`: salida prueba acceso objeto/blob.
- `runtime probe did not observe exploit`: llegó al objetivo; tras remediación acceso bloqueado o no disponible.
- `runtime probe inconclusive`: emulador, ruta o soporte impidieron prueba.
- `offline deterministic simulation`: sin sondeo runtime vivo.

Si dice «explotado», incluya evidencia de comando observado o indique simulación determinista offline.

<a id="near-term-readiness-tasks"></a>
## Tareas a corto plazo

1. Validar Azure LocalStack en vivo y documentar límites de emulador.
2. Añadir adaptadores cloud solo con allowlists por proveedor y aprobación.

<a id="commercial-boundary"></a>
## Límite comercial

CLI abierto conserva local/offline, LocalStack, informes, paquetes, panel individual. Pago debe centrarse en gobernanza:

- historial centralizado
- RBAC/logs auditoría
- allowlists policy-as-code
- modelos administrados
- soporte con bundles
- exportaciones cumplimiento
- escaneos/alertas programados
- despliegue privado
