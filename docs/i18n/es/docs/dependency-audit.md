<a id="dependency-audit"></a>
# Auditoría de dependencias

Resultados de auditoría son evidencias de publicación, no una casilla puntual.

<a id="current-result"></a>
## Resultado actual

Última auditoría local:

```text
Date: 2026-07-02
Command: python -m pip_audit . --skip-editable
Tool: pip-audit 2.10.0
Result: No known vulnerabilities found
```

El workflow PR ejecuta el mismo comando tras instalar dependencias de desarrollo.

<a id="policy"></a>
## Política

- Justifique dependencias directas nuevas en PR.
- Fallos bloquean preparación de versión salvo documentar alcance, paquete, explotabilidad, mitigación y fecha prevista de eliminación.
- Omite metadatos editables con `--skip-editable` para centrarse en paquetes externos instalados.
- Los candidatos deben repetir:

```powershell
python -m pip install -e ".[dev]"
python -m pip_audit . --skip-editable
```

<a id="accepted-risk"></a>
## Riesgo aceptado

Actualmente no se documenta riesgo aceptado de dependencias vulnerables.
