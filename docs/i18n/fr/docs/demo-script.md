<a id="demo-script"></a>
# Script de démo

<a id="60-second-version"></a>
## Version 60 secondes

1. "Voici `nullstate`, CLI purple-team locale de validation Terraform."
2. "Il lit l'IaC, exécute une sandbox locale, utilise le modèle rouge/bleu, lance un script autorisé, corrige Terraform déterministement et valide le blocage."
3. Exécuter :

```powershell
python -m nullstate
python -m nullstate status
python -m nullstate run examples/aws-public-s3 --target localstack-aws --runs-dir runs/final-aws-gemma26b --red-model nullstate-gemma4-26b-a4b --blue-model nullstate-gemma4-26b-a4b
python -m nullstate report --runs-dir runs/final-aws-gemma26b
```

4. Montrer le résumé :
   - Nombre de constats
   - Rouge avant : succès
   - Rouge après : bloqué
   - Chemin des artefacts
5. Montrer `events.jsonl`, entrées `red-tool` avec commande, stdout, stderr, retour, URL et temps.
6. Montrer rapport et répertoire. Réouvrir via `python -m nullstate report` ou `python -m nullstate report <run-id> --runs-dir runs`.

<a id="mi300x-talking-points"></a>
## Arguments MI300X

- CLI conçue pour plans énormes/logs longs.
- MI300X pour analyse bleue longue via vLLM/SGLang compatible.
- Cœur déterministe reproductible ; modèle pour raisonnement, explication, contexte correctif.
- Pas de prompts manuels ; instructions par rôle et preuves.
- Tokens depuis API et Prometheus vLLM disponible.
- Runner limité à `attack.py` généré dans le répertoire.

<a id="fallback-path"></a>
## Repli

Sans Azure LocalStack ou endpoint, `--offline` garde le flux.

<a id="live-sandbox-shot"></a>
## Plan sandbox direct

Montrer la séquence ; AWS puis Azure, port edge commun `4566`.

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

Garder `LOCALSTACK_AUTH_TOKEN` dans `.env.local`, `.env` ou shell ; ne pas filmer les valeurs.

<a id="accuracy-note"></a>
## Exactitude

Ne pas annoncer shell illimité. V1 modèle raisonne ; seul `attack.py` généré dans le répertoire vise les cibles locales configurées.
