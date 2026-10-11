<a id="case-study-outline"></a>
# Estrutura de estudo de caso

<a id="problem"></a>
## Problema

Terraform é entregue mais rápido que validação contínua. Scanners mostram risco, não exploração real nem bloqueio pela correção.

<a id="solution"></a>
## Solução

`nullstate` executa purple-team local Terraform:

- Analisar planejado.
- Tentar exploit vermelho.
- Gerar correção azul.
- Revalidar patch.
- Relatório de evidências.

<a id="demo-scenario"></a>
## Demo

Validado ao vivo: S3 público LocalStack, `nullstate` detecta, sonda leitura anônima restrita, corrige Terraform, comprova bloqueio. Azure segue determinístico, mas ao vivo aguarda habilitação ou fallback Azurite.

<a id="why-amd-mi300x"></a>
## Por que MI300X

Planos JSON, logs, saída e diffs longos vão a endpoint local sem latência API externa nem exposição.

<a id="next-steps"></a>
## Próximos

- Azure shared keys, rede pública, Key Vault.
- Resolver acesso ou Azurite.
- Adaptadores ao vivo Kubernetes/Compose/on-prem com mesmo modelo.
- GPU AMD com vLLM `/metrics`, `amd-smi` ou `rocm-smi`.
