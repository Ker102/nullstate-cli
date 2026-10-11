<a id="contributing"></a>
# Contribuciones

<a id="workflow"></a>
## Flujo de trabajo

Use GitHub flow:

1. Cree un issue o enlace uno existente.
2. Cree una rama: `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>` o `chore/<short-name>`.
3. Abra un pull request estructurado.
4. Espere a CI y a la revisión.
5. Integre mediante squash en `main`.

No haga pushes directos a `main`.

<a id="local-setup"></a>
## Configuración local

```powershell
git clone https://github.com/Ker102/nullstate-cli.git
cd nullstate-cli
python -m pip install -e ".[dev]"
nullstate doctor --offline
```

Si el comando de consola `nullstate` no está en `PATH`, use:

```powershell
python -m nullstate doctor --offline
```

<a id="local-checks"></a>
## Comprobaciones locales

```powershell
python -m pip install -e ".[dev]"
python -m ruff check src tests
python -m mypy src
python -m unittest discover -s tests -v
python -m pip_audit
```

Use `pip_audit` como señal de seguridad, no como sustituto de revisión. Si informa un problema de dependencia, documente si la ruta vulnerable es accesible en `nullstate`.

<a id="commit-style"></a>
## Estilo de commits

Use prefijos de commits convencionales:

- `feat:`
- `fix:`
- `docs:`
- `test:`
- `chore:`

<a id="pull-request-expectations"></a>
## Requisitos de pull requests

Cada PR debe incluir:

- resumen
- evidencias de pruebas
- impacto de seguridad
- actualizaciones de documentación
- capturas o artefactos de ejecución cuando corresponda

<a id="security-expectations"></a>
## Requisitos de seguridad

- No incluya credenciales reales de nube, tokens LocalStack, API keys de modelos, archivos `.env`, estado Terraform ni paquetes de ejecución sin sanear.
- Use `nullstate scrub` antes de compartir públicamente artefactos.
- Mantenga la ejecución de ataques local por defecto. El futuro trabajo contra nube real debe ser explícito, opt-in, controlado por políticas y documentado.
- Si modifica el ejecutor rojo, aplicación de políticas, saneado de artefactos, planificación de subidas, workflow de publicación o controles CI, incluya pruebas específicas.
