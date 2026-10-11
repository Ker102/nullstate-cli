<a id="technical-walkthrough"></a>
# Passo a passo técnico

Este documento explica como `nullstate` funciona desde o primeiro comando da CLI até o artefato final do relatório. Ele foi escrito para revisores que querem entender o caminho de implementação, os limites de segurança e os pontos de extensão atuais.

<a id="what-nullstate-runs"></a>
## O que o Nullstate executa

`nullstate` é um ciclo de equipe roxa para infraestrutura como código que prioriza a execução local. A implementação atual se concentra em cenários de exposição de armazenamento com Terraform:

- Bloqueio de acesso público do AWS S3 desabilitado
- Acesso público a contêineres do Azure Blob

Ela também inclui estruturas iniciais de cenários offline para Kubernetes, Docker Compose, gêmeos digitais locais e revisão genérica de planos.

A CLI combina três camadas:

1. Lógica de segurança determinística para achados, remediação e validação de aprovação ou falha.
2. Adaptadores de sandbox para alvos de execução locais, como LocalStack.
3. Raciocínio de equipe vermelha e equipe azul assistido por modelos por meio de endpoints compatíveis com OpenAI.

O modelo ajuda no raciocínio e na explicação. Ele não é a fonte de verdade para determinar se a vulnerabilidade existe ou se a remediação funcionou.

<a id="demo-command-flow"></a>
## Fluxo de comandos de demonstração

Fluxo offline típico:

```powershell
nullstate
nullstate status
nullstate run examples/aws-public-s3 --offline
nullstate report
```

Fluxo típico de execução ao vivo com LocalStack AWS:

```powershell
nullstate sandbox up localstack-aws
nullstate sandbox status localstack-aws
nullstate run examples/aws-public-s3 --target localstack-aws
nullstate report
```

Fluxo típico de execução ao vivo com LocalStack Azure:

```powershell
nullstate sandbox up localstack-azure
nullstate sandbox status localstack-azure
nullstate run examples/azure-public-blob --target localstack-azure
nullstate report
```

Quando houver um endpoint de modelo auto-hospedado disponível, use o provedor personalizado e defina um endpoint compartilhado:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_LLM_BASE_URL = "http://127.0.0.1:8000"
```

Ou defina endpoints específicos por papel:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
```

