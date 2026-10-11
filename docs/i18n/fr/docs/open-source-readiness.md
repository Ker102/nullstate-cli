<a id="open-source-readiness-milestones"></a>
# Jalons open source

Jalons pratiques avant de promouvoir `nullstate` d'alpha à CLI stable.

Suivi GitHub :

- Jalon 1 : <https://github.com/Ker102/nullstate-cli/milestone/1>
- Jalon 2 : <https://github.com/Ker102/nullstate-cli/milestone/3>
- Jalon 3 : <https://github.com/Ker102/nullstate-cli/milestone/2>

<a id="current-status"></a>
## État actuel

`nullstate` convient aux utilisateurs alpha conscients des backends expérimentaux. AWS est validé avec commandes contraintes. Azure a détection, correction, sondes à manifeste et offline, mais attend habilitation Azure Emulator.

<a id="milestone-1-alpha-publication-readiness"></a>
## Jalon 1 : Publication alpha

Objectif : repo utilisable/compréhensible pour premiers évaluateurs.

État : presque complet.

Critères :

- [x] README clair depuis source/tag actuel.
- [x] Entrée `nullstate` et repli `python -m nullstate`.
- [x] Licence, contribution, conduite, sécurité.
- [x] Templates sûrs sans demande de secrets.
- [x] Quickstart offline sans LocalStack, identifiants cloud Terraform ou modèles.
- [x] Frontières rouges documentées honnêtement.
- [x] Rapports distinguent observation, simulation, inconclusif.
- [x] Exemple assaini sans Docker. Issue #29.

<a id="milestone-2-stable-local-sandbox-validation"></a>
## Jalon 2 : Sandbox locale stable

Objectif : preuve locale fiable.

État : AWS prêt, Azure bloqué par habilitation.

Critères :

- [x] Ressources AWS vulnérables déployées localement.
- [x] `attack.py` AWS lit anonymement avant/après.
- [x] Rapport prouve exploitation puis blocage.
- [x] `sandbox up` échoue si conteneur s'arrête, sans faux succès.
- [x] Échec Azure expliqué clairement.
- [ ] Résoudre habilitation ou remplacer l'émulateur stockage.
- [ ] Prouver lecture Blob en direct avant/blocage après.
- [ ] Si indisponible, Azurite pour `azure-public-blob` stockage seul. Issue #30.

<a id="milestone-3-open-source-stable-cli"></a>
## Jalon 3 : CLI stable

Objectif : installation, exécution et confiance dans le périmètre documenté.

État : incomplet.

Critères :

- [ ] Artefacts installables sans clone.
- [ ] Page wheel, sdist, SBOM, manifeste, attestations et vérification.
- [x] Guide 10 minutes testé proprement.
- [x] Bundle/dashboard assainis.
- [x] Scénarios non directs marqués offline/ébauche.
- [x] Audit/risques documentés.
- [ ] Dry-run Actions avant prochain tag.
- [ ] `pip install` dernier tag expose `nullstate` Windows/Linux.

Notes :

- Windows réussi localement 2026-07-03 : `python scripts/release/install_smoke.py --tag v0.1.0-alpha.2`.
- Linux à confirmer sur runner/dry-run avant clôture.

<a id="azure-emulator-decision"></a>
## Décision Azure Emulator

Le token active assez une licence cache/trial mais le workspace/utilisateur n'a pas droit à l'image. Ce n'est pas une permission Azure cloud, mais une licence LocalStack.

Options :

1. Demander au support l'accès associé à `LOCALSTACK_AUTH_TOKEN`.
2. Azurite Blob V1 couvre lecture publique, pas tout ARM.
3. Petit émulateur interne pour démo : faible risque dépendance, forte maintenance ; nommer simulateur, pas Azure.
4. Azure offline jusqu'à disponibilité, AWS live prioritaire.

Recommandation :

LocalStack Azure si accès rapide ; sinon Azurite stockage Blob seul, ARM futur.
