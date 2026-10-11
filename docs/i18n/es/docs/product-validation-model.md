<a id="product-and-validation-model"></a>
# Modelo de producto y validación

<a id="product-purpose"></a>
## Propósito del producto

Nullstate es una plataforma de validación de rutas de ataque en la nube respaldada por evidencias. Correlaciona la infraestructura como código con el estado observado de AWS y Azure, razona sobre las relaciones entre redes, identidades, servicios y datos, valida rutas de ataque seleccionadas dentro de entornos controlados, aplica remediaciones y vuelve a ejecutar el ataque.

El producto no pretende exigir una representación perfecta en Terraform de toda una cuenta de nube. IaC describe la configuración prevista y gestionada, mientras que el descubrimiento de solo lectura describe la realidad desplegada. Nullstate debería combinar ambos en un grafo de entorno normalizado y conservar el origen y la confianza de cada relación.

El producto de código abierto debería funcionar primero como un framework local de validación DevSecOps para personas, trabajos de CI y agentes de programación. `nullstate summary --json` proporciona a los agentes un resultado compacto de la ejecución en lugar de obligarlos a analizar informes Markdown, mientras que `nullstate context validate` y `nullstate context summary --json` definen un contrato seguro de contexto de nube de solo lectura antes de incorporar recolectores en vivo.

<a id="environment-graph"></a>
## Grafo del entorno

El grafo del entorno debería aceptar:

- Terraform, CloudFormation, exportaciones de CDK, Bicep, ARM y datos de planes/estado del proveedor.
- Inventario de recursos de AWS y Azure de solo lectura.
- Roles IAM, asignaciones de Azure RBAC, identidades administradas, relaciones de confianza e identidades de cargas de trabajo.
- Identidades de agentes IA, plantillas de identidad de agentes, identidades de cargas de trabajo de agentes, contexto delegado de usuario, identidades de herramientas y relaciones con credenciales posteriores.
- Endpoints públicos, redes virtuales, grupos de seguridad, NSG, rutas, gateways, endpoints privados y peering.
- Configuración de almacenamiento, bases de datos, gestión de secretos, cómputo, serverless, contenedores y Kubernetes.
- Hallazgos de seguridad nativos, logs de actividad, logs de flujo, logs de auditoría y metadatos de runtime seleccionados.
- Clasificación opcional de datos proporcionada por el usuario o inferida a partir de metadatos seguros y fixtures sintéticos.

El grafo no necesita clonar todos los recursos. Debe identificar las rutas relevantes para la seguridad y crear un gemelo mínimo de la ruta de ataque que contenga solo las relaciones necesarias para probar una hipótesis.

La vista previa actual del manifiesto de contexto es deliberadamente solo local:

```bash
nullstate context validate examples/cloud-context/aws-readonly-context.json
nullstate context summary examples/cloud-context/aws-readonly-context.json --json
```

Valida la estructura de los metadatos de proveedor, cuenta, identidad, recursos, exposición pública y clasificación de datos sin solicitar credenciales de nube. Los futuros recolectores deberían emitir este contrato usando identidades de nube de solo lectura y de corta duración.

<a id="evaluation-and-product-metrics"></a>
## Evaluación y métricas del producto

El valor de Nullstate para los casos de estudio debería medirse, no solo describirse. El sistema de evaluación actual comienza con benchmarks internos repetibles:

```bash
nullstate eval run examples/eval/iac-security-regression.json --output-dir eval-runs/iac-security-regression
```

El sistema registra la duración, el número de hallazgos, la gravedad máxima, el estado del ataque antes/después, los totales de tokens, el número de artefactos y el estado de cumplimiento/incumplimiento de las expectativas. Este es el primer paso para comparar Nullstate con una revisión basada solo en escáneres, una revisión manual y una revisión realizada por agentes de programación genéricos. Hasta que existan esas líneas base, las afirmaciones deberían limitarse al comportamiento medido de Nullstate, en lugar de hacer afirmaciones generales sobre precisión o ahorro de tiempo.