As predefinições de provedores gerenciados podem dispensar a configuração de endpoints para usuários que fornecem suas próprias chaves:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
```

A predefinição `claude` também está disponível pela camada de compatibilidade com o SDK da OpenAI da Anthropic, mas deve ser tratada como experimental até que exista um adaptador nativo do Claude.

<a id="runtime-modes"></a>
## Modos de execução

<a id="offline-mode"></a>
### Modo offline

`--offline` ignora a execução do Terraform e as chamadas ao emulador de nuvem. A CLI usa análise estática de IaC e comportamento determinístico dos cenários. Esse modo é usado para demonstrações repetíveis, testes e desenvolvimento sem Docker, LocalStack ou GPU.

Detalhe importante: `--offline` não desabilita automaticamente as chamadas aos modelos. Se as variáveis de ambiente dos endpoints de modelos estiverem configuradas, as chamadas dos agentes vermelho e azul ainda usarão esses endpoints. Use `--mock-agents` quando o comportamento desejado for totalmente determinístico e sem modelo.

<a id="live-localstack-mode"></a>
### Modo ao vivo com LocalStack

O modo ao vivo copia o projeto Terraform para um espaço de trabalho da execução, executa comandos de automação do Terraform, usa LocalStack como alvo, executa o ciclo vermelho/azul, aplica a remediação no espaço de trabalho copiado e valida novamente.

O diretório original do Terraform não é modificado. A remediação acontece em:

```text
runs/<run-id>/workspace/
```

<a id="model-endpoint-mode"></a>
### Modo de endpoint de modelo

O endpoint de modelo deve expor uma API compatível com OpenAI. Isso permite que a mesma integração da CLI funcione com vLLM local, SGLang, predefinições de provedores gerenciados ou um proxy personalizado.

A resolução do provedor segue esta ordem:

1. opções da CLI ou valores de ambiente específicos por papel
2. opções da CLI ou valores de ambiente compartilhados
3. URL padrão da predefinição do provedor
4. fallback para agente simulado determinístico quando nenhum endpoint está configurado

A predefinição `google` resolve para o endpoint do Gemini compatível com OpenAI. A predefinição `claude` resolve para o endpoint de compatibilidade com o SDK da OpenAI da Anthropic. Os modos `custom` e `openai-compatible` exigem uma URL base, a menos que uma URL específica por papel seja fornecida.

A CLI registra as contagens de tokens do modelo e a latência a partir dos campos `usage` da resposta, quando disponíveis. Ela também tenta coletar `/metrics` no estilo Prometheus do endpoint e grava os snapshots brutos das métricas no diretório da execução.

<a id="end-to-end-execution-path"></a>
## Caminho de execução de ponta a ponta

<a id="1-command-entry"></a>
### 1. Entrada do comando

Ponto de entrada:

```text
src/nullstate/cli.py
```

O comando `run` recebe:

- diretório do Terraform
- backend de destino, ou `auto`
- cenário, ou `auto`
- opções de modo offline ou simulado
- diretório de artefatos da execução
- configurações dos modelos vermelho e azul

Se nenhum comando for fornecido, a CLI exibe a tela inicial com a identidade da marca e os prováveis próximos comandos.

<a id="2-scenario-inference"></a>
### 2. Inferência do cenário

Arquivos relevantes:

```text
src/nullstate/scenario_detection.py
src/nullstate/scenarios.py
```

Quando `--scenario auto` é usado, a CLI inspeciona o diretório de IaC e mapeia a entrada para um cenário conhecido. Por exemplo:

- `examples/aws-public-s3` mapeia para `aws-public-s3`
- `examples/azure-public-blob` mapeia para `azure-public-blob`

A definição do cenário escolhe o backend de sandbox padrão. Os usuários ainda podem sobrescrever essa escolha com `--target`.

<a id="3-sandbox-backend-selection"></a>
### 3. Seleção do backend de sandbox

Arquivo relevante:

```text
src/nullstate/sandbox.py
```

Os backends de sandbox definem:

- nome do backend
- tipo de IaC de destino
- modo de execução
- imagem Docker
- comandos de inicialização e parada
- sondas de execução

Os backends atuais incluem:

| Backend | Finalidade |
|---|---|
| `localstack-aws` | Execução ao vivo de cenários de armazenamento no estilo AWS |
| `localstack-azure` | Execução ao vivo de cenários de armazenamento no estilo Azure |
| `kind-kubernetes` | Estrutura inicial de cenário do Kubernetes |
| `docker-compose` | Estrutura inicial de gêmeo digital com Docker Compose |
| `microvm-onprem` | Estrutura inicial de gêmeo digital local |
| `plan-only` | Modo de análise sem execução |

`nullstate sandbox up` inicia o backend. `nullstate sandbox status` verifica o Docker e a acessibilidade HTTP quando aplicável.

<a id="4-run-workspace-creation"></a>
### 4. Criação do espaço de trabalho da execução

A CLI cria um novo diretório de execução:

```text
runs/<run-id>/
```

Ela copia o diretório de entrada do Terraform para:

```text
runs/<run-id>/workspace/
```

Isso mantém o projeto original intacto. O estado do Terraform, `.terraform`, os planos em cache e os diretórios de execução são excluídos da cópia.

<a id="5-terraform-plan-loading"></a>
### 5. Carregamento do plano do Terraform

Arquivo relevante:

```text
src/nullstate/terraform.py
```

No modo ao vivo, o fluxo do Terraform segue comandos adequados para automação:

```text
terraform init -input=false
terraform plan -out=tfplan -input=false
terraform show -json tfplan
```

No modo offline, a CLI usa um analisador estático do Terraform para as fixtures de demonstração compatíveis. Isso mantém os testes e as demonstrações reproduzíveis mesmo sem dependências externas de execução.

Os resultados dos comandos do Terraform são gravados em:

```text
runs/<run-id>/events.jsonl
```

<a id="6-finding-detection"></a>
### 6. Detecção de achados

Arquivo relevante:

```text
src/nullstate/findings.py
```

O detector determinístico identifica as configurações de risco compatíveis. Exemplos:

- O contêiner do Azure Blob tem `container_access_type = "blob"` ou `"container"`
- A conta de armazenamento do Azure permite itens públicos aninhados
- Os controles de bloqueio de acesso público do AWS S3 estão desabilitados

Os achados são gravados como JSON estruturado:

```text
runs/<run-id>/findings.json
```

Esses dados determinísticos dos achados são a fonte de verdade para o restante da execução.

<a id="7-red-team-model-reasoning"></a>
### 7. Raciocínio do modelo da equipe vermelha

Arquivo relevante:

```text
src/nullstate/agents.py
```

O agente vermelho recebe instruções internas e evidências do cenário. O usuário não fornece prompts manualmente ao modelo durante a execução.

O modelo vermelho retorna raciocínio sobre o ataque, por exemplo:

- caminho de leitura anônima de objetos do S3
- caminho de leitura anônima de contêineres do Azure Blob
- prováveis evidências a coletar

Se nenhum endpoint estiver configurado, o papel recorre a uma saída simulada determinística.

<a id="8-constrained-attack-script-execution"></a>
### 8. Execução restrita do script de ataque

Arquivos relevantes:

```text
src/nullstate/attack.py
src/nullstate/attack_runner.py
```

`nullstate` grava um artefato de ataque gerado:

```text
runs/<run-id>/attack.py
runs/<run-id>/attack-manifest.json
```

O manifesto registra o cenário, o backend, a URL de destino e as indicações de recursos que as sondas do cenário podem usar sem dar ao modelo poder para construir comandos arbitrários. Ele inclui um ponteiro `$schema` para `docs/schemas/attack-manifest.schema.json`, e `nullstate run` valida o manifesto antes da execução restrita das sondas.

Em seguida, o executor restrito executa apenas esse script gerado. Ele impõe estes limites:

- o nome do script deve ser exatamente `attack.py`
- o script deve estar diretamente dentro do diretório da execução atual
- a execução usa o interpretador Python atual
- nenhum comando de shell arbitrário é aceito
- as entradas dinâmicas se limitam a `--target-url`, `--stage` e ao `attack-manifest.json` gerado no diretório da execução

O executor registra evidências dos comandos antes e depois da remediação:

```json
{
  "phase": "red-tool",
  "message": "Allowlisted attack command completed",
  "data": {
    "command": ["python", "attack.py", "--target-url", "...", "--stage", "before", "--manifest", "..."],
    "target_url": "...",
    "stage": "before",
    "returncode": 0,
    "stdout": "...",
    "stderr": "",
    "started_at": "...",
    "ended_at": "...",
    "duration_seconds": 0.123
  }
}
```

Isso fornece ao relatório evidências de comandos reais e evita acesso irrestrito do agente vermelho às ferramentas.

Salvaguardas empresariais para essa camada:

- A política de comandos é baseada em modelos de cenários. O modelo pode raciocinar sobre o caminho de ataque, mas não pode escolher um comando de shell arbitrário.
- `nullstate policy init` cria um arquivo de política com referência a esquema e o valida antes de gravar; `policy init --scenario <name>` cria uma predefinição mais restrita para um par de cenário/backend. `run --policy-file` impõe, antes da execução, os cenários, backends e estágios permitidos, as opções do `attack.py` gerado, as classificações de destino, as listas de hosts de destino permitidos, os IDs das políticas de comandos e os limites de tempo e tamanho de saída.
- `nullstate policy validate` verifica um arquivo de política sem executar um cenário e pode gravar `policy-validation.json` como evidência para CI.
- Os alvos de execução permanecem endpoints de sandbox locais, a menos que `--allow-live-cloud` seja explicitamente fornecido e registrado.
- Os eventos `red-tool` incluem uma versão do esquema de comandos e hashes de reprodutibilidade para o `attack.py` gerado e o manifesto.
- A saída padrão e a saída de erro das sondas devem ser limitadas antes de upload, anexação a tickets ou retenção de evidências a longo prazo.
- Os relatórios devem distinguir evidências observadas em execução de simulação determinística e de sondas inconclusivas no emulador.

<a id="9-deterministic-remediation"></a>
### 9. Remediação determinística

Arquivo relevante:

```text
src/nullstate/remediation.py
```

O modelo azul explica a remediação, mas o patch em si é produzido pela lógica de remediação determinística.

Para exposição do Azure Blob, a remediação define:

```hcl
allow_nested_items_to_be_public = false
container_access_type           = "private"
```

Para exposição do AWS S3, a remediação define os controles de bloqueio de acesso público como `true`:

```hcl
block_public_acls       = true
block_public_policy     = true
ignore_public_acls      = true
restrict_public_buckets = true
```

O diff é gravado em:

```text
runs/<run-id>/remediation.patch
```

<a id="10-re-plan-and-validation"></a>
### 10. Novo plano e validação

Após a remediação, a CLI carrega novamente o espaço de trabalho remediado. No modo ao vivo, ela executa as etapas de planejamento e aplicação do Terraform sobre o espaço de trabalho copiado. No modo offline, ela analisa novamente os arquivos atualizados.

O detector é executado novamente. Se o achado desapareceu, a simulação determinística do ataque retorna:

```text
Red after: blocked
```

O script de ataque restrito também é executado uma segunda vez com:

```text
--stage after
```

A saída desse comando após a remediação é registrada como outro evento `red-tool`.

<a id="11-report-and-metrics"></a>
### 11. Relatório e métricas

Arquivos relevantes:

```text
src/nullstate/report.py
src/nullstate/metrics.py
```

Cada execução grava:

| Artefato | Finalidade |
|---|---|
| `events.jsonl` | Linha do tempo completa dos eventos |
| `findings.json` | Achados de vulnerabilidades estruturados |
| `attack.py` | Artefato de ataque restrito gerado |
| `attack-manifest.json` | Cenário, backend, URL de destino e indicações de recursos validados por esquema para sondas restritas |
| `remediation.patch` | Diff da remediação do Terraform |
| `remediation.json` | Metadados do conjunto de regras de remediação determinística validados por esquema |
| `metrics.json` | Chamadas aos modelos, contagens de tokens, latência, métricas dos endpoints |
| `ci-summary.json` | Veredito de CI legível por máquina e validado por esquema quando `--ci` é usado |
| `policy-result.json` | Decisão de política JSON independente para uma execução existente |
| `report.md` | Resumo legível por humanos |
| `evidence-manifest.json` | Inventário SHA-256 de evidências de execução compartilháveis quando `nullstate evidence-manifest` é usado |
| `evidence-verification.json` | Resultado da verificação de um manifesto quando `nullstate evidence-verify` é usado |
| `upload-plan.json` | Plano de upload sem rede quando `nullstate upload --dry-run` é usado |
| `workspace/` | Espaço de trabalho de IaC copiado e remediado |

`nullstate report` abre o relatório mais recente por padrão, incluindo relatórios aninhados em diretórios de execução nomeados.

`remediation.json` inclui um ponteiro `$schema` para `docs/schemas/remediation-metadata.schema.json`, e os metadados de remediação gerados são validados antes de serem usados por relatórios, bundles e artefatos da execução.

`nullstate bundle` grava `run-bundle.json`, o contrato portátil de evidências para dashboards locais, uploads de CI, bundles de suporte e a futura ingestão do Nullstate Cloud. O bundle inclui um ponteiro `$schema` para `docs/schemas/run-bundle.schema.json`, e a CLI valida sua estrutura antes de gravar. O bundle também inclui os metadados de `remediation.json` quando disponíveis, para que ferramentas posteriores possam exibir a versão do conjunto de regras de remediação e os IDs das regras.

`nullstate dashboard` grava `dashboard.html`, um dashboard local gratuito de uma única execução que pode ser aberto sem login na nuvem. Ele resume os achados, os metadados de remediação, os metadados do esquema do bundle, o inventário de artefatos, a linha do tempo das evidências e o trecho do relatório.

`nullstate sarif` grava `nullstate.sarif`, uma exportação SARIF 2.1.0 com um resultado por achado para uploads de CI e de análise de código.

`nullstate run --ci` grava `ci-summary.json` e encerra com o código `2` quando os achados originais da execução atingem ou superam `--fail-on-severity`. O resumo inclui um ponteiro `$schema` para `docs/schemas/ci-summary.schema.json` e é validado antes de gravar, fornecendo à CI um controle estável de política sem alterar o relatório humano.

`nullstate baseline` grava uma linha de base JSON das identidades dos achados. Quando `nullstate run --ci --baseline-file` é usado, os achados conhecidos da linha de base continuam visíveis, mas o limite de falha da CI é avaliado apenas contra novos achados.

`nullstate policy-result` grava o mesmo tipo de decisão de limite e linha de base para uma execução existente sem executar novamente o cenário.

`nullstate evidence-manifest` grava `evidence-manifest.json`, um inventário determinístico de integridade para artefatos de execução compartilháveis. O manifesto inclui um ponteiro `$schema` para `docs/schemas/evidence-manifest.schema.json`, e a CLI valida sua estrutura antes de gravar. Ele exclui espaços de trabalho copiados, arquivos internos do Terraform, caches do Python, o próprio arquivo do manifesto e a saída da verificação. Use `--signing-key-env` para anexar uma assinatura de evidências HMAC-SHA256 com chave compartilhada a partir de um segredo do ambiente; isso é assinatura de evidências da execução, não proveniência de pacotes com chave pública.

`nullstate evidence-verify` grava `evidence-verification.json` após recalcular os hashes e os tamanhos dos arquivos dos artefatos registrados. Ele verifica apenas os artefatos listados no manifesto, ignora novos arquivos não relacionados, verifica assinaturas HMAC quando `--signing-key-env` é fornecido e encerra com o código `2` quando um artefato registrado está ausente, foi alterado, foi copiado de outra execução ou tem uma assinatura inválida.

`nullstate upload --dry-run` grava `upload-plan.json`, atualiza `run-bundle.json`, registra o endpoint pretendido e a variável de ambiente do token e confirma se o token existe sem armazenar seu valor. O plano inclui um ponteiro `$schema` para `docs/schemas/upload-plan.schema.json`, e a CLI valida sua estrutura antes de gravar. Ele também registra o estado da verificação prévia de sanitização: execuções brutas avisam com `upload_recommended: false`, enquanto cópias sanitizadas com `scrub-report.json` são marcadas como prontas para upload para o futuro caminho de ingestão.

`nullstate scrub` cria uma cópia sanitizada de uma execução em `scrubbed-runs/` e grava `scrub-report.json`. Ele deixa a execução original intacta e se recusa a sobrescrever uma cópia sanitizada existente.

<a id="security-boundaries"></a>
## Limites de segurança

Os limites importantes são:

- Nenhum alvo de nuvem real por padrão.
- As alterações do Terraform acontecem em um espaço de trabalho copiado.
- O modelo vermelho não recebe acesso ao shell.
- O executor de ataques só executa o `attack.py` gerado no diretório da execução.
- Os segredos são carregados de variáveis de ambiente ou de arquivos env locais ignorados.
- Os artefatos da execução devem ser revisados antes da publicação.
- `nullstate scrub` deve ser executado antes da publicação de estudos de caso públicos, do upload de CI ou do compartilhamento de bundles de suporte.
- `--allow-live-cloud` é obrigatório antes de direcionar a execução a qualquer endpoint de nuvem não local.

<a id="extension-points"></a>
## Pontos de extensão

<a id="new-scenario"></a>
### Novo cenário

Adicione ou atualize:

```text
src/nullstate/scenarios.py
src/nullstate/scenario_detection.py
src/nullstate/findings.py
src/nullstate/remediation.py
src/nullstate/attack.py
examples/<scenario-name>/
tests/
```

<a id="new-sandbox-backend"></a>
### Novo backend de sandbox

Adicione metadados e comandos do backend em:

```text
src/nullstate/sandbox.py
```

Depois, adicione testes para:

- `sandbox list`
- `sandbox status`
- `sandbox up --dry-run`
- `sandbox down`

<a id="richer-red-tooling"></a>
### Ferramentas mais completas para a equipe vermelha

A próxima expansão segura não é acesso livre ao shell. Ela deve ser uma lista de permissões por cenário:

- sondas Python geradas
- modelos fixos de comandos
- URLs de destino exclusivamente locais
- tempo limite estrito
- registro completo de eventos
- sem herança de credenciais reais de nuvem

Consulte [Prontidão empresarial](enterprise-readiness.md) para a lista de controles que deve ser concluída antes de apresentar sondas de execução como evidência para equipes ou empresas.

<a id="test-coverage"></a>
## Cobertura de testes

Comandos principais de validação:

```powershell
python -m unittest discover -s tests -v
python -m ruff check src tests
python -m mypy src
```

Teste de fumaça útil:

```powershell
python -m nullstate run examples/aws-public-s3 --offline --mock-agents --runs-dir runs/red-tool-smoke
python -m nullstate report --runs-dir runs/red-tool-smoke
```

A execução de fumaça deve mostrar:

- um achado antes da remediação
- `Red before: success`
- `Red after: blocked`
- dois eventos `red-tool` em `events.jsonl`
