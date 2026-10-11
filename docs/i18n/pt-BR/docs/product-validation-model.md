<a id="product-and-validation-model"></a>
# Modelo de produto e validação

<a id="product-purpose"></a>
## Objetivo do produto

Nullstate é uma plataforma de validação de caminhos de ataque na nuvem sustentada por evidências. Ela correlaciona infraestrutura como código com o estado observado de AWS e Azure, raciocina sobre as relações entre rede, identidade, serviços e dados, valida caminhos de ataque selecionados em ambientes controlados, aplica correções e executa novamente o ataque.

O produto não pretende exigir uma representação perfeita, em Terraform, de uma conta inteira de nuvem. IaC descreve a configuração pretendida e gerenciada, enquanto a descoberta somente leitura descreve a realidade implantada. Nullstate deveria combinar ambas em um grafo de ambiente normalizado e preservar a origem e o grau de confiança de cada relação.

O produto de código aberto deveria primeiro atuar como um framework local de validação DevSecOps para pessoas, jobs de CI e agentes de programação. `nullstate summary --json` fornece aos agentes um resultado compacto da execução em vez de obrigá-los a analisar relatórios Markdown, enquanto `nullstate context validate` e `nullstate context summary --json` definem um contrato seguro de contexto de nuvem somente leitura antes da inclusão de coletores ao vivo.

<a id="environment-graph"></a>
## Grafo de ambiente

O grafo de ambiente deveria aceitar:

- Terraform, CloudFormation, exportações do CDK, Bicep, ARM e dados de plano/estado do provedor.
- Inventário somente leitura de recursos de AWS e Azure.
- Papéis IAM, atribuições do Azure RBAC, identidades gerenciadas, relações de confiança e identidades de cargas de trabalho.
- Identidades de agentes IA, blueprints de identidade de agentes, identidades de cargas de trabalho de agentes, contexto delegado de usuário, identidades de ferramentas e relações com credenciais posteriores.
- Endpoints públicos, redes virtuais, grupos de segurança, NSGs, rotas, gateways, endpoints privados e peering.
- Configuração de armazenamento, banco de dados, gerenciamento de segredos, computação, serverless, contêineres e Kubernetes.
- Achados de segurança nativos, logs de atividade, logs de fluxo, logs de auditoria e metadados de runtime selecionados.
- Classificação opcional de dados fornecida pelo usuário ou inferida a partir de metadados seguros e fixtures sintéticas.

O grafo não precisa clonar todos os recursos. Ele deve identificar caminhos relevantes para a segurança e criar um gêmeo mínimo do caminho de ataque contendo apenas as relações necessárias para testar uma hipótese.

A prévia atual do manifesto de contexto é intencionalmente apenas local:

```bash
nullstate context validate examples/cloud-context/aws-readonly-context.json
nullstate context summary examples/cloud-context/aws-readonly-context.json --json
```

Ela valida a estrutura dos metadados de provedor, conta, identidade, recurso, exposição pública e classificação de dados sem solicitar credenciais de nuvem. Coletores futuros deveriam emitir dados de acordo com esse contrato usando identidades de nuvem somente leitura e de curta duração.

<a id="evaluation-and-product-metrics"></a>
## Avaliação e métricas do produto

O valor de Nullstate para estudos de caso deveria ser medido, não apenas descrito. O sistema de avaliação atual começa com benchmarks internos repetíveis:

```bash
nullstate eval run examples/eval/iac-security-regression.json --output-dir eval-runs/iac-security-regression
```

O sistema registra duração, quantidade de achados, maior severidade, estado do ataque antes/depois, totais de tokens, quantidade de artefatos e estado de aprovação/reprovação das expectativas. Esse é o primeiro passo para comparar Nullstate com uma revisão baseada apenas em scanners, uma revisão manual e uma revisão feita por agentes de programação genéricos. Até que essas linhas de base existam, as afirmações deveriam se limitar ao comportamento medido de Nullstate, em vez de fazer alegações amplas sobre precisão ou economia de tempo.

