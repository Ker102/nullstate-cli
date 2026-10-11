<a id="technical-walkthrough"></a>
# Recorrido técnico

Este documento explica cómo funciona `nullstate` desde el primer comando de la CLI hasta el artefacto final del informe. Está dirigido a revisores que quieren entender la ruta de implementación, los límites de seguridad y los puntos de extensión actuales.

<a id="what-nullstate-runs"></a>
## Qué ejecuta Nullstate

`nullstate` es un ciclo de equipo morado para infraestructura como código que prioriza la ejecución local. La implementación actual se centra en escenarios de exposición de almacenamiento con Terraform:

- Bloqueo de acceso público de AWS S3 deshabilitado
- Acceso público a contenedores de Azure Blob

También incluye estructuras base de escenarios offline para Kubernetes, Docker Compose, gemelos digitales en instalaciones propias y revisión genérica de planes.

La CLI combina tres capas:

1. Lógica de seguridad determinista para hallazgos, remediación y validación de aprobación o fallo.
2. Adaptadores de sandbox para destinos de ejecución locales como LocalStack.
3. Razonamiento de equipo rojo y equipo azul asistido por modelos mediante endpoints compatibles con OpenAI.

El modelo ayuda con el razonamiento y la explicación. No es la fuente de verdad para determinar si existe la vulnerabilidad o si funcionó la remediación.

<a id="demo-command-flow"></a>
## Flujo de comandos de demostración

Flujo offline típico:

```powershell
nullstate
nullstate status
nullstate run examples/aws-public-s3 --offline
nullstate report
```

Flujo típico de ejecución en vivo con LocalStack AWS:

```powershell
nullstate sandbox up localstack-aws
nullstate sandbox status localstack-aws
nullstate run examples/aws-public-s3 --target localstack-aws
nullstate report
```

Flujo típico de ejecución en vivo con LocalStack Azure:

```powershell
nullstate sandbox up localstack-azure
nullstate sandbox status localstack-azure
nullstate run examples/azure-public-blob --target localstack-azure
nullstate report
```

Cuando haya disponible un endpoint de modelo autoalojado, use el proveedor personalizado y configure un endpoint compartido:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_LLM_BASE_URL = "http://127.0.0.1:8000"
```

O configure endpoints específicos para cada rol:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
```

