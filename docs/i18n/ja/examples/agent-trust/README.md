<a id="external-agent-trust-example"></a>
# 外部代理信頼の例

<!-- i18n-switcher:start -->
[English](../../../../../examples/agent-trust/README.md) | [Español](../../../es/examples/agent-trust/README.md) | [简体中文](../../../zh-CN/examples/agent-trust/README.md) | [Français](../../../fr/examples/agent-trust/README.md) | [日本語](README.md) | [Deutsch](../../../de/examples/agent-trust/README.md) | [Português (Brasil)](../../../pt-BR/examples/agent-trust/README.md)
<!-- i18n-switcher:end -->

自身のクラウド ID と利用者委任で動く外部ホスト AI をモデル化します。

実行：

```bash
nullstate agent posture verify examples/agent-trust/external-agent-manifest.json
nullstate agent blast-radius examples/agent-trust/external-agent-manifest.json
```
