<a id="enterprise-readiness"></a>
# Prontidão empresarial

Controles para levar `nullstate` do protótipo local a DevSecOps empresarial, distinguindo o imposto do necessário antes de team pago, cloud ou auto-hospedado.

<a id="current-controls"></a>
## Controles atuais

| Controle | Status | Evidência |
|---|---|---|
| Achados determinísticos | implementado | `src/nullstate/findings.py` |
| Correção determinística | implementado | `src/nullstate/remediation.py` |
| Workspace copiado | implementado | IaC original intacto |
| Executor restrito | implementado | só `attack.py` do run |
| Entradas por manifesto | implementado | `attack-manifest.json` valida cenário, backend, URL, pistas de recursos |
| Logs runtime | implementado | `red-tool` saída/tempo |
| Alvo local | implementado | rejeita HTTP remoto padrão |
| Hashes | implementado | `red-tool` SHA-256 script/manifesto |
| Truncamento | implementado | `red-tool` stdout/stderr |
| Sanitização não destrutiva | implementado | `nullstate scrub` copia/remove dados |
| Preflight upload | implementado | `nullstate upload --dry-run` estado e aviso bruto |
| Contrato upload | implementado | `docs/schemas/upload-plan.schema.json` e validação CLI |
| Classificação | implementado | runtime, inconclusivo, simulação |
| Painel/pacote | implementado | `nullstate dashboard`, `nullstate bundle`, `docs/schemas/run-bundle.schema.json` |
| Política vermelha | implementado | `nullstate policy init`, presets, `run --policy-file` impõem cenário, backend, etapa, argumentos, classificação, host, comando, timeout e saída validados |
| Validação política | implementado | `nullstate policy validate`, `policy-validation.json` opcional |
| Integridade | implementado | `nullstate evidence-manifest` SHA-256 validado, HMAC opcional |
| Verificação | implementado | `nullstate evidence-verify` falta, mudança, cópia, HMAC inválido |
| Proveniência | implementado | tag grava `release-manifest.json` e atesta `dist/*` |
| SBOM | implementado | wheel limpo, `sbom.spdx.json` local/SPDX/atestado |
| Assinatura sem chave | implementado | Sigstore GitHub OIDC |
| Ensaio release | implementado | `workflow_dispatch` sem release |
| Regras versionadas | implementado | `remediation.json` versão, cenário, arquivos, IDs, contrato v1 |

<a id="required-before-enterprise-claims"></a>
## Antes de alegações empresariais

<a id="local-only-enforcement"></a>
### Somente local

Alvos padrão locais:

- `offline://...`
- `local://...`
- `127.0.0.1`
- `localhost`
- `localhost.localstack.cloud`

HTTP não local rejeitado. Nuvem real exige `--allow-live-cloud` explícito, desligado padrão. `events.jsonl` grava aprovação e red-tool estado do gate por comando. `allowed_target_hosts` pode restringir hostname exato ou `*.domain`.

<a id="command-allowlist-policy"></a>
### Comandos permitidos

Manter templates. Política define:

- cenários permitidos
- backends permitidos
- nome do script gerado
- argumentos CLI
- timeout máximo
- bytes stdout/stderr máximos
- classes/hosts permitidos

Modelo explica caminho, não cria shell arbitrário.

`nullstate policy init` gera JSON com `$schema` em `docs/schemas/nullstate-policy.schema.json`, valida antes. `nullstate policy init --scenario <name>` restringe par conhecido, útil CI sem todas as versões preliminares. `nullstate policy validate` verifica antes. `nullstate run --policy-file` impõe cenários, backends, etapas, flags `attack.py`, classes, hosts, IDs, teto timeout/saída antes de `attack.py`. Menor que engine completo, mas contrato futuro.

`nullstate run --ci` grava `ci-summary.json` com decisão, código, limiar, contagens, baseline, ataque antes/depois, validado por `docs/schemas/ci-summary.schema.json`.

<a id="event-schema-hardening"></a>
### Hardening dos eventos

`red-tool` contém metadados iniciais:

- `schema_version`
- `command_policy_id`
- `attack_script_sha256`
- `manifest_sha256`

Adicionar políticas mais ricas com o tempo; já inclui:

- `stdout_truncated`
- `stderr_truncated`

Também inclui:

- `live_cloud_allowed`
- `target_classification`, com `external-http` se gate explícito

Reproduzível/auditável em CI, suporte, compliance.

`nullstate evidence-manifest` inventaria SHA-256/tamanhos compartilháveis, exclui workspaces, internos Terraform, cache Python, manifesto próprio, verificação. `$schema` em `docs/schemas/evidence-manifest.schema.json`, valida. `--signing-key-env` usa ambiente HMAC-SHA256 sem chave escrita. `nullstate evidence-verify` recalcula, grava `evidence-verification.json`, sai `2` por falta, mudança, outra identidade de run ou assinatura.

Tags gravam `release-manifest.json` e `sbom.spdx.json` do wheel limpo. Estrutura/`pyspdxtools` antes de atestar. GitHub vincula proveniência/SPDX a `dist/*`; Sigstore `.sigstore.json` adjacentes wheel, sdist, SBOM, manifesto. Supply chain é diferente do HMAC de run.

`dry_run=true` manual ensaia build, validação, atestação, assinatura e pacotes sem release GitHub.

`remediation.json` ao lado de `remediation.patch` registra versão, cenário, mudança, arquivos, IDs. `$schema` em `docs/schemas/remediation-metadata.schema.json` validado antes de consumir para vincular patch ao contrato.

`run-bundle.json` validado localmente, `$schema` em `docs/schemas/run-bundle.schema.json`; `nullstate bundle` falha antes se top-level inválido.

Painel exibe achados, regras, esquema, inventário, timeline, trecho. Continua único usuário/arquivo; histórico team, RBAC, agendamento, compliance são pagos.

<a id="artifact-scrubbing"></a>
### Sanitização

Antes de publicar/upload/anexar, `nullstate scrub` copia e remove:

- tokens LocalStack
- keys de modelo
- IDs de conta cloud
- IDs Azure tenant/assinatura
- endpoints/IPs privados
- valores Terraform state
- credenciais provider
- prompts brutos com contexto cliente

`scrub-report.json` lista arquivos e regras aplicadas.

`nullstate upload --dry-run` verifica `scrub-report.json`, registra `preflight.scrub` em `upload-plan.json`, `$schema` em `docs/schemas/upload-plan.schema.json` validado. Bruto permitido para plano local, mas `upload_recommended: false` e aviso.

<a id="evidence-classification"></a>
### Evidência

Evite exagero. Labels:

- `runtime exploit observed`: saída comprova acesso objeto/blob.
- `runtime probe did not observe exploit`: alvo alcançado, após correção bloqueado/indisponível.
- `runtime probe inconclusive`: emulador/rota/runtime impediu prova.
- `offline deterministic simulation`: nenhuma sondagem ao vivo.

« Explorado » exige comando observado ou simulação offline explícita.

<a id="near-term-readiness-tasks"></a>
## Tarefas próximas

1. Azure ao vivo e limitações documentadas.
2. Adaptadores reais só com allowlists e aprovação.

<a id="commercial-boundary"></a>
## Fronteira comercial

CLI aberta mantém local/offline, LocalStack, relatórios, pacotes, painel individual. Pago para governança:

- histórico central
- RBAC/audit
- policy-as-code
- modelos gerenciados
- suporte bundle
- exports compliance
- scans/alertas agendados
- deploy privado
