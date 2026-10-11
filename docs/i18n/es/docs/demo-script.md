<a id="demo-script"></a>
# Guion de demo

<a id="60-second-version"></a>
## Versión de 60 segundos

1. "Esto es `nullstate`, una CLI purple-team local-first para validar seguridad Terraform."
2. "Lee IaC, ejecuta sandbox local, usa modelo para razonar rojo/azul, ejecuta script permitido, parchea Terraform determinísticamente y valida bloqueo."
3. Ejecute:

```powershell
python -m nullstate
python -m nullstate status
python -m nullstate run examples/aws-public-s3 --target localstack-aws --runs-dir runs/final-aws-gemma26b --red-model nullstate-gemma4-26b-a4b --blue-model nullstate-gemma4-26b-a4b
python -m nullstate report --runs-dir runs/final-aws-gemma26b
```

4. Muestre resumen del terminal:
   - Número de hallazgos
   - Rojo antes: éxito
   - Rojo después: bloqueado
   - Ruta de artefactos
5. Muestre `events.jsonl` y entradas `red-tool`: comando, stdout, stderr, retorno, URL y tiempos.
6. Muestre informe y ruta de ejecución. Reabra con `python -m nullstate report` o `python -m nullstate report <run-id> --runs-dir runs`.

<a id="mi300x-talking-points"></a>
## Puntos MI300X

- CLI pensada para planes IaC enormes y logs largos.
- MI300X para análisis azul de contexto largo con endpoint vLLM/SGLang compatible.
- Núcleo determinista reproduce veredicto; modelo añade razonamiento, explicación y contexto de remediación.
- Sin prompts manuales: instrucciones por rol y evidencia.
- Tokens desde uso API y métricas Prometheus vLLM si existen.
- Ejecutor rojo limitado a `attack.py` generado dentro de directorio de ejecución.

<a id="fallback-path"></a>
## Alternativa

Si falta LocalStack Azure o endpoint, use `--offline`. Mismo flujo CLI/informe.

<a id="live-sandbox-shot"></a>
## Toma de sandbox en vivo

Con LocalStack configurado, muestre secuencia. AWS y Azure secuenciales: ambos usan puerto edge `4566`.

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

Guarde `LOCALSTACK_AUTH_TOKEN` en `.env.local`, `.env` o shell; no muestre valores al grabar.

<a id="accuracy-note"></a>
## Nota de precisión

No diga que modelo rojo tiene shell irrestricta. En V1 razona y nullstate ejecuta solo `attack.py` generado en directorio de ejecución contra objetivos locales configurados.
