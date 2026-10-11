<a id="external-agent-trust-example"></a>
# Exemple de confiance d'agent externe

<!-- i18n-switcher:start -->
[English](../../../../../examples/agent-trust/README.md) | [Español](../../../es/examples/agent-trust/README.md) | [简体中文](../../../zh-CN/examples/agent-trust/README.md) | [Français](README.md) | [日本語](../../../ja/examples/agent-trust/README.md) | [Deutsch](../../../de/examples/agent-trust/README.md) | [Português (Brasil)](../../../pt-BR/examples/agent-trust/README.md)
<!-- i18n-switcher:end -->

Ce manifeste modélise un agent hébergé à l'extérieur, avec identité cloud propre et autorité utilisateur déléguée.

Exécuter :

```bash
nullstate agent posture verify examples/agent-trust/external-agent-manifest.json
nullstate agent blast-radius examples/agent-trust/external-agent-manifest.json
```
