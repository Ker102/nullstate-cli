<a id="amd-compute-strategy"></a>
# AMD-Compute-Strategie

<a id="decision"></a>
## Entscheidung

Schwierigere AMD-Developer-Cloud-/DigitalOcean-Route primär; Fireworks AI als GPU-Fallback.

<a id="why-primary-path-is-digitaloceanamd-developer-cloud"></a>
## Warum DigitalOcean/AMD

- Stärkere Evidenz: Serving, ROCm, vLLM/SGLang, GPU-Observability, Betrieb.
- Besserer Lerneffekt durch DevOps, Cloud, Sicherheit, Inferenz.
- Private/eigene Inferenz für sensible IaC.
- Bessere Fallstudie als Hosted-API allein.

<a id="why-fireworks-stays-as-fallback"></a>
## Warum Fireworks

- Entblockt AMD-Verzögerung.
- Red-/Blue-Loop kompatibel.
- AMD-relevant, aber Managed statt privat positionieren.

<a id="execution-plan"></a>
## Plan

<a id="track-a---digitalocean-baseline-without-gpu"></a>
### Pfad A - DigitalOcean ohne GPU

Zuerst vorbereiten:

- Projekt-/Reposecrets
- gehärteter Droplet/Host
- Docker/Compose
- Azure LocalStack
- CLI-Installation
- Actions-Umgebung
- Artefaktspeicher
- Monitoring/Logs

Schon vor GPU nützlich.

<a id="track-b---amd-gpu-inference"></a>
### Pfad B - AMD-Inferenz

Bei MI300X-Zugang:

- AMD-/DO-GPU provisionieren
- ROCm oder Providerimage
- vLLM/SGLang-kompatibles API
- nur benötigte API zum Betreiber öffnen
- Modell, Kontext, ROCm, GPU, RAM, Durchsatz, Latenz erfassen
- vLLM `/metrics`, `amd-smi` oder `rocm-smi` speichern

<a id="track-c---fireworks-contingency"></a>
### Pfad C - Fireworks

Wenn GPU Einreichung blockiert:

- `NULLSTATE_LLM_BASE_URL` setzen
- dieselbe Demo
- Managed-Fallback dokumentieren
- AMD nächster Meilenstein statt Blocker verstecken

<a id="demo-positioning"></a>
## Präsentation

Bevorzugte Geschichte:

```text
nullstate runs local IaC security validation and can use a private AMD MI300X-hosted model endpoint for red/blue reasoning over security evidence.
```

Fallbackgeschichte:

```text
nullstate is model-provider portable through OpenAI-compatible endpoints. The same CLI can run against managed inference while the private AMD GPU endpoint is being provisioned.
```

<a id="evidence-checklist"></a>
## Evidenz

- `runs/<id>/report.md`
- `runs/<id>/metrics.json`
- vLLM `/metrics` vorher/nachher
- `amd-smi` oder `rocm-smi`
- ROCm-Version
- Serverstart
- bereinigtes Netzdiagramm
- GPU-/CLI-Screenshots
- AMD, Mock oder Fireworks nennen

<a id="risks"></a>
## Risiken

| Risiko | Wirkung | Mitigation |
|---|---|---|
| AMD-Zugang spät | Hoch | DO/Fireworks |
| GPU/ROCm-Mismatch | Mittel | Providerimage/exakte Versionen |
| Modell groß/langsam | Mittel | eines für beide Rollen |
| Öffentlicher Endpunkt | Hoch | Ingress, Token, Grenze |
| Private Inferenz übertrieben | Hoch | echten Typ nennen |
