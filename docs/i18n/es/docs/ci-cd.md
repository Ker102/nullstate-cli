<a id="cicd"></a>
# CI/CD

<a id="when-nullstate-runs"></a>
## Cuándo se ejecuta Nullstate

Se pretende participar en tres ciclos de seguridad:

1. **CI de pull requests:** al cambiar Terraform, CloudFormation, Bicep, Helm, políticas o archivos relacionados. Analiza estado propuesto, compara baseline, opcionalmente valida rutas en entorno desechable, publica SARIF y falla según severidad.
2. **Validación posdespliegue:** tras despliegue correcto o evento del proveedor sobre cambio relevante. Actualiza estado observado, detecta desviaciones y valida rutas afectadas. Los sondeos destructivos permanecen fuera de producción.
3. **Garantía programada:** periódicamente detecta cambios manuales, recursos no gestionados, deriva de permisos, nuevos servicios expuestos y rutas creadas fuera de Git.

CI pregunta si el cambio es seguro para integrar; posdespliegue si el entorno alcanzó el estado previsto; garantía programada si ha cambiado desde la última revisión.

CI del cliente puede aportar identidad AWS/Azure de solo lectura y endpoint privado o credenciales de modelo administrado. Una futura integración Nullstate Cloud puede recibir paquetes saneados, dar inferencia administrada, conservar historial y coordinar horarios/alertas.

<a id="branching-model"></a>
## Modelo de ramas

- `main` está protegida.
- Trabajo en ramas como `feat/sandbox-localstack`.
- Todos los cambios requieren PR.
- Versiones etiquetadas `vMAJOR.MINOR.PATCH`.

<a id="pull-request-checks"></a>
## Comprobaciones PR

El workflow ejecuta:

- pruebas unitarias
- lint Ruff
- tipos mypy
- auditoría pip-audit

<a id="nullstate-ci-export"></a>
## Exportación CI Nullstate

Sin sandbox, use offline para evidencias deterministas de PR:

```powershell
python -m nullstate policy validate nullstate-policy.json --output artifacts/policy-validation.json
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --ci --fail-on-severity none --runs-dir runs/ci
python -m nullstate policy-result --runs-dir runs/ci --fail-on-severity high
python -m nullstate sarif --runs-dir runs/ci --output artifacts/nullstate.sarif
python -m nullstate evidence-manifest --runs-dir runs/ci --output artifacts/evidence-manifest.json
python -m nullstate evidence-verify --runs-dir runs/ci --manifest artifacts/evidence-manifest.json --output artifacts/evidence-verification.json
python -m nullstate bundle --runs-dir runs/ci
python -m nullstate upload --runs-dir runs/ci --dry-run
```

`--ci` escribe `ci-summary.json` y sale con código `2` cuando hallazgos originales alcanzan `--fail-on-severity`. Umbrales: `none`, `low`, `medium`, `high`, `critical`. Incluye puntero `$schema` a `docs/schemas/ci-summary.schema.json` y se valida antes de escribir.

`nullstate policy-result` escribe `policy-result.json` desde ejecución existente para decisión JSON independiente sin repetir escenario.

`nullstate policy validate` valida política roja sin ejecutar. Con `--output` escribe `policy-validation.json`; código `2` para archivo malformado/inválido.

Use `--fail-on-severity none` para demos o solo subida, `--fail-on-severity high` o `--fail-on-severity critical` para imponer controles. Para fallar y subir SARIF, maneje `continue-on-error` explícitamente o separe exportación y decisión.

Si hay hallazgos aceptados, cree baseline de una ejecución revisada:

```powershell
python -m nullstate baseline --runs-dir runs/ci --output nullstate-baseline.json
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --ci --baseline-file nullstate-baseline.json --runs-dir runs/ci-next
python -m nullstate policy-result --runs-dir runs/ci-next --baseline-file nullstate-baseline.json
```

Con `--baseline-file`, `ci-summary.json` cuenta conocidos/nuevos y evalúa severidad solo sobre nuevos, conservando contrato validado.

`nullstate sarif` lee última ejecución o ID indicado. Escribe SARIF 2.1.0, un resultado por hallazgo, conservando severidad, evidencias, guía y dirección IaC como ubicación lógica. Suba `artifacts/nullstate.sarif` a GitHub code scanning u otra herramienta compatible.

