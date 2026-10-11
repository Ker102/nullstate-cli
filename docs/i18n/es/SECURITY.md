<a id="security-policy"></a>
# Política de seguridad

<a id="supported-versions"></a>
## Versiones compatibles

`nullstate` es anterior a 1.0. Las correcciones de seguridad se aplican a la rama `main` más reciente y a la última etiqueta preliminar cuando deban publicarse para evaluadores.

| Versión | Soporte |
|---|---|
| `main` | sí |
| última versión preliminar | sí |
| versiones preliminares anteriores | según posibilidades |

<a id="reporting-a-vulnerability"></a>
## Informar una vulnerabilidad

No abra issues públicos sobre vulnerabilidades explotables de nullstate. Contacte al mantenedor en privado o use informes privados de vulnerabilidades de GitHub si están habilitados. Publique detalles solo cuando exista una corrección o mitigación.

<a id="security-boundaries"></a>
## Límites de seguridad

nullstate está diseñado para probar sandboxes locales intencionadamente vulnerables. No debe apuntar a producción salvo que el operador sea propietario del entorno y entienda el riesgo.

Valores predeterminados V1:

- sin ejecución en Azure real por defecto
- sandboxes LocalStack/Docker solo al iniciarlos explícitamente
- los artefactos son archivos locales
- los secretos se suministran mediante variables de entorno, no archivos versionados
- los sondeos rojos restringidos solo ejecutan `attack.py` generado en el directorio de ejecución
- los objetivos HTTP no locales requieren aprobación explícita del operador y controles de política

<a id="secret-handling"></a>
## Gestión de secretos

Nunca incluya en commits:

- `LOCALSTACK_AUTH_TOKEN`
- API keys de modelos
- credenciales de nube
- estado Terraform
- `.env`
- archivos `.tfvars` reales

Use `.env.example` para la configuración documentada.

Antes de adjuntar artefactos a issues, tickets, casos de estudio o soporte:

```powershell
nullstate scrub
```

Adjunte la copia saneada de `scrubbed-runs/`, no el directorio original `runs/`.