<a id="identity-aware-attack-analysis"></a>
## Análise de ataques que considera identidades

Uma porta aberta ou um contêiner público não representa o achado inteiro. Nullstate deveria avaliar o que cada perspectiva autorizada de atacante pode alcançar:

| Perspectiva | Exemplo |
|---|---|
| Externa | Cliente anônimo da internet |
| Usuário do tenant | Usuário de nuvem autenticado, mas com poucos privilégios |
| Desenvolvedor | Identidade humana com permissões de implantação ou leitura |
| Carga de trabalho de CI | Identidade do GitHub Actions, GitLab ou sistema de build |
| Carga de trabalho comprometida | Identidade de VM, contêiner, função ou aplicação |
| Papel de nuvem | Papel AWS IAM, principal de serviço do Azure ou identidade gerenciada |
| Agente IA | Identidade dedicada de agente, identidade de carga de trabalho de agente ou papel de runtime do agente |
| Agente delegado | Agente agindo com autoridade propagada a partir de um usuário humano |
| Ator lateral | Principal obtido por meio de uma etapa anterior do caminho de ataque |

Cada resultado observado deveria registrar o principal, as permissões presumidas, o método de autenticação, o alvo, os dados ou a capacidade alcançados, as evidências de comandos e o grau de confiança.

<a id="ai-agents-as-cloud-principals"></a>
## Agentes IA como principais de nuvem

Agentes IA interagem cada vez mais com infraestrutura, APIs de nuvem, serviços internos, armazenamentos de dados, sistemas de tickets, repositórios de código-fonte e ferramentas de implantação. Eles podem operar por meio de:

- uma identidade dedicada criada especificamente para o agente
- um principal de serviço convencional, uma identidade gerenciada, um papel IAM ou uma identidade de carga de trabalho
- uma identidade de runtime ou de ferramenta compartilhada por vários agentes
- autoridade delegada propagada a partir de um usuário humano
- credenciais adquiridas para ferramentas posteriores ou serviços de terceiros

Esses modos não devem ser reduzidos a uma única conta de serviço genérica. Nullstate deveria representar o agente, o runtime, a ferramenta, o usuário delegante, as credenciais e o serviço alvo como nós separados do grafo. Isso preserva quem iniciou uma ação, de quem eram as permissões que a autorizaram e qual componente poderia ser comprometido.

Os caminhos de ataque específicos de agentes incluem:

- injeção de prompt fazendo o agente usar indevidamente permissões legítimas de nuvem
- ferramentas, plugins, servidores MCP, memória ou conteúdo recuperado comprometidos influenciando ações
- autonomia excessiva permitindo operações destrutivas ou alterações de privilégios fora da tarefa pretendida
- um caminho de representante confuso em que um usuário não confiável faz um agente privilegiado agir em seu nome
- autoridade delegada de usuário alcançando recursos que a identidade própria do agente não poderia acessar
- identidades de runtime compartilhadas tornando ineficazes a atribuição e o princípio do menor privilégio
- confiança entre agentes permitindo movimentação lateral
- credenciais posteriores de longa duração ou de escopo amplo aumentando o raio de impacto

Nullstate deveria avaliar pelo menos três visões separadas de permissões:

1. **Permissões nativas do agente:** recursos alcançáveis usando a identidade própria do agente.
2. **Permissões delegadas:** recursos alcançáveis ao agir em nome de um usuário ou de uma classe de usuários específicos.
3. **Permissões da cadeia de ferramentas:** recursos alcançáveis por meio de identidades de runtime, plugins, gateways, conectores e credenciais posteriores.

O relatório deveria explicar a cadeia efetiva de permissões e identificar os dados e as operações expostos se o agente, suas instruções, sua memória ou uma de suas ferramentas forem comprometidos. A validação segura deveria usar prompts sintéticos, dados sintéticos, ferramentas controladas e ambientes descartáveis em vez de tentar injeções de prompt não controladas contra agentes de produção.

