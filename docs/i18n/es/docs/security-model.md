<a id="security-model"></a>
# Modelo de seguridad

<a id="assets"></a>
## Activos

| Activo | Importancia | Sensibilidad |
|---|---|---|
| Entrada Terraform | describe infraestructura y posibles secretos | media/alta |
| Artefactos de ejecución | contienen hallazgos, logs, parches y evidencias del modelo | media |
| Clave del endpoint de modelo | permite acceso al LLM | alta |
| Token LocalStack | inicia el emulador LocalStack Azure | alta |
| Estado Terraform | puede contener datos sensibles de infraestructura | alta |

<a id="trust-boundaries"></a>
## Límites de confianza

- Shell del operador a CLI nullstate.
- CLI nullstate a backend de sandbox.
- CLI nullstate a endpoint de modelo.
- Instrucciones del agente a ejecución de herramientas permitidas.
- Artefactos locales a documentación pública del repositorio.

<a id="identities"></a>
## Identidades

- Operador: humano de confianza que ejecuta la CLI.
- Agente rojo: rol atacante parcialmente confiable limitado al sandbox local.
- Agente azul: rol de remediación parcialmente confiable.
- Servidor externo de modelos: confiable solo para el comportamiento del endpoint configurado.
- Ejecutor CI: identidad efímera de automatización con permisos mínimos.
- Agente IA del cliente: principal no humano parcialmente confiable que puede usar identidad propia, identidad de carga, principal de servicio, rol IAM, identidad administrada o autoridad delegada de usuario.
- Identidad de herramienta/runtime: principal separado usado por host, gateway, conector, plugin, servidor MCP o herramienta posterior.

El análisis de identidad debe conservar estas distinciones:

- identidad y permisos propios del agente
- usuario humano o carga que pidió la acción
- autoridad delegada/en nombre de otro
- identidades de runtime y herramientas
- credenciales posteriores y audiencias de tokens
- recurso y operación finales

Si ambas identidades contribuyeron a autorizar, el informe no debe atribuir la acción delegada solo al humano o solo al agente.

Para agentes externos, una identidad federada válida es necesaria pero insuficiente. La autorización de alto impacto debería depender de evidencia en ejecución cuando exista:

- identidad de carga vinculada a atributos de runtime previstos
- digest desplegado coincide con artefacto firmado aprobado
- procedencia de construcción y emisor verificados
- atestación de runtime/hardware vigente y válida donde se requiera
- políticas de red y herramientas coinciden con perfil aprobado
- revocación y auditoría operativas

Clasifique evidencias como verificadas criptográficamente, observadas por proveedor, atestadas por operador, inferidas o desconocidas. No convierta silenciosamente una postura desconocida en confiable.

<a id="network-controls"></a>
## Controles de red

V1 usa por defecto modo offline o endpoints locales tipo LocalStack. La ejecución de nube real queda fuera de alcance por defecto.

Los sondeos apuntan por defecto solo a URLs locales como `offline://...`, `local://...`, `127.0.0.1`, `localhost` o `localhost.localstack.cloud`. Los objetivos HTTP(S) no locales requieren `--allow-live-cloud` explícito y registran aprobación en eventos. Con `run --policy-file`, `allowed_target_hosts` puede exigir hostname exacto o sufijo comodín `*.domain`. Los escenarios integrados siguen siendo locales/offline hasta añadir adaptador real; no describa validación de nube real salvo que objetivo y eventos demuestren ese modo.

<a id="secret-handling"></a>
## Gestión de secretos

- Los secretos se leen de variables de entorno.
- `.env` y estado Terraform se ignoran.
- `.env.example` documenta nombres requeridos sin valores.
- Revisar artefactos es obligatorio antes de publicar casos de estudio, paquetes de soporte, capturas o archivos de demo.
- `nullstate scrub` crea copia redactada antes de subir, compartir soporte o publicar casos.

<a id="container-security"></a>
## Seguridad de contenedores

LocalStack y otros sandboxes son dependencias de runtime, no binarios incluidos. Obtenga imágenes confiables y evite código rojo arbitrario fuera de espacios de ejecución generados.

<a id="red-team-command-execution"></a>
## Ejecución de comandos rojos

El ejecutor V1 está restringido por diseño:

- Solo ejecuta el archivo generado `attack.py`.
- `attack.py` debe estar directamente en el directorio de ejecución.
- Si se usa manifiesto, `attack-manifest.json` también debe estar directamente en ese directorio.
- El comando se inicia con el intérprete Python actual, no una shell arbitraria.
- Solo son entradas dinámicas `--target-url`, `--stage` y ruta del manifiesto generado.
- El log registra comando, stdout, stderr, retorno, URL, etapa, inicio, fin y duración.
- Los sondeos se permiten por plantilla, no se generan por modelo en runtime.
- Mantenga timeouts cortos y captura stdout/stderr acotada antes de subidas empresariales o retención prolongada.

Esto muestra ejecución real contra endpoints locales sin acceso irrestricto del modelo a herramientas.

El endurecimiento empresarial debería añadir:

- política explícita permitida para cada par escenario/backend
- hostnames permitidos para adaptadores HTTP(S) de nube en vivo
- saneador al publicar con reglas de redacción específicas de organización
- control `--allow-live-cloud`, apagado por defecto

<a id="cicd-security"></a>
## Seguridad CI/CD

- Las comprobaciones PR ejecutan pruebas, lint, tipos y auditoría de dependencias.
- CodeQL se ejecuta en PR, pushes y semanalmente.
- Revisión de dependencias en PR.
- Publicación solo por etiquetas semver con atestaciones GitHub de distribuciones y `sbom.spdx.json`.
- Workflows con permisos mínimos.

<a id="data-protection"></a>
## Protección de datos

Revise antes de publicar. No publique tokens, IDs reales de inquilino/suscripción, mapas IP privados ni estado de nube.

<a id="known-risks"></a>
## Riesgos conocidos

- Algunos adaptadores son esqueletos, no backends completos.
- LocalStack Azure requiere configuración externa y token.
- Las métricas offline indican cero tokens porque no se llama a modelos.
- Los scripts son sondeos deliberadamente limitados; exploits más ricos deben quedar permitidos explícitamente y dentro del sandbox.

<a id="future-improvements"></a>
## Mejoras futuras

- SBOM más completo de dependencias resueltas desde lockfiles.
- Reglas organizacionales de redacción más amplias.
- Guardas policy-as-code para herramientas de agentes.
- Aprobación de nube en vivo con intención auditable del operador.
- Inventario y controles por proveedor para identidades de agentes IA, contexto delegado, herramientas y confianza entre agentes.
