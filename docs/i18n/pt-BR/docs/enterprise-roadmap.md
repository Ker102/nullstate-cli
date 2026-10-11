<a id="enterprise-and-monetization-roadmap"></a>
# Roadmap empresarial e monetização

`nullstate` como futuro DevSecOps empresarial, não só CLI hackathon.

<a id="product-positioning"></a>
## Posicionamento

`nullstate` valida caminhos cloud com evidências: correlaciona IaC/AWS/Azure, determina identidades e dados/capacidades alcançáveis, comprova sob controle, corrige deterministicamente, preserva evidência.

Mensagem:

> Scanners indicam possíveis erros. Nullstate comprova, corrige e valida bloqueio.

Não exige IaC completa da conta. IaC dá intenção; descoberta somente leitura dá recursos, identidades, rede, logs, drift. Grafo normalizado reconstrói mínimo necessário.

IA como principal: identidade dedicada, IAM, serviço, gerenciada/workload, gateways, delegação. Calcular raio se agente, prompt, memória, conector, MCP, plugin ou credencial posterior comprometido.

Postura externa é oportunidade paga: verificar continuamente binding, proveniência, digest, atestação, patches/vulnerabilidades, rede, tools, atualidade, logs, revogação. Combinar dados/permissões, não score opaco.

<a id="target-customers"></a>
## Clientes

<a id="primary"></a>
### Primários

- DevSecOps Terraform intenso
- Plataforma IaC segura padrão
- Segurança cloud para SLA de correção
- Consultorias com evidência

<a id="secondary"></a>
### Secundários

- Startups reguladas sem enviar dados ao SaaS
- Empresas IA privada segurança
- MSP/migração

<a id="core-value-propositions"></a>
## Valor

<a id="1-evidence-over-alerts"></a>
### 1. Evidência sobre alertas

Scanners param em achados. `nullstate` cria timeline:

1. achado
2. raciocínio vermelho
3. comando sandbox
4. patch
5. validação após
6. relatório

<a id="2-local-first-and-private"></a>
### 2. Local e privado

IaC, planos, logs sensíveis no cliente; endpoints privados compatíveis.

<a id="3-deterministic-security-core"></a>
### 3. Núcleo determinístico

Modelo não decide sucesso/falha; detecção, correção, validação confiáveis.

<a id="4-devsecops-native-cli"></a>
### 4. CLI DevSecOps

Local, CI, ambiente efêmero.

<a id="enterprise-product-tiers"></a>
## Edições

<a id="open-source-cli"></a>
### CLI aberta

Objetivo: adoção/confiança.

Recursos:

- local/offline
- biblioteca limitada
- relatórios
- executor restrito
- LocalStack básico
- comunidade docs

<a id="team-edition"></a>
### Team

Objetivo: equipes pequenas/consultorias.

Recursos:

- packs ampliados
- HTML/PDF
- sanitização
- baseline
- Actions/GitLab CI
- export histórico
- presets privados

Preço possível:

- assento: 19-49 EUR/mês
- ou repo: 49-199 EUR/mês

<a id="enterprise-edition"></a>
### Enterprise

Objetivo: empresas com compliance/infra privada.

Recursos:

- tool policy-as-code
- SSO/SAML/OIDC
- audit
- evidência central
- permissões equipe/role
- deploy privado
- cenários custom
- SLA
- Jira, ServiceNow, Slack, SIEM, GRC

Preço possível:

- anual desde cerca de 15k-50k EUR/ano
- packs/suporte extras

<a id="monetization-paths"></a>
## Monetização

<a id="path-a-open-core-devsecops-cli"></a>
### A: CLI open-core

Núcleo aberto, monetizar:

- cenários enterprise
- painel cloud
- evidência hospedada
- suporte privado
- exports compliance

Prós:

- adoção dev
- GitHub credibilidade
- confiança

Contras:

- separar grátis/pago
- suporte cresce

<a id="path-b-security-consultancy-tooling"></a>
### B: Consultoria

`nullstate` diferencia avaliações pagas.

Oferecer:

- assessment purple-team
- hardening Terraform
- PRs de correção
- pacotes auditáveis

Prós:

- primeira receita fácil
- sem SaaS completo
- casos/prova cliente

Contras:

- serviço escala menos

<a id="path-c-enterprise-private-ai-security-platform"></a>
### C: IA privada empresarial

Camada privada de validação IaC/cloud.

Prós:

- narrativa MI300X
- orçamento maior

Contras:

- vendas longas
- hardening/integração

<a id="recommended-near-term-strategy"></a>
## Estratégia próxima

A+B:

1. CLI aberta.
2. Marca técnica IaC com evidência.
3. Portfolio/caso para atenção.
4. Serviços pagos primeiro.
5. Necessidades repetidas viram Team/Enterprise.

<a id="product-architecture-cli-local-gui-and-paid-platform"></a>
## CLI, GUI e plataforma

CLI motor aberto, local/CI, artefatos/bundle portátil.

GUI grátis usuário único lê `runs/`, painéis, run/report/bundle/sandbox. Sem login cloud ou team/compliance/alertas/modelos gerenciados.

App paga cloud/self-hosted ingere bundles, equipes, modelos, histórico, suporte, agendas, alertas, integrações, RBAC, audit, compliance.

`run-bundle.json` une CLI, painel grátis, CI, suporte e futuro pago. `docs/schemas/run-bundle.schema.json` v1 validado antes de gravar.

`nullstate upload --dry-run` sem rede registra endpoint, checksum, número, token presente, preflight, sem enviar/guardar valor. `docs/schemas/upload-plan.schema.json` v1 validado.

