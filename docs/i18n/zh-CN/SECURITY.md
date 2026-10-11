<a id="security-policy"></a>
# 安全策略

<a id="supported-versions"></a>
## 支持版本

`nullstate` 尚未达到 1.0。安全修复面向最新 `main` 分支；需向评估者发布修复时，也面向最新预发布标签。

| 版本 | 支持情况 |
|---|---|
| `main` | 是 |
| 最新预发布 | 是 |
| 更早预发布 | 尽力支持 |

<a id="reporting-a-vulnerability"></a>
## 报告漏洞

不要为 nullstate 自身可利用漏洞创建公开 issue。请私下联系维护者，或在仓库已启用时使用 GitHub 私密漏洞报告。仅在修复或缓解措施可用后公开详情。

<a id="security-boundaries"></a>
## 安全边界

nullstate 旨在测试故意存在漏洞的本地沙箱。除非操作者拥有环境且理解风险，否则不得将其指向生产基础设施。

V1 默认：

- 默认不执行真实 Azure 操作
- 仅在明确启动时使用 LocalStack/Docker 沙箱
- 运行产物是本地文件
- 秘密通过环境变量提供，不放入提交文件
- 受限红队探测仅执行运行目录生成的 `attack.py`
- 非本地 HTTP 探测目标需要操作者明确批准及策略控制

<a id="secret-handling"></a>
## 秘密处理

绝不提交：

- `LOCALSTACK_AUTH_TOKEN`
- 模型 API key
- 云凭据
- Terraform state
- `.env`
- 真实 `.tfvars`

使用 `.env.example` 记录配置。

向 issue、工单、案例研究或支持请求附上运行产物前：

```powershell
nullstate scrub
```

附上 `scrubbed-runs/` 中的脱敏副本，而非原始 `runs/` 目录。
