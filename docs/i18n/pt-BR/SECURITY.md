<a id="security-policy"></a>
# Política de segurança

<a id="supported-versions"></a>
## Versões suportadas

`nullstate` está antes de 1.0. Correções de segurança miram a branch `main` mais recente e a última tag de pré-versão quando precisam ser publicadas para avaliadores.

| Versão | Suporte |
|---|---|
| `main` | sim |
| pré-versão mais recente | sim |
| pré-versões anteriores | melhor esforço |

<a id="reporting-a-vulnerability"></a>
## Reportar vulnerabilidade

Não abra issues públicas sobre vulnerabilidades exploráveis do próprio nullstate. Contate o mantenedor em privado ou use o reporte privado GitHub se habilitado. Publique detalhes somente após disponibilização de correção ou mitigação.

<a id="security-boundaries"></a>
## Fronteiras de segurança

nullstate testa sandboxes locais intencionalmente vulneráveis. Não deve apontar para produção, salvo se o operador for dono do ambiente e entender o risco.

Padrões V1:

- nenhuma execução real Azure por padrão
- sandboxes LocalStack/Docker somente quando explicitamente iniciados
- artefatos são arquivos locais
- segredos via variáveis de ambiente, não arquivos commitados
- sondagens vermelhas restritas executam apenas `attack.py` gerado no diretório da execução
- alvos HTTP não locais exigem aprovação explícita e controles de política

<a id="secret-handling"></a>
## Tratamento de segredos

Nunca faça commit de:

- `LOCALSTACK_AUTH_TOKEN`
- API keys de modelos
- credenciais de nuvem
- estado Terraform
- `.env`
- arquivos `.tfvars` reais

Use `.env.example` para documentar configuração.

Antes de anexar artefatos a issues, tickets, estudos de caso ou suporte:

```powershell
nullstate scrub
```

Anexe a cópia sanitizada de `scrubbed-runs/`, não o diretório bruto `runs/`.