<a id="ci-and-managed-model-inference"></a>
## CI e modelos

Dois modos:

- Cliente: secrets `NULLSTATE_LLM_BASE_URL`, `NULLSTATE_LLM_API_KEY`.
- Nullstate: `NULLSTATE_CLOUD_TOKEN`, raciocínio Cloud vermelho/azul.

Gerenciado pago, medido por organização, projeto, run, modelo, tokens, latência, custo.

Três gatilhos:

1. PR IaC/policy: proposta, baseline, opcional validação descartável, bloqueio por política.
2. Após Terraform/CloudFormation/Bicep/outro: inventário, drift, caminhos.
3. Agendado: console, não gerenciado, permissões, endpoints, risco antigo, fora Git.

Descoberta produção somente leitura; checks não destrutivos aprovados. Exploit em emulador/twin/cluster/AWS/Azure dedicado conforme fidelidade.

<a id="support-automation-and-alerts"></a>
## Suporte/automação/alertas

Painel pago com ticket e bundle sanitizado, versão, ID, cenário, dashboard.

Scans repos conectados/IaC enviado; alertas críticos novos, exploit observado, correção/CI falho, risco antigo, modelo falho. Email/webhooks primeiro, Slack, Teams, Jira, GitHub Issues, SIEM depois.

<a id="brand-direction"></a>
## Marca

<a id="name"></a>
### Nome

`nullstate` sugere baseline segura.

<a id="tagline-options"></a>
### Slogans

- Comprove, corrija, valide IaC.
- Purple-team Terraform.
- Achado a caminho bloqueado.
- DevSecOps cloud com evidência.
- Ataques IaC local-first.

Principal:

> Comprove, corrija, valide caminhos cloud.

<a id="brand-personality"></a>
### Personalidade

- precisa
- técnica
- confiável
- segurança primeiro
- empresarial
- sem hype

Evite hacker autônomo antes de tools maduros. Prefira:

- vermelho restrito
- validação com evidência
- loop local

<a id="enterprise-reliability-requirements"></a>
## Confiabilidade

Antes de empresas dependerem:

1. Probes reais centrais.
2. Simulado/inferido/observado distintos.
3. Allowlist por política; cenário/backend/etapa/argumentos/classe/host/comando/timeout/saída já validados.
4. Sanitização.
5. Schema estável, manifesto antes de executar.
6. CI máquina, `nullstate run --ci`, `ci-summary.json` validados.
7. SARIF/JSON/policy-result disponíveis.
8. `nullstate evidence-manifest` SHA-256/HMAC, v1, `nullstate evidence-verify`.
9. Release checksum, wheel limpo, `sbom.spdx.json`, GitHub pacote/SBOM, Sigstore, dry-run.
10. `remediation.json` versão, arquivos, IDs, `$schema` e v1.
11. Nuvem real só explícita.

<a id="next-feature-priorities"></a>
## Prioridades

<a id="p0-trust-and-correctness"></a>
### P0: Confiança

- leitura S3 real
- runtime no relatório
- scrubber
- `ci-summary.json` veredicto/código

<a id="p1-cicd-adoption"></a>
### P1: CI/CD

- `nullstate run --ci`
- `nullstate sarif`
- Actions
- `nullstate baseline`, `--baseline-file`
- `nullstate upload --dry-run`
- `docs/schemas/upload-plan.schema.json`
- `docs/schemas/attack-manifest.schema.json`

<a id="p2-enterprise-controls"></a>
### P2: Enterprise

- política cenário/backend/etapa/classe/host/comando/timeout/saída
- `nullstate policy init` presets
- `docs/schemas/nullstate-policy.schema.json`
- organização config
- `nullstate evidence-manifest`
- `docs/schemas/evidence-manifest.schema.json`
- `nullstate evidence-verify`
- HMAC opcional
- GitHub proveniência
- GitHub SBOM
- Sigstore
- checklist primeira tag
- `remediation.json` validado
- IA AWS/Azure
- separar nativo/delegado/runtime/tool/credencial
- injection/excessive agency sintética/controlada
- confiança interagentes/shared
- postura externa/atualidade
- assinatura/digest/SLSA/SPIFFE/SPIRE/hardware
- gateway reduz sem evidência atual

<a id="p3-growth-and-brand"></a>
### P3: Crescimento

- portfolio
- vídeo
- blog
- comparação scanners
- landing GIF CLI

<a id="case-study-angle"></a>
## Caso

Não só scanner:

> CLI local transforma achados Terraform em detectar, raciocinar, comando restrito, correção, bloqueio, evidência reproduzível.

Ressalva honesta:

> Hackathon tem limite seguro; próxima versão amplia health probes a exploits reais sandbox.

Honestidade melhora credibilidade.

<a id="success-metrics"></a>
## Métricas

Técnicas:

- cenários observados
- falsos positivos
- sucesso correção
- reprodução
- evidência completa

Negócio:

- stars/forks
- vídeo completo
- conversas
- pilotos
- leads pagos
- CI recorrente

<a id="90-day-roadmap"></a>
## 90 dias

<a id="days-1-14"></a>
### Dias 1-14

- S3 real
- runtime relatório
- scrub
- walkthrough polido
- publicar caso

<a id="days-15-30"></a>
### Dias 15-30

- Azure real/limite explícito
- CI além baseline/limiar
- SARIF/JSON
- exemplo Actions

<a id="days-31-60"></a>
### Dias 31-60

- packs AWS/Azure
- política comando/classe/host
- integridade
- assinatura verificada
- landing caso

<a id="days-61-90"></a>
### Dias 61-90

- primeiro parceiro
- oferta assessment
- protótipo equipe/evidência
- arquitetura enterprise
