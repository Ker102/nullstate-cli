<a id="threat-model---nullstate"></a>
# Modelo de amenazas - nullstate

<a id="system-overview"></a>
## Visión del sistema

nullstate es una CLI local-first que analiza IaC, ejecuta o simula ataques en sandbox, usa roles rojo/azul, remedia en un workspace copiado y genera evidencias.

<a id="assets"></a>
## Activos

| Activo | Importancia | Sensibilidad |
|---|---|---|
| Fuente IaC | puede revelar arquitectura y secretos | media/alta |
| Workspace de ejecución | contiene IaC copiado y remediación | media |
| API key de modelo | acceso al endpoint | alta |
| Token LocalStack | acceso a imagen LocalStack Azure | alta |
| Informes | evidencias públicas | baja/media tras sanear |
| Grafo de identidad y delegación | revela permisos, delegaciones, herramientas y sistemas accesibles | alta |
| Memoria y configuración de herramientas | puede contener instrucciones, credenciales, datos recuperados e integraciones confiables | alta |

<a id="trust-boundaries"></a>
## Límites de confianza

- Shell de usuario a CLI.
- CLI a Docker/LocalStack/kind.
- CLI a endpoint de modelo.
- Agente IA a proveedor de identidad, gateway de herramientas, servicio posterior y contexto delegado.
- Script generado a directorio local de ejecución.
- Documentación a internet público.

<a id="actors"></a>
## Actores

| Actor | Objetivo | Confianza |
|---|---|---|
| Operador | validar seguridad IaC local | confiable |
| Atacante externo | abusar de artefactos o sandbox expuesto | no confiable |
| Agente rojo | encontrar ruta en sandbox | parcialmente confiable |
| Agente azul | generar remediación | parcialmente confiable |
| Agente IA cliente | operar recursos con identidad propia o delegada | parcialmente confiable |
| Herramienta/memoria comprometida | influir decisiones o abusar de autoridad | no confiable |
| Dependencia comprometida | ejecutar código malicioso | no confiable |

<a id="threats"></a>
## Amenazas

| Amenaza | Impacto | Probabilidad | Control | Evidencia |
|---|---|---|---|---|
| Alcanzar nube real por accidente | Alto | Media | LocalStack/solo plan por defecto | docs de objetivos CLI |
| Secreto en commit | Alto | Media | `.gitignore`, `.env.example`, SECURITY.md | archivos del repo |
| Agente escapa del sandbox | Alto | Media | comandos permitidos, workspace copiado | módulo sandbox |
| Dependencia comprometida | Alto | Media | Dependabot, pip-audit, revisión | workflows |
| Modelo engañoso | Medio | Alta | detector y validador deterministas | pruebas |
| Agente comprometido abusa de autoridad | Alto | Media | grafo por identidad, mínimo privilegio, separación delegada, validación controlada | futuro adaptador de identidad |
| Agente privilegiado como intermediario confundido | Alto | Media | atribución de solicitante/delegación, políticas, autorización por herramienta | futuro adaptador de identidad |
| Identidad compartida oculta atribución | Alto | Media | evidencia separada de agente/runtime/herramienta donde se soporte | futuro inventario |
| Host externo comprometido con identidad de inquilino válida | Alto | Media | postura, federación breve, gateway, mínimo privilegio, revocación | futuro recolector |
| Postura falsa u obsoleta aceptada | Alto | Media | firma, emisor, tiempos, vigencia y denegación de alto impacto ante fallos | futuro verificador |

<a id="abuse-cases"></a>
## Casos de abuso

- Usuario apunta accidentalmente al estado Terraform de producción.
- Dependencia maliciosa lee variables durante CI.
- Informe contiene token real o endpoint privado.
- Agente rojo propone acciones fuera de LocalStack.
- Contenedor expone puerto inesperadamente.
- Inyección de prompts hace que agente de nube use herramienta legítima con parámetros dañinos.
- Agente para usuario de pocos privilegios conserva/adquiere más permisos de principal de servicio.
- Servidor MCP, conector, plugin, memoria o documento comprometido redirige acciones.
- Varios agentes comparten identidad privilegiada, ocultando quién cambió algo.
- Credencial posterior tiene alcance o duración superior a la tarea.
- Agente externo presenta identidad válida desde host vulnerable y abusa de permisos aprobados.
- Operador interpreta firma de imagen/atestación hardware como garantía de seguridad de toda la aplicación.

<a id="residual-risks"></a>
## Riesgos residuales

- Seguridad Docker depende de máquina del operador.
- Cobertura LocalStack Azure puede diferir de Azure real.
- CI no puede imponer protección de ramas hasta configurarla en GitHub.
- Identidades nativas y delegación evolucionan y requieren inventario/evidencias por proveedor.

<a id="next-improvements"></a>
## Próximas mejoras

- Validar LocalStack Azure en vivo cuando exista habilitación Azure Emulator.
- Añadir adaptadores reales solo con allowlists por proveedor y aprobación.
- Inventario de identidad AWS/Azure con agentes nativos, cargas convencionales, usuarios delegados, herramientas y credenciales posteriores.
- Evidencia de postura externa clasificada explícitamente como verificada, observada, atestada por operador, inferida o desconocida.
