<a id="security-model"></a>
# Modelo de segurança

<a id="assets"></a>
## Ativos

| Ativo | Importância | Sensibilidade |
|---|---|---|
| Entrada Terraform | infraestrutura e possíveis segredos | média/alta |
| Artefatos | achados, logs, patches e evidências de modelos | média |
| Chave do modelo | acesso LLM | alta |
| Token LocalStack | inicia emulador Azure | alta |
| Estado Terraform | possíveis dados sensíveis de infraestrutura | alta |

<a id="trust-boundaries"></a>
## Fronteiras de confiança

- Shell do operador para CLI.
- CLI para backend sandbox.
- CLI para endpoint de modelo.
- Instruções do agente para ferramentas permitidas.
- Artefatos locais para documentação pública.

<a id="identities"></a>
## Identidades

- Operador: pessoa confiável executando CLI.
- Agente vermelho: atacante parcialmente confiável, restrito ao local.
- Agente azul: correção parcialmente confiável.
- Servidor externo: confiável só para comportamento do endpoint configurado.
- Runner CI: identidade efêmera com permissões mínimas.
- Agente IA cliente: principal não humano parcialmente confiável, com identidade dedicada, workload, principal de serviço, papel IAM, identidade gerenciada ou autoridade delegada.
- Identidade ferramenta/runtime: principal distinto para host, gateway, conector, plugin, MCP ou ferramenta posterior.

A análise deve distinguir:

- identidade e permissões próprias do agente
- pessoa/workload solicitante
- autoridade delegada/em nome de outro
- identidades de runtime e ferramenta
- credenciais posteriores e audiences de tokens
- recurso e operação finais

Não atribua ação delegada só à pessoa ou ao agente quando ambos participam da autorização.

Para externos, identidade federada válida é necessária, mas insuficiente. Autorização de alto impacto deve depender de evidência runtime disponível:

- identidade vinculada aos atributos esperados
- digest implantado coincide com artefato assinado aprovado
- proveniência de build e emissor verificados
- atestação runtime/hardware atual e válida quando exigida
- políticas de rede/ferramentas coincidem com perfil aprovado
- revogação/auditoria operantes

Classifique como verificada criptograficamente, observada pelo provedor, atestada pelo operador, inferida ou desconhecida. Não promova postura desconhecida silenciosamente a confiável.

<a id="network-controls"></a>
## Controles de rede

V1 usa offline ou endpoints locais LocalStack por padrão. Nuvem real fica fora do escopo padrão.

Sondagens miram apenas `offline://...`, `local://...`, `127.0.0.1`, `localhost` ou `localhost.localstack.cloud` por padrão. HTTP(S) não local exige `--allow-live-cloud` explícito e aprovação nos eventos. Com `run --policy-file`, `allowed_target_hosts` pode exigir hostname exato ou sufixo `*.domain`. Cenários integrados ficam locais/offline até haver adaptador real; não declare validação real sem evidência do alvo e dos eventos.

<a id="secret-handling"></a>
## Segredos

- Lidos de variáveis de ambiente.
- `.env` e estado Terraform ignorados.
- `.env.example` documenta nomes sem valores.
- Revisão obrigatória antes de estudo público, suporte, captura ou arquivo de demo.
- `nullstate scrub` cria cópia sem informações sensíveis antes de upload, suporte ou publicação.

<a id="container-security"></a>
## Segurança de contêineres

LocalStack e outros são dependências runtime, não binários incluídos. Use imagens confiáveis e evite código vermelho arbitrário fora de workspaces gerados.

<a id="red-team-command-execution"></a>
## Comandos da equipe vermelha

O executor V1 é restrito por projeto:

- Só executa `attack.py` gerado.
- `attack.py` fica diretamente no diretório da execução.
- Se usado, `attack-manifest.json` também fica diretamente ali.
- Inicia com Python atual, não shell arbitrário.
- Entradas dinâmicas só `--target-url`, `--stage` e caminho do manifesto.
- Registra comando, stdout, stderr, retorno, URL, etapa, início, fim e duração.
- Sondagens permitidas por template, não geradas pelo modelo em runtime.
- Timeouts curtos e captura limitada antes de upload empresarial ou retenção longa.

Permite comandos reais locais sem acesso irrestrito do modelo às ferramentas.

Hardening empresarial deve adicionar:

- política explícita para cada cenário/backend
- hostnames permitidos para adaptador HTTP(S) de nuvem real
- sanitização na publicação com regras organizacionais
- gate `--allow-live-cloud`, desligado por padrão

<a id="cicd-security"></a>
## Segurança CI/CD

- PR: testes, lint, tipos e auditoria.
- CodeQL em PR, pushes e semanalmente.
- Revisão de dependências em PR.
- Release apenas por tags semver com atestações GitHub para distribuições e `sbom.spdx.json`.
- Workflows de menor privilégio.

<a id="data-protection"></a>
## Proteção de dados

Revise antes de publicar. Não publique tokens, IDs reais de tenants/assinaturas, mapas IP privados ou estado cloud.

<a id="known-risks"></a>
## Riscos conhecidos

- Adaptadores podem ser esqueletos, não backends completos.
- Azure LocalStack exige configuração externa e token.
- Métricas offline mostram zero tokens porque não há chamada a modelo.
- Scripts são sondagens estreitas; exploits mais ricos devem permanecer permitidos explicitamente e restritos ao sandbox.

<a id="future-improvements"></a>
## Melhorias futuras

- SBOM de dependências resolvidas mais completo a partir de lockfiles.
- Regras organizacionais mais amplas para remoção de informações sensíveis.
- Policy-as-code para ferramentas.
- Aprovação de nuvem real com intenção auditável.
- Inventário/controles por provedor para identidades IA, contexto delegado, ferramentas e confiança entre agentes.
