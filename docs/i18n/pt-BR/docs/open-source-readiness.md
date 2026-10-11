<a id="open-source-readiness-milestones"></a>
# Marcos de prontidão open source

Marcos antes de promover `nullstate` alfa a CLI estável.

GitHub:

- Marco 1: <https://github.com/Ker102/nullstate-cli/milestone/1>
- Marco 2: <https://github.com/Ker102/nullstate-cli/milestone/3>
- Marco 3: <https://github.com/Ker102/nullstate-cli/milestone/2>

<a id="current-status"></a>
## Status

`nullstate` pronto para alfa consciente de backends experimentais. AWS validado com comandos restritos; Azure tem IaC, correção, manifesto e offline, mas ao vivo espera Azure Emulator.

<a id="milestone-1-alpha-publication-readiness"></a>
## Marco 1: Publicação alfa

Objetivo: repo utilizável/compreensível.

Status: quase completo.

Critérios:

- [x] Instalação clara de fonte/tag no README.
- [x] `nullstate` e fallback `python -m nullstate`.
- [x] Licença, contribuição, conduta, segurança.
- [x] Templates seguros sem pedir secrets.
- [x] Offline sem LocalStack, credenciais Terraform cloud, modelos.
- [x] Limites vermelhos honestos.
- [x] Relatórios separam runtime, simulação, inconclusivo.
- [x] Exemplo sanitizado sem Docker. Issue #29.

<a id="milestone-2-stable-local-sandbox-validation"></a>
## Marco 2: Sandbox estável

Objetivo: prova local confiável.

Status: AWS pronto, Azure bloqueado por acesso.

Critérios:

- [x] AWS vulnerável local.
- [x] `attack.py` AWS lê anônimo antes/depois.
- [x] Evidência real antes explorado/depois bloqueado.
- [x] `sandbox up` falha se contêiner para, sem falso sucesso.
- [x] Dica clara de habilitação Azure.
- [ ] Resolver acesso ou emulador Azure suportado.
- [ ] Blob ao vivo antes leitura/depois bloqueio.
- [ ] Sem Azure, Azurite para `azure-public-blob`. Issue #30.

<a id="milestone-3-open-source-stable-cli"></a>
## Marco 3: CLI estável

Objetivo: externos instalam, executam, confiam no escopo.

Status: incompleto.

Critérios:

- [ ] Artefatos sem clone.
- [ ] Página wheel, sdist, SBOM, manifesto, atestações, verificação.
- [x] Guia 10 minutos limpo.
- [x] Bundle/dashboard sanitizado.
- [x] Não-live marcado offline/esqueleto.
- [x] Auditoria/risco aceito.
- [ ] Actions dry-run antes da tag.
- [ ] `pip install` último tag fornece `nullstate` Windows/Linux.

Notas:

- Windows local passou 2026-07-03: `python scripts/release/install_smoke.py --tag v0.1.0-alpha.2`.
- Linux precisa confirmar runner/dry-run.

<a id="azure-emulator-decision"></a>
## Decisão Azure Emulator

Token ativa licença cache/trial, mas usuário/workspace sem direito à imagem. Licença LocalStack, não permissão cloud Azure.

Opções:

1. Pedir suporte acesso de `LOCALSTACK_AUTH_TOKEN`.
2. Azurite Blob V1 cobre leitura pública, não ARM amplo.
3. Pequeno emulador interno só demo: menor dependência, maior manutenção; chamar simulador, não Azure.
4. Azure offline até emulador, AWS ao vivo primeiro.

Recomendação:

LocalStack se acesso rápido, senão Azurite somente Blob, ARM futuro.
