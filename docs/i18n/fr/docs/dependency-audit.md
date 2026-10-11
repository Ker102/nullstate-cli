<a id="dependency-audit"></a>
# Audit des dépendances

Les résultats sont des preuves de release, pas une case unique.

<a id="current-result"></a>
## Résultat actuel

Dernier audit local :

```text
Date: 2026-07-02
Command: python -m pip_audit . --skip-editable
Tool: pip-audit 2.10.0
Result: No known vulnerabilities found
```

Le workflow PR lance la même commande après installation dev.

<a id="policy"></a>
## Politique

- Justifier toute dépendance directe nouvelle dans le PR.
- Échec bloquant sauf documentation du périmètre, package, exploitabilité, mitigation et date de retrait.
- `--skip-editable` ignore les métadonnées éditables pour cibler les tiers installés.
- Les candidats doivent relancer :

```powershell
python -m pip install -e ".[dev]"
python -m pip_audit . --skip-editable
```

<a id="accepted-risk"></a>
## Risque accepté

Aucun risque accepté de dépendance vulnérable n'est documenté.
