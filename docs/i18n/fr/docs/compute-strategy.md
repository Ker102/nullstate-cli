<a id="amd-compute-strategy"></a>
# Stratégie de calcul AMD

<a id="decision"></a>
## Décision

Choisir AMD Developer Cloud / DigitalOcean comme voie principale plus exigeante ; Fireworks AI en secours si GPU retardé.

<a id="why-primary-path-is-digitaloceanamd-developer-cloud"></a>
## Pourquoi DigitalOcean/AMD

- Preuves fortes : serving, ROCm, vLLM/SGLang, observabilité GPU, opérations.
- Meilleur apprentissage : vrai DevOps, accès cloud, frontières et inférence.
- Inférence privée/contrôlée pour IaC sensible.
- Étude plus riche qu'un appel API hébergé.

<a id="why-fireworks-stays-as-fallback"></a>
## Pourquoi Fireworks

- Débloque si AMD tarde.
- Boucle rouge/bleu via OpenAI-compatible.
- Pertinent AMD mais à présenter comme managé, pas privé.

<a id="execution-plan"></a>
## Plan

<a id="track-a---digitalocean-baseline-without-gpu"></a>
### Voie A - DigitalOcean sans GPU

Préparer d'abord :

- secrets projet/repo
- droplet de contrôle/hôte durci
- Docker/Compose
- sandbox Azure LocalStack
- CLI nullstate
- environnement Actions
- stockage artefacts
- monitoring/logs

Utile avant GPU.

<a id="track-b---amd-gpu-inference"></a>
### Voie B - GPU AMD

Avec MI300X :

- instance GPU AMD/DigitalOcean
- ROCm ou image fournisseur
- vLLM/SGLang compatible
- exposer seulement API nécessaire à l'opérateur
- noter modèle, contexte, ROCm, GPU, mémoire, débit, latence
- conserver `/metrics` vLLM et `amd-smi` ou `rocm-smi`

<a id="track-c---fireworks-contingency"></a>
### Voie C - Secours Fireworks

Si GPU bloque :

- configurer `NULLSTATE_LLM_BASE_URL` Fireworks
- même démo
- documenter le repli managé
- AMD comme prochain jalon, sans cacher le blocage

<a id="demo-positioning"></a>
## Présentation

Récit préféré :

```text
nullstate runs local IaC security validation and can use a private AMD MI300X-hosted model endpoint for red/blue reasoning over security evidence.
```

Récit de repli :

```text
nullstate is model-provider portable through OpenAI-compatible endpoints. The same CLI can run against managed inference while the private AMD GPU endpoint is being provisioned.
```

<a id="evidence-checklist"></a>
## Preuves

- `runs/<id>/report.md`
- `runs/<id>/metrics.json`
- vLLM `/metrics` avant/après
- `amd-smi` ou `rocm-smi`
- version ROCm
- lancement serveur
- réseau assaini
- captures GPU/CLI
- préciser AMD, mock ou Fireworks

<a id="risks"></a>
## Risques

| Risque | Impact | Mitigation |
|---|---|---|
| Accès AMD retardé | Élevé | baseline DO/Fireworks |
| Image GPU/ROCm incompatible | Moyen | image fournisseur, versions exactes |
| Modèle trop grand/lent | Moyen | un modèle pour deux rôles |
| Endpoint public | Élevé | ingress restreint, token, frontière |
| Inférence privée exagérée | Élevé | type réel par run |
