<a id="contributing"></a>
# Contribuição

<a id="workflow"></a>
## Fluxo de trabalho

Use GitHub flow:

1. Crie uma issue ou vincule uma existente.
2. Crie uma branch: `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>` ou `chore/<short-name>`.
3. Abra um pull request estruturado.
4. Aguarde CI e revisão.
5. Faça squash merge para `main`.

Sem pushes diretos para `main`.

<a id="local-setup"></a>
## Configuração local

```powershell
git clone https://github.com/Ker102/nullstate-cli.git
cd nullstate-cli
python -m pip install -e ".[dev]"
nullstate doctor --offline
```

Se `nullstate` não estiver em `PATH`, use:

```powershell
python -m nullstate doctor --offline
```

<a id="local-checks"></a>
## Verificações locais

```powershell
python -m pip install -e ".[dev]"
python -m ruff check src tests
python -m mypy src
python -m unittest discover -s tests -v
python -m pip_audit
```

Use `pip_audit` como sinal de segurança, não como substituto da revisão. Se reportar problema em dependência, documente se o caminho vulnerável é alcançável em `nullstate`.

<a id="commit-style"></a>
## Estilo de commits

Use prefixos conventional commit:

- `feat:`
- `fix:`
- `docs:`
- `test:`
- `chore:`

<a id="pull-request-expectations"></a>
## Requisitos de pull requests

Cada PR deve incluir:

- resumo
- evidências de testes
- impacto de segurança
- atualizações de documentação
- capturas ou artefatos de execução quando relevantes

<a id="security-expectations"></a>
## Requisitos de segurança

- Não inclua credenciais reais de nuvem, tokens LocalStack, API keys de modelos, arquivos `.env`, estado Terraform ou pacotes não sanitizados.
- Use `nullstate scrub` antes de compartilhar artefatos publicamente.
- Mantenha ataques locais por padrão. Futuros alvos reais de nuvem devem ser explícitos, opt-in, controlados por política e documentados.
- Inclua testes focados ao alterar executor vermelho, políticas, sanitização, planos de upload, workflow de release ou gates CI.
