<a id="runbook"></a>
# Betriebshandbuch

<a id="local-offline-demo"></a>
## Lokale Offline-Demo

```powershell
python -m pip install -e .
python -m nullstate doctor --offline
python -m nullstate status
python -m nullstate run examples/azure-public-blob --offline
python -m nullstate report
```

Vor Aufnahme alle Offline-Szenarien ausführen:

```powershell
python -m nullstate run examples/aws-public-s3 --offline
python -m nullstate run examples/k8s-privileged-pod --offline
python -m nullstate run examples/compose-exposed-admin --offline
python -m nullstate run examples/onprem-ssh-password --offline
python -m nullstate run examples/generic-plan-review --offline
```

`run` nutzt `--scenario auto` und `--target auto`. Für konkrete Adapteraufnahmen `--scenario` und `--target` explizit halten.

<a id="sandbox-discovery"></a>
## Sandbox-Erkennung

```powershell
python -m nullstate status
python -m nullstate sandbox list
python -m nullstate sandbox status localstack-azure
python -m nullstate sandbox up localstack-azure --dry-run
```

Meist erscheint `Next`. Bei unklarer Konfiguration, Erreichbarkeit oder neuestem Bericht `python -m nullstate status` nutzen.

<a id="localstack-azure-setup"></a>
## LocalStack Azure einrichten

Setzen:

```powershell
$env:LOCALSTACK_AUTH_TOKEN = "<token>"
```

Dann:

```powershell
python -m nullstate sandbox up localstack-azure
python -m nullstate sandbox status localstack-azure
```

Bleibt der Container laut `sandbox up localstack-azure` nicht aktiv, prüfen:

```powershell
docker logs localstack-azure
```

Bei nicht aktiviertem Azure Emulator stoppen und Berechtigung klären. Wiederholungen können wegen großem Image viel Speicher verbrauchen.

Lokale Token-env-Datei unversioniert halten. Zuerst `.env.local`, dann `.env` erkannt:

```powershell
python -m nullstate sandbox up localstack-azure
python -m nullstate sandbox up localstack-aws
```

`--env-file` nur für andere Orte:

```powershell
python -m nullstate sandbox up localstack-aws --env-file .env.local
```

Docker-Compose-Alternative:

```powershell
$env:LOCALSTACK_AUTH_TOKEN = "<token>"
docker compose -f docker-compose.localstack-azure.yml up
```

Compose liest `${LOCALSTACK_AUTH_TOKEN}` aus Shell oder `.env` neben `docker-compose.localstack-azure.yml`:

```env
LOCALSTACK_AUTH_TOKEN=your-token-here
```

Git ignoriert `.env`. Token nie committen; anderer Speicherort kann explizit übergeben werden:

```powershell
docker compose --env-file .env.local -f docker-compose.localstack-azure.yml up
```

`env_file:` im Dienst injiziert Containerwerte; hier ist Compose-Interpolation von `${LOCALSTACK_AUTH_TOKEN}` vor Start nötig.

<a id="reports-and-run-lookup"></a>
## Berichte und Suche

Neuesten Bericht unter `runs/` öffnen:

```powershell
python -m nullstate report
```

Neuesten Bericht eines benannten Evidenzordners:

```powershell
python -m nullstate report --runs-dir runs/live-aws-model
```

Bekannte ID auch verschachtelt öffnen:

```powershell
python -m nullstate report 20260509-200601 --runs-dir runs
```

Vor Veröffentlichung, Support oder Fallstudie bereinigte Kopie erstellen:

```powershell
python -m nullstate scrub --runs-dir runs
python -m nullstate scrub 20260509-200601 --runs-dir runs --output-dir scrubbed-runs
```

`scrub` kopiert nach `scrubbed-runs/`, lässt Original unverändert und überschreibt keine bestehende Kopie. `scrub-report.json` vor Teilen prüfen.

<a id="first-tagged-release-checklist"></a>
## Erster getaggter Release

Vor erstem Produkttag verwenden. Hackathon-Freeze endete 2026-06-18; Tags und Veröffentlichung benötigen weiter ausdrückliche Eigentümerzustimmung. Normale Änderungen über Featurebranches und geschützte PRs.

Grüne Kandidatenchecks prüfen:

```powershell
gh pr checks 24
```

Release ohne Veröffentlichung proben:

```powershell
gh workflow run Release --field dry_run=true
gh run list --workflow Release --limit 1
```

Wheel-Installation des Befehls `nullstate` lokal prüfen:

```powershell
python scripts/release/install_smoke.py
```

Nach genehmigtem Merge/Tag Release prüfen:

```powershell
gh release view v0.1.0
gh release download v0.1.0 --dir dist
```

Provenienz-/SBOM-Attestierungen prüfen:

```powershell
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli
gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli --predicate-type https://spdx.dev/Document/v2.3
```

Sigstore-Bundle prüfen:

```powershell
$wheel = Get-ChildItem dist\nullstate-*.whl | Select-Object -First 1
cosign verify-blob $wheel.FullName --bundle "$($wheel.FullName).sigstore.json" --certificate-identity "https://github.com/Ker102/nullstate-cli/.github/workflows/release.yml@refs/tags/v0.1.0" --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

Assets bestätigen:

- Wheel und Quelldistribution
- `release-manifest.json`
- `sbom.spdx.json`
- benachbarte `.sigstore.json` für Hauptartefakte

<a id="model-endpoint-setup"></a>
## Modellendpunkt

Für selbst gehostetes vLLM/SGLang oder privaten OpenAI-Proxy für beide Rollen setzen:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_LLM_BASE_URL = "http://localhost:8000"
$env:NULLSTATE_LLM_API_KEY = "<optional>"
```

