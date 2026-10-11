<a id="amd-compute-strategy"></a>
# Estrategia de cómputo AMD

<a id="decision"></a>
## Decisión

Use la vía más compleja AMD Developer Cloud / DigitalOcean como principal para el caso de estudio; Fireworks AI como contingencia si se retrasa GPU.

<a id="why-primary-path-is-digitaloceanamd-developer-cloud"></a>
## Por qué DigitalOcean/AMD como principal

- Evidencia más sólida: servicio de modelos, ROCm, vLLM/SGLang, observabilidad GPU y operación.
- Mejor aprendizaje personal: DevOps real, acceso cloud, límites de seguridad e inferencia.
- Apoya inferencia privada/controlada para IaC y evidencia sensibles.
- Mejor material de caso que solo llamar API alojada.

<a id="why-fireworks-stays-as-fallback"></a>
## Por qué Fireworks de respaldo

- Desbloquea demo si se retrasa AMD.
- Mantiene ciclo rojo/azul con endpoint compatible OpenAI.
- Relevante al ecosistema AMD, pero etiquetado administrado, no privado/propio.

<a id="execution-plan"></a>
## Plan de ejecución

<a id="track-a---digitalocean-baseline-without-gpu"></a>
### Vía A - Baseline DigitalOcean sin GPU

Prepare primero plataforma sin GPU:

- secretos proyecto/repo
- droplet de control o host endurecido
- base Docker/Compose
- sandbox Azure LocalStack
- instalación CLI nullstate
- entorno GitHub Actions
- disposición de almacenamiento de artefactos
- monitorización/logs básicos

Es útil antes de tener GPU.

<a id="track-b---amd-gpu-inference"></a>
### Vía B - Inferencia GPU AMD

Con acceso MI300X:

- aprovisionar instancia AMD/DigitalOcean GPU
- instalar ROCm o usar imagen del proveedor
- servir modelo vLLM/SGLang con API compatible
- exponer solo API necesaria al operador
- registrar modelo, contexto, ROCm, GPU, memoria, throughput y latencia
- guardar vLLM `/metrics` y `amd-smi` o `rocm-smi` en evidencias

<a id="track-c---fireworks-contingency"></a>
### Vía C - Contingencia Fireworks

Si GPU bloquea entrega:

- configurar `NULLSTATE_LLM_BASE_URL` compatible Fireworks
- misma demo nullstate
- documentar inferencia administrada
- conservar AMD/DigitalOcean como próximo hito, no ocultar bloqueo

<a id="demo-positioning"></a>
## Posicionamiento de demo

Historia preferida:

```text
nullstate runs local IaC security validation and can use a private AMD MI300X-hosted model endpoint for red/blue reasoning over security evidence.
```

Historia alternativa:

```text
nullstate is model-provider portable through OpenAI-compatible endpoints. The same CLI can run against managed inference while the private AMD GPU endpoint is being provisioned.
```

<a id="evidence-checklist"></a>
## Lista de evidencias

- `runs/<id>/report.md`
- `runs/<id>/metrics.json`
- vLLM `/metrics` antes/después
- salida `amd-smi` o `rocm-smi`
- versión ROCm
- comando de servidor
- diagrama de red saneado
- capturas GPU y CLI
- indicar AMD GPU, mock local o Fireworks

<a id="risks"></a>
## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Acceso AMD retrasado | Alto | base DO y Fireworks |
| Imagen GPU/ROCm incompatible | Medio | imagen proveedor, versiones exactas |
| Modelo grande/lento | Medio | un modelo para ambos roles |
| Endpoint público | Alto | limitar entrada, token, documentar límite |
| Caso exagera inferencia privada | Alto | etiquetar tipo real de endpoint |
