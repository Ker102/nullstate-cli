<a id="cost-report"></a>
# Relatório de custos

<a id="summary"></a>
## Resumo

V1 visa custo cloud quase zero por padrão. Offline local; LocalStack no Docker do operador; AMD somente evidência de serving hackathon.

<a id="cost-items"></a>
## Itens

| Item | Custo previsto | Notas |
|---|---:|---|
| CLI | 0 | Python local |
| Demo offline | 0 | sem nuvem/modelo |
| LocalStack Azure | depende do acesso | token |
| AMD Developer Cloud | créditos hackathon | MI300X |
| Fireworks | depende do provider | fallback GPU |
| GitHub Actions | depende do plano baixo/grátis | testes leves |

<a id="controls"></a>
## Controles

- Sem Azure real padrão.
- CLI não cria recursos duradouros.
- Pare local com `nullstate sandbox down`.

<a id="future-tracking"></a>
## Futuro

Registre duração real de serving, horas GPU e custos LocalStack/cloud antes de publicar.

Registre offline, inferência gerenciada ou AMD por run para não ocultar fallback antes do acesso.
