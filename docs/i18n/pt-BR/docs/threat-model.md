<a id="threat-model---nullstate"></a>
# Modelo de ameaças - nullstate

<a id="system-overview"></a>
## Visão geral

nullstate é CLI local-first que analisa IaC, executa/simula ataques sandbox, usa vermelho/azul, corrige em cópia e produz evidências.

<a id="assets"></a>
## Ativos

| Ativo | Importância | Sensibilidade |
|---|---|---|
| Fonte IaC | pode revelar arquitetura/segredos | média/alta |
| Workspace | IaC copiado e correção | média |
| API key modelo | acesso ao endpoint | alta |
| Token LocalStack | acesso à imagem Azure | alta |
| Relatórios | evidência pública | baixa/média após sanitização |
| Grafo identidade/delegação | revela permissões, delegações, ferramentas e sistemas acessíveis | alta |
| Memória/configuração ferramentas | instruções, credenciais, dados recuperados, integrações confiáveis possíveis | alta |

<a id="trust-boundaries"></a>
## Fronteiras

- Shell usuário para CLI.
- CLI para Docker/LocalStack/kind.
- CLI para modelo.
- IA para identidade cloud, gateway, serviço posterior e contexto delegado.
- Script gerado para diretório local.
- Documentação para internet pública.

<a id="actors"></a>
## Atores

| Ator | Objetivo | Confiança |
|---|---|---|
| Operador | validar IaC local | confiável |
| Atacante externo | abusar de artefatos/sandbox exposto | não confiável |
| Agente vermelho | encontrar caminho | parcial |
| Agente azul | gerar correção | parcial |
| IA cliente | operar com identidade própria/delegada | parcial |
| Ferramenta/memória comprometida | influenciar/abusar de autoridade | não confiável |
| Dependência comprometida | executar código malicioso | não confiável |

<a id="threats"></a>
## Ameaças

| Ameaça | Impacto | Probabilidade | Controle | Evidência |
|---|---|---|---|---|
| Atingir nuvem real por acidente | Alto | Média | LocalStack/plano padrão | docs CLI |
| Segredo commitado | Alto | Média | `.gitignore`, `.env.example`, SECURITY.md | arquivos |
| Escape do sandbox | Alto | Média | comandos permitidos, cópia | módulo |
| Dependência comprometida | Alto | Média | Dependabot, pip-audit, revisão | workflows |
| Modelo enganoso | Médio | Alta | detector/validador determinísticos | testes |
| IA comprometida abusa do cloud | Alto | Média | grafo, menor privilégio, separação delegada, validação controlada | futuro adaptador |
| Agente privilegiado como intermediário confuso | Alto | Média | atribuição, política, autorização por ferramenta | futuro adaptador |
| Identidade compartilhada esconde atribuição | Alto | Média | evidência distinta agente/runtime/ferramenta quando possível | futuro inventário |
| Host externo comprometido com identidade tenant válida | Alto | Média | postura, federação curta, gateway, menor privilégio, revogação | futuro coletor |
| Postura falsa/obsoleta aceita | Alto | Média | assinatura, emissor, timestamps, atualidade, negar alto impacto em falha | futuro verificador |

<a id="abuse-cases"></a>
## Casos de abuso

- Usuário aponta para estado Terraform de produção.
- Dependência lê ambiente durante CI.
- Relatório inclui token real/endpoint privado.
- Vermelho propõe ações fora do LocalStack.
- Contêiner expõe porta inesperada.
- Injeção de prompt usa ferramenta legítima com parâmetros nocivos.
- Agente para usuário fraco retém/adquire permissões maiores de principal de serviço.
- MCP, conector, plugin, memória ou documento comprometido redireciona ações.
- Agentes compartilham identidade privilegiada e escondem autor.
- Credencial posterior supera escopo/duração da tarefa.
- Terceiro apresenta identidade válida de host vulnerável e abusa de permissões aprovadas.
- Operador toma assinatura/atestação de hardware por garantia de toda a aplicação.

<a id="residual-risks"></a>
## Riscos residuais

- Docker depende da máquina do operador.
- Cobertura Azure LocalStack pode diferir do real.
- CI não impõe proteção de branches antes de configurar GitHub.
- Identidade nativa/delegação evoluem e exigem inventário/evidência por provedor.

<a id="next-improvements"></a>
## Próximas melhorias

- Validar Azure ao vivo com habilitação Emulator.
- Adaptadores reais só com allowlists específicas e aprovação.
- Inventário AWS/Azure de agentes nativos, workloads, usuários delegados, ferramentas e credenciais posteriores.
- Evidência externa classificada como verificada, observada, atestada pelo operador, inferida ou desconhecida.
