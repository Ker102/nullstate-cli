<a id="first-10-minutes"></a>
# Primeiros 10 minutos

Este é o caminho mais seguro para novos usuários open source: cenário AWS S3 offline, agentes mock e artefatos locais.

Não exige Docker, LocalStack, endpoint de modelo nem credenciais reais de nuvem.

<a id="1-install-from-a-checkout"></a>
## 1. Instalar de um checkout

```powershell
git clone https://github.com/Ker102/nullstate-cli.git
cd nullstate-cli
python -m pip install -e .
```

Se `nullstate` não estiver em `PATH`, use `python -m nullstate` para os mesmos comandos.

<a id="2-check-the-local-environment"></a>
## 2. Verificar o ambiente local

```powershell
nullstate doctor --offline
nullstate status
```

Resultado esperado:

- CLI imprime a saída de início/status Nullstate
- ausência de Docker, Terraform, LocalStack ou endpoints de modelo é aceitável neste caminho

<a id="3-run-a-deterministic-offline-scan"></a>
## 3. Executar scan determinístico offline

Para inspecionar exemplo sanitizado antes de gerar sua execução:

```powershell
nullstate report --runs-dir examples/sample-runs
nullstate summary --runs-dir examples/sample-runs --json
```

O exemplo inclui `report.md`, `run-bundle.json` e `dashboard.html` para revisar artefatos principais antes do scan.

```powershell
nullstate run examples/aws-public-s3 --offline --mock-agents
```

Resultado esperado:

- um achado de acesso público S3 com severidade alta
- vermelho antes: sucesso
- vermelho depois: bloqueado
- artefatos em `runs/<run-id>/`

<a id="4-open-the-report"></a>
## 4. Abrir o relatório

```powershell
nullstate report
```

Procure:

- resumo de achados
- raciocínio do ataque
- patch de correção
- resultado de validação
- classificação de evidência em execução

<a id="5-build-shareable-local-artifacts"></a>
## 5. Criar artefatos locais compartilháveis

```powershell
nullstate bundle
nullstate dashboard --open
nullstate sarif
nullstate evidence-manifest
nullstate evidence-verify
```

Artefatos gerados:

- `run-bundle.json`
- `dashboard.html`
- `nullstate.sarif`
- `evidence-manifest.json`
- `evidence-verification.json`

<a id="6-scrub-before-sharing"></a>
## 6. Sanitizar antes de compartilhar

```powershell
nullstate scrub
```

Compartilhe a cópia de `scrubbed-runs/`, não o diretório bruto `runs/`.

<a id="7-optional-github-actions-gate"></a>
## 7. Gate GitHub Actions opcional

```powershell
nullstate init-ci github --scenario aws-public-s3 --iac-path examples/aws-public-s3
```

Arquivos gerados:

- `.github/workflows/nullstate.yml`
- `nullstate-policy.json`

Faça commit dos dois para executar o gate offline nos PRs. Ajuste `--iac-path` para seu diretório Terraform antes de usar em repositório real.

<a id="8-optional-live-aws-localstack-path"></a>
## 8. Caminho AWS LocalStack ao vivo opcional

Use somente após configurar Docker e LocalStack:

```powershell
nullstate sandbox up localstack-aws
nullstate sandbox status localstack-aws
nullstate run examples/aws-public-s3 --target localstack-aws --mock-agents
nullstate report
nullstate sandbox down localstack-aws
```

O caminho AWS é o cenário local atualmente comprovado. Implanta o fixture vulnerável no LocalStack AWS, executa sondagem anônima restrita, aplica correção determinística e repete a sondagem.

<a id="current-azure-note"></a>
## Nota Azure atual

Azure Blob permite validação determinística offline, mas LocalStack Azure ao vivo exige habilitação Azure Emulator para workspace/usuário. Se `localstack/localstack-azure-alpha` sair com código `55`, verifique `docker logs localstack-azure`; provavelmente o emulador não está habilitado na conta.
