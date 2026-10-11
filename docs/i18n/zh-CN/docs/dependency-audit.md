<a id="dependency-audit"></a>
# 依赖审计

审计结果是发布证据，不是一次性打勾。

<a id="current-result"></a>
## 当前结果

上次本地审计：

```text
Date: 2026-07-02
Command: python -m pip_audit . --skip-editable
Tool: pip-audit 2.10.0
Result: No known vulnerabilities found
```

PR workflow 安装开发依赖后运行同一命令。

<a id="policy"></a>
## 策略

- 新直接依赖需在 PR 说明理由。
- 审计失败阻止发布就绪，除非记录范围、包、可利用性、缓解和计划移除日期。
- `--skip-editable` 跳过可编辑元数据，审计已装第三方包。
- 发布候选应重跑：

```powershell
python -m pip install -e ".[dev]"
python -m pip_audit . --skip-editable
```

<a id="accepted-risk"></a>
## 接受风险

当前未记录接受的漏洞依赖风险。