<a id="identity-aware-attack-analysis"></a>
## Análisis de ataques consciente de la identidad

Un puerto abierto o un contenedor público no constituye todo el hallazgo. Nullstate debería evaluar a qué puede acceder cada perspectiva de atacante autorizada:

| Perspectiva | Ejemplo |
|---|---|
| Externa | Cliente anónimo de internet |
| Usuario del tenant | Usuario de nube autenticado pero con pocos privilegios |
| Desarrollador | Identidad humana con permisos de despliegue o lectura |
| Carga de trabajo de CI | Identidad de GitHub Actions, GitLab o un sistema de compilación |
| Carga de trabajo comprometida | Identidad de VM, contenedor, función o aplicación |
| Rol de nube | Rol AWS IAM, principal de servicio de Azure o identidad administrada |
| Agente IA | Identidad dedicada de agente, identidad de carga de trabajo de agente o rol de runtime de agente |
| Agente delegado | Agente que actúa con autoridad propagada desde un usuario humano |
| Actor lateral | Principal obtenido mediante un paso anterior de la ruta de ataque |

Cada resultado observado debería registrar el principal, los permisos asumidos, el método de autenticación, el objetivo, los datos o la capacidad alcanzados, las evidencias de comandos y la confianza.

<a id="ai-agents-as-cloud-principals"></a>
## Agentes IA como principales de nube

Los agentes IA interactúan cada vez más con infraestructura, API de nube, servicios internos, almacenes de datos, sistemas de tickets, repositorios de código fuente y herramientas de despliegue. Pueden operar mediante:

- una identidad dedicada creada específicamente para el agente
- un principal de servicio convencional, una identidad administrada, un rol IAM o una identidad de carga de trabajo
- una identidad de runtime o de herramienta compartida por varios agentes
- autoridad delegada propagada desde un usuario humano
- credenciales adquiridas para herramientas posteriores o servicios de terceros

Estos modos no deben reducirse a una única cuenta de servicio genérica. Nullstate debería representar al agente, el runtime, la herramienta, el usuario delegado, las credenciales y el servicio objetivo como nodos separados del grafo. Esto conserva quién inició una acción, los permisos de quién la autorizaron y qué componente podría verse comprometido.

Las rutas de ataque específicas de agentes incluyen:

- inyección de prompts que hace que el agente use indebidamente permisos legítimos de nube
- herramientas, plugins, servidores MCP, memoria o contenido recuperado comprometidos que influyen en las acciones
- autonomía excesiva que permite operaciones destructivas o cambios de privilegios fuera de la tarea prevista
- una ruta de intermediario confundido en la que un usuario no confiable hace que un agente privilegiado actúe en su nombre
- autoridad delegada de usuario que alcanza recursos a los que la identidad propia del agente no podría acceder
- identidades de runtime compartidas que vuelven ineficaces la atribución y el mínimo privilegio
- confianza entre agentes que permite movimiento lateral
- credenciales posteriores de larga duración o de alcance amplio que aumentan el radio de impacto

Nullstate debería evaluar al menos tres vistas de permisos separadas:

1. **Permisos propios del agente:** recursos accesibles usando la identidad propia del agente.
2. **Permisos delegados:** recursos accesibles al actuar en nombre de un usuario o una clase de usuarios específicos.
3. **Permisos de la cadena de herramientas:** recursos accesibles a través de identidades de runtime, plugins, gateways, conectores y credenciales posteriores.

El informe debería explicar la cadena efectiva de permisos e identificar los datos y operaciones expuestos si el agente, sus instrucciones, su memoria o una de sus herramientas se ven comprometidos. La validación segura debería usar prompts sintéticos, datos sintéticos, herramientas controladas y entornos desechables en lugar de intentar inyecciones de prompts no controladas contra agentes de producción.

Para agentes alojados externamente, el análisis de identidad por sí solo es insuficiente. Nullstate también debería evaluar la postura del runtime: vinculación de la carga de trabajo con la identidad, procedencia de los artefactos, digest del despliegue, integridad del host y del runtime, exposición de red, controles de herramientas, registro, revocación, y actualidad y solidez de las evidencias de respaldo. El diseño detallado está en [Confianza de agentes externos y postura del runtime](plans/2026-06-22-external-agent-trust-design.md).

