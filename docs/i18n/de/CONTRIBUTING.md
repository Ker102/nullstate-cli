<a id="contributing"></a>
# Beiträge

<a id="workflow"></a>
## Workflow

GitHub flow verwenden:

1. Ein Issue erstellen oder ein bestehendes verlinken.
2. Branch erstellen: `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>` oder `chore/<short-name>`.
3. Strukturierten Pull Request öffnen.
4. CI und Review abwarten.
5. Per Squash nach `main` mergen.

Keine direkten Pushes nach `main`.

<a id="local-setup"></a>
## Lokale Einrichtung

```powershell
git clone https://github.com/Ker102/nullstate-cli.git
cd nullstate-cli
python -m pip install -e ".[dev]"
nullstate doctor --offline
```

Ist `nullstate` nicht in `PATH`, verwenden:

```powershell
python -m nullstate doctor --offline
```

<a id="local-checks"></a>
## Lokale Prüfungen

```powershell
python -m pip install -e ".[dev]"
python -m ruff check src tests
python -m mypy src
python -m unittest discover -s tests -v
python -m pip_audit
```

`pip_audit` ist ein Sicherheitssignal, kein Review-Ersatz. Bei Abhängigkeitsproblemen dokumentieren, ob der verwundbare Pfad in `nullstate` erreichbar ist.

<a id="commit-style"></a>
## Commit-Stil

Conventional-Commit-Präfixe verwenden:

- `feat:`
- `fix:`
- `docs:`
- `test:`
- `chore:`

<a id="pull-request-expectations"></a>
## Pull-Request-Anforderungen

Jeder PR sollte enthalten:

- Zusammenfassung
- Testevidenz
- Sicherheitsauswirkungen
- Dokumentationsänderungen
- relevante Screenshots oder Ausführungsartefakte

<a id="security-expectations"></a>
## Sicherheitsanforderungen

- Keine echten Cloud-Zugangsdaten, LocalStack-Tokens, Modell-API-Keys, `.env`-Dateien, Terraform-State oder unbereinigten Bundles aufnehmen.
- Vor öffentlichem Teilen `nullstate scrub` verwenden.
- Angriffe standardmäßig lokal halten. Künftige echte Cloud-Ziele müssen explizit, opt-in, richtlinienkontrolliert und dokumentiert sein.
- Änderungen an Red-Runner, Richtlinien, Artefaktbereinigung, Uploadplanung, Release-Workflow oder CI-Gates benötigen gezielte Tests.
