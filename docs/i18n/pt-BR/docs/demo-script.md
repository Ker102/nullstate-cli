<a id="demo-script"></a>
# Roteiro de demo

<a id="60-second-version"></a>
## Versão 60 segundos

1. "`nullstate` é CLI purple-team local para segurança Terraform."
2. "Lê IaC, usa sandbox/modelos, script permitido, patch determinístico e valida bloqueio."
3. Execute:

```powershell
python -m nullstate
python -m nullstate status
python -m nullstate run examples/aws-public-s3 --target localstack-aws --runs-dir runs/final-aws-gemma26b --red-model nullstate-gemma4-26b-a4b --blue-model nullstate-gemma4-26b-a4b
python -m nullstate report --runs-dir runs/final-aws-gemma26b
```

4. Mostre resumo:
   - Contagem
   - Vermelho antes: sucesso
   - Vermelho depois: bloqueado
   - Caminho artefatos
5. `events.jsonl` e `red-tool`: comando, stdout, stderr, retorno, URL, timestamps.
6. Relatório e diretório. Reabra via `python -m nullstate report` ou `python -m nullstate report <run-id> --runs-dir runs`.

<a id="mi300x-talking-points"></a>
## MI300X

- Planos grandes/logs longos.
- Análise azul longa por vLLM/SGLang compatível.
- Núcleo reproduzível; modelo dá raciocínio, explicação, contexto.
- Sem prompts manuais; instruções por papel/evidência.
- Tokens API e Prometheus vLLM se disponível.
- Só `attack.py` gerado no diretório.

<a id="fallback-path"></a>
## Fallback

Sem Azure/modelo, `--offline`; mesmo fluxo.

<a id="live-sandbox-shot"></a>
## Tomada ao vivo

Sequência guiada; AWS/Azure sequenciais pela porta edge `4566`.

```powershell
python -m nullstate sandbox up localstack-aws
python -m nullstate sandbox status localstack-aws
python -m nullstate run examples/aws-public-s3 --target localstack-aws --runs-dir runs/final-aws-gemma26b --red-model nullstate-gemma4-26b-a4b --blue-model nullstate-gemma4-26b-a4b
python -m nullstate report --runs-dir runs/final-aws-gemma26b

python -m nullstate sandbox down localstack-aws

python -m nullstate sandbox up localstack-azure
python -m nullstate sandbox status localstack-azure
python -m nullstate run examples/azure-public-blob --target localstack-azure --runs-dir runs/final-azure-gemma26b --red-model nullstate-gemma4-26b-a4b --blue-model nullstate-gemma4-26b-a4b
python -m nullstate report --runs-dir runs/final-azure-gemma26b
```

`LOCALSTACK_AUTH_TOKEN` em `.env.local`, `.env`, shell; não mostre valores.

<a id="accuracy-note"></a>
## Precisão

Não diga shell irrestrito. V1 modelo raciocina; somente `attack.py` gerado em diretório contra locais configurados.
