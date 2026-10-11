<a id="external-agent-trust-example"></a>
# Ejemplo de confianza de agentes externos

<!-- i18n-switcher:start -->
[English](../../../../../examples/agent-trust/README.md) | [Español](README.md) | [简体中文](../../../zh-CN/examples/agent-trust/README.md) | [Français](../../../fr/examples/agent-trust/README.md) | [日本語](../../../ja/examples/agent-trust/README.md) | [Deutsch](../../../de/examples/agent-trust/README.md) | [Português (Brasil)](../../../pt-BR/examples/agent-trust/README.md)
<!-- i18n-switcher:end -->

Este manifiesto modela un agente IA externo que actúa con identidad de nube propia y autoridad delegada de usuario.

Ejecute:

```bash
nullstate agent posture verify examples/agent-trust/external-agent-manifest.json
nullstate agent blast-radius examples/agent-trust/external-agent-manifest.json
```
