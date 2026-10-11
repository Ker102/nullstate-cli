<a id="dependency-audit"></a>
# Auditoria de dependências

Auditoria é evidência de release, não checkbox único.

<a id="current-result"></a>
## Resultado atual

Última auditoria local:

```text
Date: 2026-07-02
Command: python -m pip_audit . --skip-editable
Tool: pip-audit 2.10.0
Result: No known vulnerabilities found
```

Workflow PR roda mesma auditoria após instalar dependências dev.

<a id="policy"></a>
## Política

- Justifique novas dependências diretas no PR.
- Falha bloqueia release salvo registro de escopo, pacote, explorabilidade, mitigação e data de remoção.
- `--skip-editable` pula metadados editáveis e audita terceiros instalados.
- Candidatos devem repetir:

```powershell
python -m pip install -e ".[dev]"
python -m pip_audit . --skip-editable
```

<a id="accepted-risk"></a>
## Risco aceito

Nenhum risco aceito de dependência vulnerável documentado.