La CLI actual incluye una vista previa determinista inicial de este modelo:

```bash
nullstate agent posture verify examples/agent-trust/external-agent-manifest.json
nullstate agent blast-radius examples/agent-trust/external-agent-manifest.json
```

Estos comandos operan sobre un manifiesto local, no sobre recolectores de proveedores en vivo. Su objetivo es reforzar primero el contrato de datos: las evidencias de postura ausentes, obsoletas o desconocidas deben permanecer visibles, y la autoridad delegada del usuario debe separarse de la identidad propia del agente.

<a id="exposed-data-and-impact"></a>
## Datos expuestos e impacto

Los administradores de nube pueden aceptar deliberadamente un servicio accesible porque creen que no contiene nada crítico. Aun así, Nullstate debería identificar si la ruta expone:

- nombres de objetos, listados de directorios, ID de cuentas, ID de tenants, nombres de host o topología interna
- logs de aplicaciones, copias de seguridad, diagnósticos, artefactos de compilación, mapas de código fuente o paquetes de despliegue
- credenciales, tokens, cadenas de conexión, configuración o referencias a secretos
- datos personales, financieros, regulados, de clientes o propietarios
- capacidades de escritura, eliminación, suplantación, ejecución o cambio de políticas
- información que permite ataques a credenciales, movimiento lateral, escalada de privilegios o ingeniería social dirigida

Los informes deben distinguir entre:

- la configuración sugiere exposición
- se observaron metadatos seguros
- se recuperaron datos sintéticos de evidencia
- se demostró una capacidad privilegiada
- se evitó deliberadamente acceder a contenido sensible de producción

<a id="why-not-attack-production-directly"></a>
## ¿Por qué no atacar directamente la producción?

El descubrimiento de solo lectura y la validación no destructiva con aprobación de alcance limitado pueden ejecutarse contra producción. La explotación autónoma debería realizarse por defecto en un entorno controlado porque:

1. Los exploits pueden modificar, eliminar, corromper o exponer datos reales.
2. Los sondeos pueden provocar limitación de solicitudes, interrupciones, bloqueos de cuentas, cuarentena o activación de la respuesta a incidentes.
3. Las pruebas de IAM pueden crear credenciales persistentes, relaciones de confianza o cambios de privilegios.
4. Las pruebas de exfiltración pueden infringir requisitos de privacidad, contractuales, regulatorios y de residencia de datos.
5. Las dependencias de producción pueden afectar a clientes y terceros fuera del alcance aprobado.
6. La limpieza no puede garantizar la restauración exacta del estado anterior.
7. La validación repetida en CI debe ser determinista y lo bastante segura para ejecutarse sin que un especialista en pruebas de penetración supervise cada ejecución.

El modelo operativo seguro es:

1. Descubrir producción mediante API de proveedores de solo lectura.
2. Construir y priorizar hipótesis de ataque.
3. Ejecutar comprobaciones no destructivas incluidas en una lista de permitidos contra producción solo cuando la política lo permita.
4. Reconstruir la ruta mínima relevante usando datos sintéticos en un entorno desechable.
5. Ejecutar ataques restringidos contra ese entorno.
6. Aplicar remediaciones y volver a ejecutar el mismo ataque.
7. Conservar las evidencias y convertir la ruta demostrada en una prueba de regresión.

<a id="aws-and-azure-first"></a>
## AWS y Azure primero

AWS y Azure deberían ser los primeros proveedores de nube porque cubren una gran parte de la infraestructura empresarial y ambos tienen ecosistemas IaC maduros. Terraform sigue siendo una entrada de primera clase, no un objetivo competidor: Terraform para AWS y Terraform para Azure proporcionan la topología y la configuración previstas, mientras que el descubrimiento del proveedor proporciona el estado en vivo y la deriva no gestionada.

