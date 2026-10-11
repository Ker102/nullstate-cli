<a id="contributing"></a>
# Contribuer

<a id="workflow"></a>
## Processus

Utiliser GitHub flow :

1. Créer une issue ou lier une issue existante.
2. Créer une branche : `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>` ou `chore/<short-name>`.
3. Ouvrir une pull request structurée.
4. Attendre CI et la revue.
5. Fusionner par squash vers `main`.

Aucun push direct vers `main`.

<a id="local-setup"></a>
## Installation locale

```powershell
git clone https://github.com/Ker102/nullstate-cli.git
cd nullstate-cli
python -m pip install -e ".[dev]"
nullstate doctor --offline
```

Si la commande console `nullstate` n'est pas dans `PATH`, utiliser :

```powershell
python -m nullstate doctor --offline
```

<a id="local-checks"></a>
## Vérifications locales

```powershell
python -m pip install -e ".[dev]"
python -m ruff check src tests
python -m mypy src
python -m unittest discover -s tests -v
python -m pip_audit
```

Utiliser `pip_audit` comme signal de sécurité, pas comme substitut à la revue. S'il signale une dépendance vulnérable, documenter si le chemin est accessible dans `nullstate`.

<a id="commit-style"></a>
## Style des commits

Utiliser les préfixes conventional commit :

- `feat:`
- `fix:`
- `docs:`
- `test:`
- `chore:`

<a id="pull-request-expectations"></a>
## Attentes pour les pull requests

Chaque PR doit inclure :

- résumé
- preuves de tests
- impact sur la sécurité
- mises à jour documentaires
- captures ou artefacts d'exécution si pertinents

<a id="security-expectations"></a>
## Exigences de sécurité

- Ne pas inclure d'identifiants cloud réels, tokens LocalStack, clés API modèle, fichiers `.env`, état Terraform ou bundles non assainis.
- Utiliser `nullstate scrub` avant partage public des artefacts.
- Garder les attaques locales par défaut. Toute future cible cloud réelle doit être explicite, opt-in, contrôlée par politique et documentée.
- Inclure des tests ciblés pour toute modification de l'exécuteur rouge, des politiques, de l'assainissement, des plans d'upload, du workflow de publication ou des gates CI.
