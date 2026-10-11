<a id="demo-script"></a>
# Demoskript

<a id="60-second-version"></a>
## 60-Sekunden-Version

1. "`nullstate` ist lokale Purple-Team-CLI für Terraform-Sicherheit."
2. "Liest IaC, nutzt lokale Sandbox, Red-/Blue-Modelle, erlaubtes Skript, deterministischen Patch und Blockierungsvalidierung."
3. Ausführen:

```powershell
python -m nullstate
python -m nullstate status
python -m nullstate run examples/aws-public-s3 --target localstack-aws --runs-dir runs/final-aws-gemma26b --red-model nullstate-gemma4-26b-a4b --blue-model nullstate-gemma4-26b-a4b
python -m nullstate report --runs-dir runs/final-aws-gemma26b
```

4. Zusammenfassung zeigen:
   - Befundzahl
   - Rot vorher: Erfolg
   - Rot nachher: blockiert
   - Artefaktpfad
5. `events.jsonl` und `red-tool` mit Befehl, stdout, stderr, Code, URL, Zeiten zeigen.
6. Bericht/Verzeichnis zeigen. Wiederöffnen mit `python -m nullstate report` oder `python -m nullstate report <run-id> --runs-dir runs`.

<a id="mi300x-talking-points"></a>
## MI300X-Punkte

- Große IaC-Pläne/lange Logs.
- Lange Blue-Analyse via kompatibles vLLM/SGLang.
- Reproduzierbarer Kern, Modell für Reasoning/Erklärung/Abhilfe.
- Keine manuellen Prompts, Rolleninstruktionen/Evidenz.
- Tokens aus API/vLLM-Metriken.
- Runner nur generiertes `attack.py` im Run.

<a id="fallback-path"></a>
## Fallback

Ohne Azure/Modell `--offline`, gleicher Ablauf.

<a id="live-sandbox-shot"></a>
## Live-Aufnahme

Geführte Folge zeigen; AWS/Azure nacheinander wegen Edge-Port `4566`.

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

`LOCALSTACK_AUTH_TOKEN` in `.env.local`, `.env` oder Shell; Werte nicht zeigen.

<a id="accuracy-note"></a>
## Genauigkeit

Keine unbegrenzte Shell behaupten. V1-Modell denkt; nur generiertes `attack.py` im Run gegen lokale Ziele.
