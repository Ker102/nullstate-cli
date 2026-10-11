<a id="security-policy"></a>
# Politique de sécurité

<a id="supported-versions"></a>
## Versions prises en charge

`nullstate` est antérieur à 1.0. Les correctifs visent le dernier état de `main` et le tag de préversion le plus récent lorsqu'une publication pour les évaluateurs est nécessaire.

| Version | Support |
|---|---|
| `main` | oui |
| dernière préversion | oui |
| anciennes préversions | au mieux |

<a id="reporting-a-vulnerability"></a>
## Signaler une vulnérabilité

Ne pas ouvrir d'issue publique pour une vulnérabilité exploitable de nullstate. Contacter le mainteneur en privé ou utiliser le signalement privé GitHub s'il est activé. Publier les détails seulement après disponibilité d'un correctif ou d'une mitigation.

<a id="security-boundaries"></a>
## Frontières de sécurité

nullstate teste des sandboxes locales volontairement vulnérables. Ne pas le diriger vers la production sauf si l'opérateur possède l'environnement et comprend les risques.

Valeurs par défaut V1 :

- aucune exécution Azure réelle par défaut
- sandboxes LocalStack/Docker seulement lorsqu'elles sont démarrées explicitement
- artefacts stockés en fichiers locaux
- secrets fournis via variables d'environnement, pas fichiers commités
- sondes rouges contraintes exécutant seulement le `attack.py` généré dans le répertoire d'exécution
- cibles HTTP non locales nécessitant approbation explicite et contrôles de politique

<a id="secret-handling"></a>
## Gestion des secrets

Ne jamais committer :

- `LOCALSTACK_AUTH_TOKEN`
- clés API modèle
- identifiants cloud
- état Terraform
- `.env`
- vrais fichiers `.tfvars`

Utiliser `.env.example` pour documenter la configuration.

Avant de joindre des artefacts aux issues, tickets, études de cas ou demandes de support :

```powershell
nullstate scrub
```

Joindre la copie assainie de `scrubbed-runs/`, pas le répertoire brut `runs/`.
