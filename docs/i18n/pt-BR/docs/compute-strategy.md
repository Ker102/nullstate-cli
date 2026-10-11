<a id="amd-compute-strategy"></a>
# Estratégia de computação AMD

<a id="decision"></a>
## Decisão

AMD Developer Cloud / DigitalOcean como principal mais difícil; Fireworks AI se GPU atrasar.

<a id="why-primary-path-is-digitaloceanamd-developer-cloud"></a>
## Por que DigitalOcean/AMD

- Evidência forte: serving, ROCm, vLLM/SGLang, observabilidade GPU, operação.
- Aprendizado real DevOps, cloud, segurança, inferência.
- Inferência privada/controlada para IaC sensível.
- Caso melhor que apenas API hospedada.

<a id="why-fireworks-stays-as-fallback"></a>
## Por que Fireworks

- Desbloqueia atraso AMD.
- Mantém vermelho/azul compatível.
- Relevante AMD, mas gerenciado, não privado.

<a id="execution-plan"></a>
## Plano

<a id="track-a---digitalocean-baseline-without-gpu"></a>
### Via A - DigitalOcean sem GPU

Prepare primeiro:

- secrets projeto/repo
- droplet/host endurecido
- Docker/Compose
- Azure LocalStack
- CLI
- ambiente Actions
- armazenamento artefatos
- monitoramento/logs

Útil antes de GPU.

<a id="track-b---amd-gpu-inference"></a>
### Via B - AMD GPU

Com MI300X:

- provisionar GPU AMD/DO
- ROCm ou imagem provider
- vLLM/SGLang compatível
- só API necessária ao operador
- registrar modelo, contexto, ROCm, GPU, memória, throughput, latência
- guardar vLLM `/metrics`, `amd-smi` ou `rocm-smi`

<a id="track-c---fireworks-contingency"></a>
### Via C - Fireworks

Se GPU impedir entrega:

- configurar `NULLSTATE_LLM_BASE_URL`
- mesma demo
- rotular fallback gerenciado
- manter AMD próximo marco, não ocultar bloqueio

<a id="demo-positioning"></a>
## Posicionamento

História preferida:

```text
nullstate runs local IaC security validation and can use a private AMD MI300X-hosted model endpoint for red/blue reasoning over security evidence.
```

História fallback:

```text
nullstate is model-provider portable through OpenAI-compatible endpoints. The same CLI can run against managed inference while the private AMD GPU endpoint is being provisioned.
```

<a id="evidence-checklist"></a>
## Evidência

- `runs/<id>/report.md`
- `runs/<id>/metrics.json`
- vLLM `/metrics` antes/depois
- `amd-smi` ou `rocm-smi`
- versão ROCm
- comando de servidor
- rede sanitizada
- capturas GPU/CLI
- informar AMD, mock ou Fireworks

<a id="risks"></a>
## Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| Acesso AMD atrasado | Alto | DO/Fireworks |
| GPU/ROCm incompatível | Médio | imagem provider/versões exatas |
| Modelo grande/lento | Médio | um para dois papéis |
| Endpoint público | Alto | ingress, token, fronteira |
| Inferência privada exagerada | Alto | tipo real por run |