Dann normal ausführen.

Gemini: Preset und Key setzen; CLI ergänzt kompatible Basis-URL:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
python -m nullstate run examples/azure-public-blob --red-model gemini-3.5-flash --blue-model gemini-3.5-flash
```

`claude` nutzt Anthropics OpenAI-SDK-Kompatibilität:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "claude"
$env:NULLSTATE_LLM_API_KEY = "<anthropic-api-key>"
python -m nullstate run examples/azure-public-blob --red-model claude-sonnet-4-6 --blue-model claude-sonnet-4-6
```

Claude ist experimentell. Für spezifische Funktionen nativen Anthropic-Adapter statt überdehnten Wrapper ergänzen.

Zwei Container/SSH-Tunnel: Rollenendpunkte:

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
$env:NULLSTATE_RED_LLM_API_KEY = "<optional-red-token>"
$env:NULLSTATE_BLUE_LLM_API_KEY = "<optional-blue-token>"
python -m nullstate run examples/azure-public-blob --red-model nullstate-red --blue-model nullstate-blue
```

Pro Ausführung auch `--llm-provider`, `--red-provider`, `--blue-provider`, `--red-base-url`, `--blue-base-url`. Fehlende Rollenwerte nutzen `NULLSTATE_LLM_PROVIDER`, `NULLSTATE_LLM_BASE_URL`, `NULLSTATE_LLM_API_KEY`. Explizite URLs überschreiben Presets für Gateways/Fixtures.

Ohne Rollenendpunkt deterministischer Mock. LocalStack kann vor AMD-Zugang entwickelt werden; Endpunkt ist für MI300X-Evidenz und Tokens/Durchsatz nötig, nicht für deterministische Exploit-/Abhilfeschleife.

`--offline` steuert Terraform/Cloud, nicht Modelle. Konfigurierte gemeinsame/Rollenendpunkte werden weiterhin mit statischer Analyse aufgerufen:

```powershell
$env:NULLSTATE_LLM_BASE_URL = "http://127.0.0.1:8001"
python -m nullstate run examples/azure-public-blob --offline --blue-model nullstate-qwen3-4b --red-model nullstate-qwen3-4b
```

`--mock-agents` für keinerlei Modellaufrufe:

```powershell
python -m nullstate run examples/azure-public-blob --offline --mock-agents
```

<a id="amd-developer-cloud--digitalocean-path"></a>
## AMD Developer Cloud / DigitalOcean

[AMD-Strategie](compute-strategy.md) als Checkliste: erst Nicht-GPU-Baseline, dann MI300X-Endpunkt bei Zugang.

Aktuelles Qwen3.5/Gemma-4-Zweicontainer-Setup in [Modellbereitstellung](model-serving.md).

<a id="fireworks-fallback"></a>
## Fireworks-Fallback

Bei AMD-Verzögerung `NULLSTATE_LLM_BASE_URL` auf Managed-Endpunkt richten. Evidenz als Managed-Inferenz, nicht private GPU markieren.

<a id="metrics-evidence"></a>
## Metrikevidenz

Bei Endpunkt versucht nullstate abzurufen:

```text
<NULLSTATE_LLM_BASE_URL>/metrics
<NULLSTATE_RED_LLM_BASE_URL>/metrics
<NULLSTATE_BLUE_LLM_BASE_URL>/metrics
```

Bei vLLM-Prometheus-Metriken schreibt es:

- `vllm-metrics-before.prom`
- `vllm-metrics-after.prom`
- `vllm-metrics-red-before.prom` und Rollenvarianten bei getrennten URLs
- geparste Zähler in `metrics.json`

GPU-Snapshot zuerst `amd-smi`, dann `rocm-smi`. Ohne beide steht `status: unavailable` in `metrics.json`, ohne Abbruch.

<a id="work-you-can-do-before-amd-gpu-access"></a>
## Arbeit vor AMD-Zugang

Während Supportwartezeit vorbereiten:

- DigitalOcean-Projekt/Firewall
- SSH-Keys/Minimalrechte
- Nicht-GPU-Droplet für Smoke-Tests
- Docker/Updatepolitik
- GitHub-Secrets-/Umgebungsnamen
- lokale `.env` aus `.env.example`
- bereinigte Workflow-/PR-/Offline-Screenshots
- LocalStack-Azure-Token/Zugang falls verfügbar

<a id="artifact-review-before-publishing"></a>
## Artefakte vor Veröffentlichung

Prüfen:

- `runs/<id>/report.md`
- `runs/<id>/findings.json`
- `runs/<id>/events.jsonl`
- `runs/<id>/remediation.json`
- `runs/<id>/metrics.json`
- `runs/<id>/vllm-metrics-before.prom`
- `runs/<id>/vllm-metrics-after.prom`
- `runs/<id>/remediation.patch`

Keine Geheimnisse, echten Tenant-/Subscription-IDs, privaten Endpunkte oder Terraform-State veröffentlichen.