Para agentes hospedados externamente, a análise de identidade por si só é insuficiente. Nullstate também deveria avaliar a postura de runtime: vínculo entre carga de trabalho e identidade, proveniência dos artefatos, digest de implantação, integridade do host e do runtime, exposição de rede, controles de ferramentas, registro de logs, revogação e atualidade e força das evidências de apoio. O projeto detalhado está em [Confiança de agentes externos e postura de runtime](plans/2026-06-22-external-agent-trust-design.md).

A CLI atual inclui uma prévia determinística inicial desse modelo:

```bash
nullstate agent posture verify examples/agent-trust/external-agent-manifest.json
nullstate agent blast-radius examples/agent-trust/external-agent-manifest.json
```

Esses comandos operam sobre um manifesto local, não sobre coletores ao vivo dos provedores. Eles se destinam a fortalecer primeiro o contrato de dados: evidências de postura ausentes, desatualizadas ou desconhecidas devem permanecer visíveis, e a autoridade delegada de usuário deve ser separada da identidade própria do agente.

<a id="exposed-data-and-impact"></a>
## Dados expostos e impacto

Administradores de nuvem podem aceitar intencionalmente um serviço alcançável porque acreditam que ele não contém nada crítico. Nullstate ainda deveria identificar se o caminho expõe:

- nomes de objetos, listagens de diretórios, IDs de contas, IDs de tenants, nomes de hosts ou topologia interna
- logs de aplicações, backups, diagnósticos, artefatos de build, mapas de código-fonte ou pacotes de implantação
- credenciais, tokens, strings de conexão, configuração ou referências a segredos
- dados pessoais, financeiros, regulados, de clientes ou proprietários
- capacidades de escrita, exclusão, personificação, execução ou alteração de políticas
- informações que permitem ataques a credenciais, movimentação lateral, escalada de privilégios ou engenharia social direcionada

Os relatórios devem distinguir:

- a configuração sugere exposição
- metadados seguros foram observados
- dados sintéticos de evidência foram recuperados
- uma capacidade privilegiada foi demonstrada
- conteúdo sensível de produção intencionalmente não foi acessado

<a id="why-not-attack-production-directly"></a>
## Por que não atacar a produção diretamente?

A descoberta somente leitura e a validação não destrutiva com aprovação de escopo restrito podem ser executadas contra a produção. A exploração autônoma deveria usar por padrão um ambiente controlado porque:

1. Exploits podem modificar, excluir, corromper ou expor dados reais.
2. Sondagens podem causar limitação de requisições, indisponibilidade, bloqueios de contas, quarentena ou ativação da resposta a incidentes.
3. Testes de IAM podem criar credenciais persistentes, relações de confiança ou alterações de privilégios.
4. Testes de exfiltração podem violar requisitos de privacidade, contratuais, regulatórios e de residência de dados.
5. Dependências de produção podem afetar clientes e terceiros fora do escopo aprovado.
6. A limpeza não pode garantir a restauração exata do estado anterior.
7. A validação repetida de CI deve ser determinística e segura o suficiente para ser executada sem que um especialista em testes de penetração supervisione cada execução.

O modelo operacional seguro é:

1. Descobrir a produção por meio de APIs somente leitura dos provedores.
2. Construir e priorizar hipóteses de ataque.
3. Executar verificações não destrutivas presentes em uma lista de permissões contra a produção somente quando a política permitir.
4. Reconstruir o caminho mínimo relevante usando dados sintéticos em um ambiente descartável.
5. Executar ataques restritos contra esse ambiente.
6. Aplicar correções e executar novamente o mesmo ataque.
7. Preservar evidências e converter o caminho comprovado em um teste de regressão.

<a id="aws-and-azure-first"></a>
## AWS e Azure primeiro

AWS e Azure deveriam ser os primeiros provedores de nuvem porque abrangem uma grande parcela da infraestrutura empresarial e ambos têm ecossistemas IaC maduros. Terraform continua sendo uma entrada de primeira classe, não um alvo concorrente: Terraform para AWS e Terraform para Azure fornecem a topologia e a configuração pretendidas, enquanto a descoberta do provedor fornece o estado ao vivo e os desvios não gerenciados.

