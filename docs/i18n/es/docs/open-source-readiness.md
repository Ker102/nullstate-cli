<a id="open-source-readiness-milestones"></a>
# Hitos de preparación de código abierto

Este documento sigue los hitos prácticos antes de promover `nullstate` de alfa a CLI estable de código abierto.

Seguimiento GitHub:

- Hito 1: <https://github.com/Ker102/nullstate-cli/milestone/1>
- Hito 2: <https://github.com/Ker102/nullstate-cli/milestone/3>
- Hito 3: <https://github.com/Ker102/nullstate-cli/milestone/2>

<a id="current-status"></a>
## Estado actual

`nullstate` admite usuarios alfa que entiendan backends experimentales. AWS LocalStack tiene validación en ejecución y comandos restringidos. Azure Blob tiene IaC, remediación, sondeo con manifiesto y cobertura offline, pero ejecución Azure espera habilitación Azure Emulator del usuario/workspace.

<a id="milestone-1-alpha-publication-readiness"></a>
## Hito 1: Preparación para publicar alfa

Objetivo: repo usable y comprensible para evaluadores tempranos.

Estado: mayormente completo.

Criterios:

- [x] README con instalación clara desde fuente y etiqueta preliminar.
- [x] Entrada `nullstate` con alternativa `python -m nullstate`.
- [x] Licencia, contribuciones, conducta y política de seguridad.
- [x] Plantillas GitHub recogen contexto seguro sin pedir secretos.
- [x] Inicio offline sin LocalStack, credenciales Terraform cloud ni modelos.
- [x] Límites de ejecución roja documentados honestamente.
- [x] Informes distinguen runtime observado, simulación determinista y sondeos inconclusos.
- [x] Ejemplo saneado para inspeccionar sin Docker. Issue #29.

<a id="milestone-2-stable-local-sandbox-validation"></a>
## Hito 2: Validación local estable

Objetivo: prueba local fiable para escenarios compatibles.

Estado: AWS listo; Azure bloqueado por habilitación externa.

Criterios:

- [x] S3 LocalStack despliega recursos vulnerables localmente.
- [x] AWS `attack.py` generado lee anónimamente antes/después.
- [x] Informe AWS prueba exploit observado antes y bloqueo después.
- [x] `sandbox up` rechaza éxito si contenedor termina tras iniciar.
- [x] Fallo de habilitación Azure con indicación clara.
- [ ] Resolver habilitación o usar emulador Azure storage compatible.
- [ ] Probar Azure Blob en vivo, lectura anónima antes y bloqueo después.
- [ ] Si no hay Azure LocalStack, implementar Azurite para `azure-public-blob` solo almacenamiento. Issue #30.

<a id="milestone-3-open-source-stable-cli"></a>
## Hito 3: CLI estable de código abierto

Objetivo: CLI instalable, ejecutable y confiable para alcance documentado.

Estado: incompleto.

Criterios:

- [ ] Artefactos instalables sin clonar.
- [ ] Página con wheel, sdist, SBOM, manifiesto, atestaciones y verificación de firmas.
- [x] Recorrido corto de primeros 10 minutos probado desde checkout limpio.
- [x] Paquete y dashboard de demo saneados.
- [x] Todos los escenarios no vivos marcados offline/esqueleto.
- [x] Auditar dependencias y documentar riesgos aceptados.
- [ ] Confirmar dry-run GitHub antes de próxima etiqueta.
- [ ] Confirmar `pip install` de última etiqueta expone `nullstate` en Windows y Linux.

Notas:

- Prueba Windows local pasó el 2026-07-03 con `python scripts/release/install_smoke.py --tag v0.1.0-alpha.2`.
- Falta confirmar Linux en runner o entorno dry-run antes de completar aceptación.

<a id="azure-emulator-decision"></a>
## Decisión Azure Emulator

El fallo actual indica token suficiente para licencia cacheada/de prueba, pero usuario/workspace sin derecho a imagen Azure Emulator. No es permiso cloud Azure: es habilitación/licencia de producto LocalStack.

Opciones:

1. Solicitar a soporte LocalStack Azure Emulator para usuario/workspace de `LOCALSTACK_AUTH_TOKEN`.
2. Azurite para V1 Blob: cubre lectura pública de blobs/contenedores, no plano de control ARM completo.
3. Adaptador emulador pequeño interno solo demo: mínimo riesgo de dependencia, máxima carga de mantenimiento; etiquetarlo simulador, no Azure.
4. Mantener Azure offline hasta emulador y priorizar AWS en vivo.

Vía recomendada:

Use LocalStack Azure si obtiene habilitación rápidamente; si no, Azurite solo Blob y ARM como futuro.
