<a id="model-serving-runbook"></a>
# Guide de service des modèles

Ce projet utilise des endpoints compatibles OpenAI pour fonctionner avec vLLM/SGLang local, des presets de fournisseurs managés ou un proxy personnalisé.

Utiliser `NULLSTATE_LLM_PROVIDER=custom` pour les endpoints AMD GPU autohébergés. Utiliser `NULLSTATE_LLM_PROVIDER=google` avec une clé Google AI Studio pour un repli Gemini managé sans URL de base exigée. `NULLSTATE_LLM_PROVIDER=claude` est seulement un chemin Anthropic/OpenAI expérimental ; ajouter un adaptateur natif avant de dépendre de fonctions Claude de production.

<a id="recommended-mi300x-split"></a>
## Répartition MI300X recommandée

Utiliser deux conteneurs pour tester séparément les rôles rouge/bleu :

| Rôle | Stack | Premier modèle | Motif |
|---|---|---|---|
| Rouge | repli vLLM ROCm | `Qwen/Qwen3-4B-Instruct-2507` | Ce modèle a déjà démarré avec succès sur le droplet MI300X avec vLLM et fournit un endpoint stable. |
| Rouge expérimental | SGLang ROCm | `Qwen/Qwen3.5-9B` ou `Qwen/Qwen3.5-35B-A3B` | Garder comme objectif étendu ; l'image SGLang actuelle importe des modules `aiter` incompatibles. |
| Bleu | vLLM ROCm | d'abord `google/gemma-4-E4B-it`, puis `google/gemma-4-26B-A4B-it` ou `google/gemma-4-31B-it` | Gemma 4 nécessite une image vLLM ROCm récente ; commencer petit, puis agrandir. |

Ne pas commencer par Nemotron 3 Super sur un droplet à un seul 1x MI300X. Les fiches publiques BF16/FP8 indiquent des besoins matériels bien supérieurs. Le garder dans l'étude de cas comme future cible multi-GPU ou comparaison managée.

<a id="start-stable-red-qwen-endpoint"></a>
## Démarrer le Qwen rouge stable

Utiliser d'abord ce chemin vLLM pour éviter l'échec d'import SGLang/Quark/AITER observé sur l'image DigitalOcean ROCm.

```bash
MODEL_ID=Qwen/Qwen3-4B-Instruct-2507 \
SERVED_MODEL_NAME=nullstate-qwen3-4b \
HOST_PORT=8001 \
GPU_MEMORY_UTILIZATION=0.40 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen-vllm-rocm.sh
```

<a id="start-experimental-red-qwen35-sglang-endpoint"></a>
## Démarrer le Qwen3.5 SGLang rouge expérimental

Exécuter sur le droplet :

```bash
cd /opt/nullstate

MODEL_ID=Qwen/Qwen3.5-9B \
SERVED_MODEL_NAME=nullstate-qwen35-9b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

Le script Qwen SGLang définit `SGLANG_USE_AITER=0` par défaut. Sur DigitalOcean ROCm, le conteneur peut quitter au démarrage avec `ImportError: aiter is required when SGLANG_USE_AITER is set to True` ; le smoke test privilégie un démarrage stable aux kernels AITER. SGLang lit un entier : utiliser `0` ou `1`, pas `false` ou `true`. Réactiver seulement après confirmation d'un build `aiter` compatible :

```bash
SGLANG_USE_AITER=1 \
MODEL_ID=Qwen/Qwen3.5-9B \
SERVED_MODEL_NAME=nullstate-qwen35-9b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

Pour un modèle rouge plus puissant après le premier smoke test :

```bash
MODEL_ID=Qwen/Qwen3.5-35B-A3B \
SERVED_MODEL_NAME=nullstate-qwen35-35b \
HOST_PORT=8001 \
bash /path/to/nullstate-cli/scripts/droplet/serve-qwen35-sglang-rocm.sh
```

<a id="start-blue-gemma-4-endpoint"></a>
## Démarrer le Gemma 4 bleu

Exécuter sur le droplet :

```bash
MODEL_ID=google/gemma-4-E4B-it \
SERVED_MODEL_NAME=nullstate-gemma4-e4b \
HOST_PORT=8002 \
bash /path/to/nullstate-cli/scripts/droplet/serve-gemma4-vllm-rocm.sh
```

Pour une analyse bleue plus grande une fois E4B stable :

```bash
MODEL_ID=google/gemma-4-26B-A4B-it \
SERVED_MODEL_NAME=nullstate-gemma4-26b-a4b \
HOST_PORT=8002 \
MAX_MODEL_LEN=32768 \
bash /path/to/nullstate-cli/scripts/droplet/serve-gemma4-vllm-rocm.sh
```

<a id="tunnel-to-local-windows"></a>
## Tunnel vers Windows local

Depuis Windows PowerShell :

```powershell
ssh -i "$env:USERPROFILE\Documents\AMDhackkey" -N `
  -L 8001:127.0.0.1:8001 `
  -L 8002:127.0.0.1:8002 `
  root@<droplet-ip>
```

Configurer ensuite nullstate localement :

```powershell
$env:NULLSTATE_LLM_PROVIDER = "custom"
$env:NULLSTATE_RED_LLM_BASE_URL = "http://127.0.0.1:8001"
$env:NULLSTATE_BLUE_LLM_BASE_URL = "http://127.0.0.1:8002"
python -m nullstate run examples/aws-public-s3 --target localstack-aws --scenario aws-public-s3 --red-model nullstate-qwen3-4b --blue-model nullstate-gemma4-e4b
```

Utiliser `--offline` pour analyse IaC statique sans Terraform apply ; `--mock-agents` pour aucun appel modèle.

Exemple de repli managé :

```powershell
$env:NULLSTATE_LLM_PROVIDER = "google"
$env:NULLSTATE_LLM_API_KEY = "<google-ai-studio-key>"
python -m nullstate run examples/aws-public-s3 --offline --red-model gemini-3.5-flash --blue-model gemini-3.5-flash
```

<a id="evidence-collection"></a>
## Collecte des preuves

Sur le droplet :

```bash
bash /path/to/nullstate-cli/scripts/droplet/collect-endpoint-evidence.sh http://127.0.0.1:8001 nullstate-qwen3-4b
bash /path/to/nullstate-cli/scripts/droplet/collect-endpoint-evidence.sh http://127.0.0.1:8002 nullstate-gemma4-e4b
```

Conserver le répertoire de preuves généré et les artefacts nullstate :

- `models.json`
- `metrics.prom`
- `chat-completion.json`
- `host-snapshot.txt`
- `runs/<id>/metrics.json`
- `runs/<id>/vllm-metrics-red-*.prom`
- `runs/<id>/vllm-metrics-blue-*.prom`
