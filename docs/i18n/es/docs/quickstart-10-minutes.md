<a id="first-10-minutes"></a>
# Primeros 10 minutos

Este inicio rápido es la vía más segura para nuevos usuarios de código abierto. Usa AWS S3 sin conexión, agentes simulados y artefactos locales.

No requiere Docker, LocalStack, endpoint de modelo ni credenciales reales de nube.

<a id="1-install-from-a-checkout"></a>
## 1. Instalar desde un checkout

```powershell
git clone https://github.com/Ker102/nullstate-cli.git
cd nullstate-cli
python -m pip install -e .
```

Si `nullstate` no está en `PATH`, use `python -m nullstate` para los mismos comandos.

<a id="2-check-the-local-environment"></a>
## 2. Comprobar el entorno local

```powershell
nullstate doctor --offline
nullstate status
```

Resultado esperado:

- la CLI imprime la salida de inicio/estado Nullstate
- se admite que falten Docker, Terraform, LocalStack o endpoints de modelo para esta vía sin conexión

<a id="3-run-a-deterministic-offline-scan"></a>
## 3. Ejecutar un análisis determinista sin conexión

Para inspeccionar un ejemplo saneado antes de generar su ejecución:

```powershell
nullstate report --runs-dir examples/sample-runs
nullstate summary --runs-dir examples/sample-runs --json
```

El ejemplo incluye `report.md`, `run-bundle.json` y `dashboard.html` para revisar los artefactos principales antes de analizar.

```powershell
nullstate run examples/aws-public-s3 --offline --mock-agents
```

Resultado esperado:

- un hallazgo S3 de acceso público de severidad alta
- rojo antes: éxito
- rojo después: bloqueado
- artefactos escritos en `runs/<run-id>/`

<a id="4-open-the-report"></a>
## 4. Abrir el informe

```powershell
nullstate report
```

Busque:

- resumen de hallazgos
- razonamiento del ataque
- parche de remediación
- resultado de validación
- clasificación de evidencia en ejecución

<a id="5-build-shareable-local-artifacts"></a>
## 5. Crear artefactos locales compartibles

```powershell
nullstate bundle
nullstate dashboard --open
nullstate sarif
nullstate evidence-manifest
nullstate evidence-verify
```

Artefactos generados:

- `run-bundle.json`
- `dashboard.html`
- `nullstate.sarif`
- `evidence-manifest.json`
- `evidence-verification.json`

<a id="6-scrub-before-sharing"></a>
## 6. Sanear antes de compartir

```powershell
nullstate scrub
```

Comparta la copia de `scrubbed-runs/`, no el directorio original `runs/`.

<a id="7-optional-github-actions-gate"></a>
## 7. Control opcional de GitHub Actions

```powershell
nullstate init-ci github --scenario aws-public-s3 --iac-path examples/aws-public-s3
```

Archivos generados:

- `.github/workflows/nullstate.yml`
- `nullstate-policy.json`

Incluya ambos archivos en commits para ejecutar el control offline en PR. Ajuste `--iac-path` al directorio Terraform antes de usarlo en un repositorio real.

<a id="8-optional-live-aws-localstack-path"></a>
## 8. Vía opcional AWS LocalStack en vivo

Úsela solo tras configurar Docker y LocalStack:

```powershell
nullstate sandbox up localstack-aws
nullstate sandbox status localstack-aws
nullstate run examples/aws-public-s3 --target localstack-aws --mock-agents
nullstate report
nullstate sandbox down localstack-aws
```

La vía AWS en ejecución es el escenario local actualmente probado. Despliega el fixture vulnerable en LocalStack AWS, ejecuta el sondeo restringido de lectura anónima, aplica remediación determinista y repite el sondeo.

<a id="current-azure-note"></a>
## Nota actual sobre Azure

Azure Blob permite validación determinista sin conexión, pero la validación LocalStack Azure en vivo requiere habilitación Azure Emulator para el usuario/workspace. Si `localstack/localstack-azure-alpha` termina con código `55`, consulte `docker logs localstack-azure`; probablemente Azure Emulator no está habilitado.