`nullstate evidence-manifest` crea inventario SHA-256 compartible antes de tickets, soporte o archivos de caso. Incluye `$schema` a `docs/schemas/evidence-manifest.schema.json` y validación local. Añada `--signing-key-env NULLSTATE_EVIDENCE_SIGNING_KEY` para firmar HMAC-SHA256 con secreto CI sin escribir clave. `nullstate evidence-verify` compara archivos actuales, verifica firma si se aporta variable, escribe `evidence-verification.json` y sale `2` si falta artefacto, cambió, viene de otra ejecución o firma inválida.

`.github/workflows/nullstate-sarif.yml` es el primer ejemplo Actions: AWS S3 offline con `--ci --fail-on-severity none` permite subir demo vulnerable mediante `github/codeql-action/upload-sarif` y conserva artefactos. Cambie a `high` o `critical` para imponer control sobre IaC real.

Para un workflow más estricto, prefiera inicialización:

```bash
nullstate init-ci github --scenario aws-public-s3 --iac-path examples/aws-public-s3
```

Escribe `.github/workflows/nullstate.yml` y `nullstate-policy.json` específico. Basado en `docs/templates/github-actions/nullstate-enforcing.yml`, ejecuta `nullstate run --ci --fail-on-severity high` con `continue-on-error: true` para generar SARIF, policy-result, manifiesto, paquete y dry-run; al final falla si falló el control. Ajuste `--iac-path`, `--scenario`, `--fail-on-severity` antes de incluir archivos en commits.

Ejecute `nullstate scrub` antes de adjuntar paquetes/informes públicamente o a soporte/casos.

`nullstate upload --dry-run` escribe `upload-plan.json` junto al paquete; prepara futura ingestión sin tráfico ni valores de token. Incluye `$schema` a `docs/schemas/upload-plan.schema.json`, valida localmente, registra preflight y advierte si falta `scrub-report.json`.

<a id="security-checks"></a>
## Comprobaciones de seguridad

- CodeQL analiza Python en PR, pushes main y semanalmente.
- Dependency Review revisa cambios de dependencias en PR.
- Dependabot monitoriza Python y GitHub Actions.

<a id="release-flow"></a>
## Flujo de publicación

```text
manual workflow_dispatch dry_run=true
-> release workflow rehearses package build, SBOM validation, attestations, signing, and signature checks
-> no GitHub release is created
merge to main
-> update CHANGELOG.md
-> tag v0.1.0
-> release workflow builds package
-> release workflow smoke-installs the built wheel and runs nullstate doctor --offline
-> sbom.spdx.json records the installed wheel and runtime dependency versions
-> SBOM validation checks required package fields and root-package relationships
-> SPDX tools validate the generated SBOM document
-> release-manifest.json records SHA-256 digests and sizes
-> GitHub artifact attestations bind provenance and SBOM data to dist/*
-> Sigstore keyless signing writes .sigstore.json bundles beside primary release assets
-> GitHub release created with generated notes
```

Tras publicar etiqueta, verifique procedencia y predicado SBOM con GitHub CLI:

```powershell
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli --predicate-type https://spdx.dev/Document/v2.3
```

`release-manifest.json` acompaña wheel, sdist y `sbom.spdx.json` como índice de checksums. Atestaciones GitHub vinculan procedencia y SBOM SPDX a recursos. SBOM procede del wheel instalado en `.sbom-venv` limpio y registra versiones runtime. El workflow valida versión SPDX, campos, paquete raíz, relaciones y ejecuta `pyspdxtools` de `spdx-tools==0.8.5` antes del manifiesto/atestación.

Después firma wheel, sdist, SBOM y manifiesto con Sigstore sin clave vía GitHub OIDC. Falla antes de publicar si falta paquete `.sigstore.json` adyacente de algún artefacto principal.

Use `Release` manual con `dry_run=true` antes de etiquetar: ejecuta construcción/validación pero omite `gh release create`, reservado a pushes de etiquetas.

Verifique firma descargada con Cosign y sustituya la etiqueta de `--certificate-identity`:

```powershell
$wheel = Get-ChildItem dist\nullstate-*.whl | Select-Object -First 1
cosign verify-blob $wheel.FullName --bundle "$($wheel.FullName).sigstore.json" --certificate-identity "https://github.com/Ker102/nullstate-cli/.github/workflows/release.yml@refs/tags/v0.1.0" --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

<a id="required-repository-settings"></a>
## Configuración requerida

Configure en GitHub tras publicar:

- proteger `main`
- exigir revisión PR
- exigir PR Checks y CodeQL
- bloquear force pushes
- exigir commits firmados si es posible
- habilitar secret scanning y protección de pushes
