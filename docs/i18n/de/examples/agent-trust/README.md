<a id="external-agent-trust-example"></a>
# Beispiel externer Agentenvertrauensprüfung

<!-- i18n-switcher:start -->
[English](../../../../../examples/agent-trust/README.md) | [Español](../../../es/examples/agent-trust/README.md) | [简体中文](../../../zh-CN/examples/agent-trust/README.md) | [Français](../../../fr/examples/agent-trust/README.md) | [日本語](../../../ja/examples/agent-trust/README.md) | [Deutsch](README.md) | [Português (Brasil)](../../../pt-BR/examples/agent-trust/README.md)
<!-- i18n-switcher:end -->

Das Manifest modelliert einen externen KI-Agenten mit eigener Cloud-ID und Nutzerdelegation.

Ausführen:

```bash
nullstate agent posture verify examples/agent-trust/external-agent-manifest.json
nullstate agent blast-radius examples/agent-trust/external-agent-manifest.json
```