Os adaptadores de provedores também deveriam inventariar sistemas emergentes de identidade de agentes. Microsoft Entra Agent ID fornece identidades especializadas de agentes e blueprints de identidade, enquanto Amazon Bedrock AgentCore Identity representa agentes por mecanismos de identidade de agente/carga de trabalho. Nullstate deveria ingerir essas relações junto com principais de serviço convencionais, identidades gerenciadas e papéis IAM sem presumir que toda organização usa uma plataforma de agentes nativa do provedor.

A precisão em relação ao provedor deveria ser dividida em níveis e explícita:

| Nível | Fonte de evidência | Objetivo |
|---|---|---|
| Estático | IaC, planos, políticas e configuração exportada | Análise rápida antes da implantação |
| Observado | Inventário e logs somente leitura do provedor | Entender o estado realmente implantado |
| Emulado | LocalStack, emuladores de serviços, contêineres ou gêmeos digitais | Validação segura e repetível com limites conhecidos de fidelidade |
| Sandbox real | Conta AWS ou assinatura Azure descartável | Validação de exploits com a maior fidelidade |

Cada relatório deveria identificar o nível usado. Evidências de emuladores nunca devem ser apresentadas como prova de comportamento idêntico do provedor.

<a id="ci-cloud-event-and-scheduled-execution"></a>
## Execução por CI, eventos de nuvem e agendamento

Nullstate deveria oferecer suporte a três gatilhos complementares.

<a id="pull-request-and-iac-ci"></a>
### CI de pull requests e IaC

Acionar quando arquivos Terraform, CloudFormation, Bicep, Helm, de política ou relacionados à infraestrutura forem alterados.

O pipeline:

1. Analisar a configuração proposta antes da implantação.
2. Comparar achados com uma linha de base aprovada.
3. Opcionalmente criar um ambiente de validação descartável para alterações de alto risco.
4. Executar testes de regressão de caminhos de ataque selecionados.
5. Exportar SARIF, um resultado de política legível por máquina e artefatos de evidência.
6. Bloquear o merge quando os limiares da política não forem atendidos.

Esse é o ciclo de feedback mais rápido e impede que configurações vulneráveis cheguem à nuvem.

<a id="post-deployment-validation"></a>
### Validação após a implantação

Acionar após um workflow de implantação bem-sucedido ou um evento do provedor.

Exemplos incluem um job de Terraform apply, uma implantação CloudFormation, uma implantação Azure ou um evento de nuvem indicando uma alteração de recurso ou política relevante para a segurança. Nullstate atualiza o grafo observado do ambiente, verifica desvios e executa apenas as validações seguras afetadas. A validação potencialmente destrutiva é encaminhada a um sandbox descartável em vez do ambiente de produção atualizado.

<a id="scheduled-assurance"></a>
### Verificação programada

Executar a cada hora, diariamente ou semanalmente para detectar alterações manuais no console, recursos não gerenciados, desvios de permissões, endpoints que se tornaram públicos, riscos aceitos desatualizados e caminhos de ataque criados por alterações fora do Git.

Esses modos resolvem problemas diferentes:

- A CI de PR valida a alteração pretendida antes da implantação.
- A validação após a implantação confirma que o estado observado corresponde às expectativas.
- A verificação programada detecta desvios e alterações fora dos fluxos habituais.

A plataforma paga madura pode coordenar os três modos, reter o histórico, notificar equipes e fornecer inferência de modelos gerenciada. A CLI de código aberto continua capaz de executar localmente e em CI usando credenciais e endpoints de modelos fornecidos pelo cliente.

<a id="provider-references"></a>
## Referências dos provedores

- [Microsoft Entra Agent ID](https://learn.microsoft.com/en-us/entra/agent-id/)
- [Conceitos de identidade de agentes no Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-identity)
- [Amazon Bedrock AgentCore Identity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity-overview.html)
- [Orientações da AWS sobre identidade de agentes e gerenciamento de permissões](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentsec03.html)
