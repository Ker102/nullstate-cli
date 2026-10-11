<a id="cicd"></a>
# CI/CD

<a id="when-nullstate-runs"></a>
## Quando executa

Pretende participar de três ciclos de segurança:

1. **CI de PR:** ao mudar Terraform, CloudFormation, Bicep, Helm, política ou infraestrutura. Analisa proposto, compara baseline, opcionalmente valida ambiente descartável, publica SARIF e falha por severidade.
2. **Após implantação:** depois do sucesso ou evento relevante do provedor. Atualiza estado observado, detecta drift e valida caminhos afetados. Sondagens destrutivas ficam fora de produção.
3. **Garantia agendada:** detecta alterações manuais, recursos não gerenciados, drift de permissões, serviços expostos e caminhos fora do Git.

CI pergunta se é seguro fazer merge; pós-deploy se atingiu estado esperado; agendamento se houve drift após revisão.

CI cliente pode fornecer identidade AWS/Azure somente leitura e modelo privado ou credenciais gerenciadas. Futuro Cloud pode receber pacotes sanitizados, inferência, histórico, agendas e alertas.

<a id="branching-model"></a>
## Branches

- `main` protegida.
- Branches como `feat/sandbox-localstack`.
- PR em toda alteração.
- Tags `vMAJOR.MINOR.PATCH`.

<a id="pull-request-checks"></a>
## Checks PR

Executa:

- testes unitários
- Ruff lint
- mypy tipos
- pip-audit

<a id="nullstate-ci-export"></a>
## Exportação CI

Sem sandbox, use offline para evidências determinísticas:

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

`--ci` grava `ci-summary.json`, sai `2` quando achados originais atingem `--fail-on-severity`. Limiar `none`, `low`, `medium`, `high`, `critical`. `$schema` para `docs/schemas/ci-summary.schema.json`, valida antes.

`nullstate policy-result` grava `policy-result.json` de execução existente sem repetir.

`nullstate policy validate` sem cenário; com `--output` grava `policy-validation.json`, sai `2` se malformado/inválido.

Demo/upload puro: `--fail-on-severity none`. Gate: `--fail-on-severity high` ou `--fail-on-severity critical`. Falhar e subir SARIF exige `continue-on-error` ou separar exportação/decisão.

Para achados aceitos, crie baseline revisada:

```powershell
python -m nullstate baseline --runs-dir runs/ci --output nullstate-baseline.json
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --ci --baseline-file nullstate-baseline.json --runs-dir runs/ci-next
python -m nullstate policy-result --runs-dir runs/ci-next --baseline-file nullstate-baseline.json
```

`--baseline-file` registra conhecidos/novos em `ci-summary.json`, aplica limiar só aos novos com mesmo contrato validado.

`nullstate sarif` usa mais recente/ID. Grava SARIF 2.1.0, um por achado, com severidade, evidência, correção e endereço IaC lógico. Envie `artifacts/nullstate.sarif` ao GitHub ou ferramenta SARIF.

`nullstate evidence-manifest` cria inventário SHA-256 antes de ticket/suporte/caso. `$schema` para `docs/schemas/evidence-manifest.schema.json`, valida localmente. `--signing-key-env NULLSTATE_EVIDENCE_SIGNING_KEY` assina HMAC-SHA256 com secret CI sem gravar chave. `nullstate evidence-verify` verifica arquivos/assinatura com chave, grava `evidence-verification.json`, sai `2` se faltar, mudar, vier de outro run ou assinatura inválida.

`.github/workflows/nullstate-sarif.yml` roda AWS offline com `--ci --fail-on-severity none` para demo vulnerável enviar via `github/codeql-action/upload-sarif` e guardar artefatos. Gate real usa `high`/`critical`.

Para rigor, prefira bootstrap:

```bash
nullstate init-ci github --scenario aws-public-s3 --iac-path examples/aws-public-s3
```

Grava `.github/workflows/nullstate.yml` e `nullstate-policy.json`. Base `docs/templates/github-actions/nullstate-enforcing.yml`, executa `nullstate run --ci --fail-on-severity high` com `continue-on-error: true` para SARIF, decisão, manifesto, pacote, dry-run; ao final falha se gate falhou. Ajuste `--iac-path`, `--scenario`, `--fail-on-severity` antes de commitar.

Execute `nullstate scrub` antes de anexar publicamente/suporte/caso.

`nullstate upload --dry-run` grava `upload-plan.json` junto ao pacote para futura ingestão sem rede/token valores. `$schema` para `docs/schemas/upload-plan.schema.json`, valida, registra preflight, avisa sem `scrub-report.json`.

<a id="security-checks"></a>
## Segurança

- CodeQL em PR, main e semanalmente.
- Dependency Review em alterações PR.
- Dependabot Python/Actions.

<a id="release-flow"></a>
## Releases

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

Após tag, verifique proveniência e predicado SBOM via GitHub CLI:

```powershell
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli --predicate-type https://spdx.dev/Document/v2.3
```

`release-manifest.json` junto a wheel, sdist, `sbom.spdx.json` indexa checksums; atestações vinculam proveniência/SPDX. SBOM do wheel em `.sbom-venv` limpo captura versões runtime. Valida SPDX, campos, raiz, relações e `pyspdxtools` de `spdx-tools==0.8.5` antes do manifesto/atestação.

Sigstore sem chave por GitHub OIDC assina wheel, sdist, SBOM e manifesto; falha antes da publicação se faltar `.sigstore.json` adjacente.

Antes de tag, `Release` manual com `dry_run=true`: build/validação, não `gh release create`; release só por push de tag.

Cosign: substitua tag em `--certificate-identity` pela versão verificada:

```powershell
$wheel = Get-ChildItem dist\nullstate-*.whl | Select-Object -First 1
cosign verify-blob $wheel.FullName --bundle "$($wheel.FullName).sigstore.json" --certificate-identity "https://github.com/Ker102/nullstate-cli/.github/workflows/release.yml@refs/tags/v0.1.0" --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

<a id="required-repository-settings"></a>
## Configuração obrigatória

Após publicar, configure GitHub:

- proteger `main`
- exigir revisão PR
- exigir PR Checks e CodeQL
- bloquear force pushes
- exigir commits assinados se possível
- habilitar secret scanning/push protection