Los adaptadores de proveedores también deberían inventariar los sistemas emergentes de identidad de agentes. Microsoft Entra Agent ID proporciona identidades de agentes especializadas y plantillas de identidad, mientras que Amazon Bedrock AgentCore Identity representa a los agentes mediante mecanismos de identidad de agente/carga de trabajo. Nullstate debería incorporar estas relaciones junto con principales de servicio convencionales, identidades administradas y roles IAM sin asumir que todas las organizaciones usan una plataforma de agentes nativa del proveedor.

La precisión respecto al proveedor debería clasificarse en niveles y hacerse explícita:

| Nivel | Fuente de evidencia | Propósito |
|---|---|---|
| Estático | IaC, planes, políticas y configuración exportada | Análisis rápido antes del despliegue |
| Observado | Inventario y logs del proveedor de solo lectura | Comprender el estado realmente desplegado |
| Emulado | LocalStack, emuladores de servicios, contenedores o gemelos digitales | Validación segura y repetible con límites de fidelidad conocidos |
| Sandbox real | Cuenta AWS o suscripción Azure desechable | Validación de exploits de máxima fidelidad |

Cada informe debería identificar el nivel utilizado. Las evidencias de emuladores nunca deben presentarse como prueba de un comportamiento idéntico del proveedor.

<a id="ci-cloud-event-and-scheduled-execution"></a>
## Ejecución por CI, eventos de nube y programación

Nullstate debería admitir tres desencadenantes complementarios.

<a id="pull-request-and-iac-ci"></a>
### CI de pull requests e IaC

Activarse cuando cambien archivos de Terraform, CloudFormation, Bicep, Helm, políticas u otros archivos de infraestructura relacionados.

El pipeline:

1. Analizar la configuración propuesta antes del despliegue.
2. Comparar los hallazgos con una línea base aprobada.
3. Crear opcionalmente un entorno de validación desechable para cambios de alto riesgo.
4. Ejecutar pruebas de regresión de rutas de ataque seleccionadas.
5. Exportar SARIF, un resultado de política legible por máquinas y artefactos de evidencia.
6. Bloquear la fusión cuando no se cumplan los umbrales de la política.

Este es el ciclo de retroalimentación más rápido e impide que configuraciones vulnerables lleguen a la nube.

<a id="post-deployment-validation"></a>
### Validación posterior al despliegue

Activarse después de un workflow de despliegue exitoso o un evento del proveedor.

Los ejemplos incluyen un trabajo de Terraform apply, un despliegue de CloudFormation, un despliegue de Azure o un evento de nube que indique un cambio de recurso o de política relevante para la seguridad. Nullstate actualiza el grafo observado del entorno, comprueba la deriva y ejecuta solo las validaciones seguras afectadas. La validación potencialmente destructiva se dirige a un sandbox desechable en lugar de al entorno de producción actualizado.

<a id="scheduled-assurance"></a>
### Verificación programada

Ejecutarse cada hora, a diario o semanalmente para detectar cambios manuales en consola, recursos no gestionados, deriva de permisos, endpoints que se vuelven públicos, riesgos aceptados que han quedado obsoletos y rutas de ataque creadas por cambios fuera de Git.

Estos modos resuelven problemas distintos:

- La CI de PR valida el cambio previsto antes del despliegue.
- La validación posterior al despliegue confirma que el estado observado coincide con las expectativas.
- La verificación programada detecta deriva y cambios fuera de los canales habituales.

La plataforma de pago madura puede coordinar los tres modos, conservar el historial, notificar a los equipos y proporcionar inferencia de modelos gestionada. La CLI de código abierto mantiene la capacidad de ejecución local y en CI usando credenciales y endpoints de modelos proporcionados por el cliente.

<a id="provider-references"></a>
## Referencias de proveedores

- [Microsoft Entra Agent ID](https://learn.microsoft.com/en-us/entra/agent-id/)
- [Conceptos de identidad de agentes en Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-identity)
- [Amazon Bedrock AgentCore Identity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity-overview.html)
- [Guía de AWS sobre identidad de agentes y gestión de permisos](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentsec03.html)
