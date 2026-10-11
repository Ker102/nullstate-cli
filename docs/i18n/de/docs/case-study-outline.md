<a id="case-study-outline"></a>
# Fallstudiengliederung

<a id="problem"></a>
## Problem

Terraform wird schneller geliefert als kontinuierlich auf Ausnutzbarkeit geprüft. Scanner zeigen Risiken, beweisen aber weder Angriff noch wirksame Abhilfe.

<a id="solution"></a>
## Lösung

`nullstate` führt lokal Purple-Team-Terraform aus:

- Geplante Infrastruktur analysieren.
- Red-Exploit versuchen.
- Blue-Abhilfe erzeugen.
- Nach Patch validieren.
- Evidenzbericht erzeugen.

<a id="demo-scenario"></a>
## Demo

Live validiert: öffentliches S3 in LocalStack, `nullstate` erkennt, liest eingeschränkt anonym, patcht Terraform, bestätigt Blockierung. Azure folgt deterministisch, live wartet auf Berechtigung oder Speicherfallback Azurite.

<a id="why-amd-mi300x"></a>
## Warum MI300X

Lange Pläne, Logs, Exploitausgaben und Diffs gehen lokal ohne externe API-Latenz oder Datenoffenlegung.

<a id="next-steps"></a>
## Nächste Schritte

- Azure-Regeln für Shared Keys, öffentliches Netz, Key Vault.
- Berechtigung lösen oder Azurite.
- Kubernetes/Compose/On-Premises-Liveadapter mit gleichem Artefaktmodell.
- AMD-Evidenz mit vLLM `/metrics`, `amd-smi` oder `rocm-smi`.
