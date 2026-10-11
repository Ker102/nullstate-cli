<a id="dependency-audit"></a>
# 依存監査

結果は一度きり確認でなく公開証拠です。

<a id="current-result"></a>
## 現在の結果

最新ローカル監査：

```text
Date: 2026-07-02
Command: python -m pip_audit . --skip-editable
Tool: pip-audit 2.10.0
Result: No known vulnerabilities found
```

PR でも開発依存導入後に同じ命令。

<a id="policy"></a>
## 方針

- 新規直接依存の理由を PR に。
- 失敗は範囲、パッケージ、悪用可能性、対策、削除予定日を記載しない限り公開を阻害。
- `--skip-editable` で編集可能メタデータを省き第三者を監査。
- 候補は再実行：

```powershell
python -m pip install -e ".[dev]"
python -m pip_audit . --skip-editable
```

<a id="accepted-risk"></a>
## 受容リスク

現在受容した脆弱依存リスクは未記載。