Los preajustes de proveedores gestionados pueden evitar la configuración del endpoint a los usuarios que aportan sus propias claves:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
```

El preajuste `claude` también está disponible mediante la capa de compatibilidad con el SDK de OpenAI de Anthropic, pero debe considerarse experimental hasta que exista un adaptador nativo de Claude.

<a id="runtime-modes"></a>
## Modos de ejecución

<a id="offline-mode"></a>
### Modo offline

`--offline` omite la ejecución de Terraform y las llamadas al emulador de nube. La CLI utiliza análisis estático de IaC y comportamiento determinista de escenarios. Este modo se utiliza para demostraciones repetibles, pruebas y desarrollo sin Docker, LocalStack ni GPU.

Detalle importante: `--offline` no deshabilita automáticamente las llamadas a modelos. Si están configuradas las variables de entorno de los endpoints de modelos, las llamadas de los agentes rojo y azul siguen utilizando esos endpoints. Use `--mock-agents` cuando se pretenda un comportamiento totalmente determinista y sin modelos.

<a id="live-localstack-mode"></a>
### Modo de ejecución en vivo con LocalStack

El modo en vivo copia el proyecto Terraform a un espacio de trabajo de ejecución, ejecuta comandos de automatización de Terraform, usa LocalStack como destino, ejecuta el ciclo rojo/azul, aplica la remediación en el espacio de trabajo copiado y vuelve a validar.

El directorio original de Terraform no se modifica. La remediación se realiza en:

```text
runs/<run-id>/workspace/
```

<a id="model-endpoint-mode"></a>
### Modo de endpoint de modelo

El endpoint de modelo debe exponer una API compatible con OpenAI. Esto permite que la misma integración de la CLI funcione con vLLM local, SGLang, preajustes de proveedores gestionados o un proxy personalizado.

La resolución del proveedor sigue este orden:

1. opciones de la CLI o valores de entorno específicos del rol
2. opciones de la CLI o valores de entorno compartidos
3. URL predeterminada del preajuste del proveedor
4. agente simulado determinista como alternativa cuando no hay un endpoint configurado

El preajuste `google` se resuelve al endpoint de Gemini compatible con OpenAI. El preajuste `claude` se resuelve al endpoint de compatibilidad con el SDK de OpenAI de Anthropic. Los modos `custom` y `openai-compatible` requieren una URL base, salvo que se proporcione una URL específica del rol.

La CLI registra los recuentos de tokens y la latencia del modelo a partir de los campos `usage` de la respuesta cuando están disponibles. También intenta recopilar `/metrics` de estilo Prometheus del endpoint y escribe las instantáneas de métricas sin procesar en el directorio de ejecución.

<a id="end-to-end-execution-path"></a>
## Ruta de ejecución de extremo a extremo

<a id="1-command-entry"></a>
### 1. Entrada del comando

Punto de entrada:

```text
src/nullstate/cli.py
```

El comando `run` recibe:

- directorio de Terraform
- backend de destino, o `auto`
- escenario, o `auto`
- opciones de modo offline o simulado
- directorio de artefactos de ejecución
- configuración de los modelos rojo y azul

Si no se proporciona ningún comando, la CLI muestra la pantalla de inicio con la identidad de la marca y los posibles comandos siguientes.

<a id="2-scenario-inference"></a>
### 2. Inferencia del escenario

Archivos relevantes:

```text
src/nullstate/scenario_detection.py
src/nullstate/scenarios.py
```

Cuando se usa `--scenario auto`, la CLI inspecciona el directorio de IaC y asigna la entrada a un escenario conocido. Por ejemplo:

- `examples/aws-public-s3` se asigna a `aws-public-s3`
- `examples/azure-public-blob` se asigna a `azure-public-blob`

La definición del escenario elige el backend de sandbox predeterminado. Los usuarios pueden seguir sobrescribiéndolo con `--target`.

<a id="3-sandbox-backend-selection"></a>
### 3. Selección del backend de sandbox

Archivo relevante:

```text
src/nullstate/sandbox.py
```

Los backends de sandbox definen:

- nombre del backend
- tipo de IaC de destino
- modo de ejecución
- imagen de Docker
- comandos de arranque y parada
- sondas de ejecución

Los backends actuales incluyen:

| Backend | Propósito |
|---|---|
| `localstack-aws` | Ejecución en vivo de escenarios de almacenamiento de tipo AWS |
| `localstack-azure` | Ejecución en vivo de escenarios de almacenamiento de tipo Azure |
| `kind-kubernetes` | Estructura base de escenarios de Kubernetes |
| `docker-compose` | Estructura base de gemelos digitales de Docker Compose |
| `microvm-onprem` | Estructura base de gemelos digitales en instalaciones propias |
| `plan-only` | Modo de análisis sin ejecución |

`nullstate sandbox up` inicia el backend. `nullstate sandbox status` comprueba Docker y la accesibilidad HTTP cuando corresponde.

<a id="4-run-workspace-creation"></a>
### 4. Creación del espacio de trabajo de ejecución

La CLI crea un nuevo directorio de ejecución:

```text
runs/<run-id>/
```

Copia el directorio de Terraform de entrada en:

```text
runs/<run-id>/workspace/
```

Esto mantiene intacto el proyecto original. El estado de Terraform, `.terraform`, los planes en caché y los directorios de ejecución se excluyen de la copia.

<a id="5-terraform-plan-loading"></a>
### 5. Carga del plan de Terraform

Archivo relevante:

```text
src/nullstate/terraform.py
```

En modo en vivo, el flujo de Terraform utiliza comandos adecuados para la automatización:

```text
terraform init -input=false
terraform plan -out=tfplan -input=false
terraform show -json tfplan
```

En modo offline, la CLI utiliza un analizador estático de Terraform para los ejemplos de demostración admitidos. Esto mantiene reproducibles las pruebas y demostraciones incluso sin dependencias externas de ejecución.

Los resultados de los comandos de Terraform se escriben en:

```text
runs/<run-id>/events.jsonl
```

<a id="6-finding-detection"></a>
### 6. Detección de hallazgos

Archivo relevante:

```text
src/nullstate/findings.py
```

El detector determinista identifica las configuraciones de riesgo admitidas. Ejemplos:

- El contenedor de Azure Blob tiene `container_access_type = "blob"` o `"container"`
- La cuenta de almacenamiento de Azure permite elementos públicos anidados
- Los controles de bloqueo de acceso público de AWS S3 están deshabilitados

Los hallazgos se escriben como JSON estructurado:

```text
runs/<run-id>/findings.json
```

Estos datos deterministas de hallazgos son la fuente de verdad para el resto de la ejecución.

<a id="7-red-team-model-reasoning"></a>
### 7. Razonamiento del modelo de equipo rojo

Archivo relevante:

```text
src/nullstate/agents.py
```

El agente rojo recibe instrucciones internas y evidencias del escenario. El usuario no introduce manualmente instrucciones para el modelo durante la ejecución.

El modelo rojo devuelve razonamiento sobre el ataque, por ejemplo:

- ruta de lectura anónima de objetos de S3
- ruta de lectura anónima de contenedores de Azure Blob
- evidencias que probablemente convenga recopilar

Si no hay un endpoint configurado, el rol recurre a una salida simulada determinista.

<a id="8-constrained-attack-script-execution"></a>
### 8. Ejecución restringida del script de ataque

Archivos relevantes:

```text
src/nullstate/attack.py
src/nullstate/attack_runner.py
```

`nullstate` escribe un artefacto de ataque generado:

```text
runs/<run-id>/attack.py
runs/<run-id>/attack-manifest.json
```

El manifiesto registra el escenario, el backend, la URL de destino y las pistas sobre recursos que pueden utilizar las sondas del escenario sin dar al modelo capacidad para construir comandos arbitrarios. Incluye un puntero `$schema` a `docs/schemas/attack-manifest.schema.json`, y `nullstate run` valida el manifiesto antes de la ejecución restringida de las sondas.

Después, el ejecutor restringido ejecuta únicamente ese script generado. Aplica estos límites:

- el nombre del script debe ser exactamente `attack.py`
- el script debe estar directamente dentro del directorio de la ejecución actual
- la ejecución utiliza el intérprete de Python actual
- no se acepta ningún comando de shell arbitrario
- las entradas dinámicas se limitan a `--target-url`, `--stage` y el `attack-manifest.json` generado en el directorio de ejecución

El ejecutor registra evidencias de los comandos antes y después de la remediación:

```json
{
  "phase": "red-tool",
  "message": "Allowlisted attack command completed",
  "data": {
    "command": ["python", "attack.py", "--target-url", "...", "--stage", "before", "--manifest", "..."],
    "target_url": "...",
    "stage": "before",
    "returncode": 0,
    "stdout": "...",
    "stderr": "",
    "started_at": "...",
    "ended_at": "...",
    "duration_seconds": 0.123
  }
}
```

Esto proporciona al informe evidencias de comandos reales y evita el acceso sin restricciones del agente rojo a herramientas.

Controles de protección empresariales para esta capa:

- La política de comandos se basa en plantillas de escenarios. El modelo puede razonar sobre la ruta de ataque, pero no puede elegir un comando de shell arbitrario.
- `nullstate policy init` crea un archivo de política con referencia a un esquema y lo valida antes de escribirlo; `policy init --scenario <name>` crea un preajuste más limitado para un par de escenario/backend. `run --policy-file` aplica antes de la ejecución los escenarios, backends y etapas permitidos, las opciones del `attack.py` generado, las clasificaciones de destinos, las listas de hosts de destino permitidos, los identificadores de políticas de comandos y los límites de tiempo y tamaño de salida.
- `nullstate policy validate` comprueba un archivo de política sin ejecutar un escenario y puede escribir `policy-validation.json` como evidencia para CI.
- Los destinos de ejecución siguen siendo endpoints de sandbox locales, salvo que se proporcione y registre explícitamente `--allow-live-cloud`.
- Los eventos `red-tool` incluyen una versión del esquema de comandos y hashes de reproducibilidad del `attack.py` generado y del manifiesto.
- La salida estándar y la salida de error de las sondas deben limitarse antes de cargarlas, adjuntarlas a tickets o conservarlas como evidencia a largo plazo.
- Los informes deben distinguir las evidencias observadas en ejecución de la simulación determinista y de las sondas con resultados no concluyentes en el emulador.

<a id="9-deterministic-remediation"></a>
### 9. Remediación determinista

Archivo relevante:

```text
src/nullstate/remediation.py
```

El modelo azul explica la remediación, pero el parche en sí lo produce la lógica de remediación determinista.

Para la exposición de Azure Blob, la remediación establece:

```hcl
allow_nested_items_to_be_public = false
container_access_type           = "private"
```

Para la exposición de AWS S3, la remediación establece los controles de bloqueo de acceso público en `true`:

```hcl
block_public_acls       = true
block_public_policy     = true
ignore_public_acls      = true
restrict_public_buckets = true
```

El diff se escribe en:

```text
runs/<run-id>/remediation.patch
```

<a id="10-re-plan-and-validation"></a>
### 10. Nuevo plan y validación

Después de la remediación, la CLI vuelve a cargar el espacio de trabajo remediado. En modo en vivo ejecuta los pasos de plan y aplicación de Terraform sobre el espacio de trabajo copiado. En modo offline vuelve a analizar los archivos actualizados.

El detector vuelve a ejecutarse. Si el hallazgo ha desaparecido, la simulación determinista del ataque devuelve:

```text
Red after: blocked
```

El script de ataque restringido también se ejecuta una segunda vez con:

```text
--stage after
```

La salida de ese comando posterior a la remediación se registra como otro evento `red-tool`.

<a id="11-report-and-metrics"></a>
### 11. Informe y métricas

Archivos relevantes:

```text
src/nullstate/report.py
src/nullstate/metrics.py
```

Cada ejecución escribe:

| Artefacto | Propósito |
|---|---|
| `events.jsonl` | Cronología completa de eventos |
| `findings.json` | Hallazgos de vulnerabilidades estructurados |
| `attack.py` | Artefacto de ataque restringido generado |
| `attack-manifest.json` | Escenario, backend, URL de destino y pistas sobre recursos para sondas restringidas, validados mediante esquema |
| `remediation.patch` | Diff de remediación de Terraform |
| `remediation.json` | Metadatos del conjunto de reglas de remediación determinista validados mediante esquema |
| `metrics.json` | Llamadas a modelos, recuentos de tokens, latencia y métricas del endpoint |
| `ci-summary.json` | Veredicto de CI legible por máquina y validado mediante esquema cuando se usa `--ci` |
| `policy-result.json` | Decisión de política JSON independiente para una ejecución existente |
| `report.md` | Resumen legible por personas |
| `evidence-manifest.json` | Inventario SHA-256 de evidencias de ejecución compartibles cuando se usa `nullstate evidence-manifest` |
| `evidence-verification.json` | Resultado de verificación de un manifiesto cuando se usa `nullstate evidence-verify` |
| `upload-plan.json` | Plan de carga sin red cuando se usa `nullstate upload --dry-run` |
| `workspace/` | Espacio de trabajo de IaC copiado y remediado |

`nullstate report` abre el informe más reciente de forma predeterminada, incluidos los informes anidados en directorios de ejecución con nombre.

`remediation.json` incluye un puntero `$schema` a `docs/schemas/remediation-metadata.schema.json`, y los metadatos de remediación generados se validan antes de que los utilicen los informes, paquetes y artefactos de ejecución.

`nullstate bundle` escribe `run-bundle.json`, el contrato portátil de evidencias para paneles locales, cargas de CI, paquetes de soporte y la futura ingesta de Nullstate Cloud. El paquete incluye un puntero `$schema` a `docs/schemas/run-bundle.schema.json`, y la CLI valida su estructura antes de escribirlo. El paquete también incluye los metadatos de `remediation.json` cuando están disponibles, para que las herramientas posteriores puedan mostrar la versión del conjunto de reglas de remediación y los identificadores de las reglas.

`nullstate dashboard` escribe `dashboard.html`, un panel local gratuito de una única ejecución que puede abrirse sin iniciar sesión en la nube. Resume los hallazgos, los metadatos de remediación, los metadatos del esquema del paquete, el inventario de artefactos, la cronología de evidencias y el extracto del informe.

`nullstate sarif` escribe `nullstate.sarif`, una exportación SARIF 2.1.0 con un resultado por hallazgo para cargas de CI y de análisis de código.

`nullstate run --ci` escribe `ci-summary.json` y termina con el código `2` cuando los hallazgos originales de la ejecución alcanzan o superan `--fail-on-severity`. El resumen incluye un puntero `$schema` a `docs/schemas/ci-summary.schema.json` y se valida antes de escribirlo, lo que da a CI un control de políticas estable sin cambiar el informe para personas.

`nullstate baseline` escribe una línea base JSON de identidades de hallazgos. Cuando se usa `nullstate run --ci --baseline-file`, los hallazgos conocidos de la línea base siguen siendo visibles, pero el umbral de fallo de CI se evalúa únicamente con los hallazgos nuevos.

`nullstate policy-result` escribe el mismo tipo de decisión de umbral y línea base para una ejecución existente sin volver a ejecutar el escenario.

`nullstate evidence-manifest` escribe `evidence-manifest.json`, un inventario determinista de integridad de artefactos de ejecución compartibles. El manifiesto incluye un puntero `$schema` a `docs/schemas/evidence-manifest.schema.json`, y la CLI valida su estructura antes de escribirlo. Excluye los espacios de trabajo copiados, los componentes internos de Terraform, las cachés de Python, el propio archivo de manifiesto y la salida de verificación. Use `--signing-key-env` para adjuntar una firma de evidencias HMAC-SHA256 de clave compartida a partir de un secreto del entorno; esto firma evidencias de ejecución, no acredita la procedencia de paquetes mediante clave pública.

`nullstate evidence-verify` escribe `evidence-verification.json` después de recalcular los hashes y tamaños de archivo de los artefactos registrados. Comprueba solo los artefactos enumerados en el manifiesto, ignora los archivos nuevos no relacionados, verifica las firmas HMAC cuando se proporciona `--signing-key-env` y termina con el código `2` cuando un artefacto registrado falta, ha cambiado, se ha copiado de otra ejecución o tiene una firma no válida.

`nullstate upload --dry-run` escribe `upload-plan.json`, actualiza `run-bundle.json`, registra el endpoint previsto y la variable de entorno del token, y confirma si el token existe sin almacenar su valor. El plan incluye un puntero `$schema` a `docs/schemas/upload-plan.schema.json`, y la CLI valida su estructura antes de escribirlo. También registra el estado de la comprobación previa de sanitización: las ejecuciones sin procesar advierten con `upload_recommended: false`, mientras que las copias sanitizadas con `scrub-report.json` se marcan como listas para carga para la futura ruta de ingesta.

`nullstate scrub` crea una copia sanitizada de una ejecución bajo `scrubbed-runs/` y escribe `scrub-report.json`. Deja intacta la ejecución original y se niega a sobrescribir una copia sanitizada existente.

<a id="security-boundaries"></a>
## Límites de seguridad

Los límites importantes son:

- Ningún destino de nube real de forma predeterminada.
- Los cambios de Terraform se realizan en un espacio de trabajo copiado.
- El modelo rojo no recibe acceso al shell.
- El ejecutor de ataques solo ejecuta el `attack.py` generado en el directorio de ejecución.
- Los secretos se cargan de variables de entorno o de archivos env locales ignorados.
- Los artefactos de ejecución deben revisarse antes de publicarse.
- Se debe ejecutar `nullstate scrub` antes de publicar estudios de caso públicos, cargar a CI o compartir paquetes de soporte.
- Se requiere `--allow-live-cloud` antes de apuntar a cualquier endpoint de nube no local.

<a id="extension-points"></a>
## Puntos de extensión

<a id="new-scenario"></a>
### Nuevo escenario

Añada o actualice:

```text
src/nullstate/scenarios.py
src/nullstate/scenario_detection.py
src/nullstate/findings.py
src/nullstate/remediation.py
src/nullstate/attack.py
examples/<scenario-name>/
tests/
```

<a id="new-sandbox-backend"></a>
### Nuevo backend de sandbox

Añada metadatos y comandos del backend en:

```text
src/nullstate/sandbox.py
```

Después, añada pruebas para:

- `sandbox list`
- `sandbox status`
- `sandbox up --dry-run`
- `sandbox down`

<a id="richer-red-tooling"></a>
### Herramientas más completas para el equipo rojo

La siguiente ampliación segura no consiste en acceso libre al shell. Debe ser una lista de permitidos por escenario:

- sondas de Python generadas
- plantillas de comandos fijas
- URL de destino exclusivamente locales
- tiempo de espera estricto
- registro completo de eventos
- sin credenciales heredadas de nube real

Consulte [Preparación empresarial](enterprise-readiness.md) para ver la lista de controles que debe completarse antes de presentar las sondas de ejecución como evidencias para equipos o empresas.

<a id="test-coverage"></a>
## Cobertura de pruebas

Comandos principales de validación:

```powershell
python -m unittest discover -s tests -v
python -m ruff check src tests
python -m mypy src
```

Prueba de humo útil:

```powershell
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --runs-dir runs/red-tool-smoke
python -m nullstate report --runs-dir runs/red-tool-smoke
```

La ejecución de humo debe mostrar:

- un hallazgo antes de la remediación
- `Red before: success`
- `Red after: blocked`
- dos eventos `red-tool` en `events.jsonl`
