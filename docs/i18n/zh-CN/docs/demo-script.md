<a id="demo-script"></a>
# 演示脚本

<a id="60-second-version"></a>
## 60 秒版本

1. “这是 `nullstate`，本地优先 Terraform 安全验证紫队 CLI。”
2. “读取 IaC、运行本地沙箱、模型红/蓝推理、执行允许攻击脚本、确定性修补并验证阻断。”
3. 运行：

```powershell
python -m nullstate
python -m nullstate status
python -m nullstate run examples/aws-public-s3 --target localstack-aws --runs-dir runs/final-aws-gemma26b --red-model nullstate-gemma4-26b-a4b --blue-model nullstate-gemma4-26b-a4b
python -m nullstate report --runs-dir runs/final-aws-gemma26b
```

4. 展示终端摘要：
   - 发现数
   - 红队前：成功
   - 红队后：阻断
   - 产物路径
5. 展示 `events.jsonl` 的 `red-tool`：命令、stdout、stderr、返回码、URL、时间戳。
6. 展示报告和运行路径。可用 `python -m nullstate report` 或 `python -m nullstate report <run-id> --runs-dir runs` 重开。

<a id="mi300x-talking-points"></a>
## MI300X 要点

- 面向大型 IaC 计划和长日志。
- MI300X 通过兼容 vLLM/SGLang 做蓝队长上下文分析。
- 确定性核心保持判定可复现；模型提供推理、解释、修复背景。
- 用户无需手写提示，发送角色指令和证据。
- token 来自 API 用量和可用 vLLM Prometheus。
- 红队执行限运行目录生成的 `attack.py`。

<a id="fallback-path"></a>
## 备用

LocalStack Azure 或模型不可用时用 `--offline`，CLI/报告仍可用。

<a id="live-sandbox-shot"></a>
## 实际沙箱镜头

配置后展示引导流程。AWS/Azure 顺序运行，均占 edge 端口 `4566`。

```powershell
python -m nullstate sandbox up localstack-aws
python -m nullstate sandbox status localstack-aws
python -m nullstate run examples/aws-public-s3 --target localstack-aws --runs-dir runs/final-aws-gemma26b --red-model nullstate-gemma4-26b-a4b --blue-model nullstate-gemma4-26b-a4b
python -m nullstate report --runs-dir runs/final-aws-gemma26b

python -m nullstate sandbox down localstack-aws

python -m nullstate sandbox up localstack-azure
python -m nullstate sandbox status localstack-azure
python -m nullstate run examples/azure-public-blob --target localstack-azure --runs-dir runs/final-azure-gemma26b --red-model nullstate-gemma4-26b-a4b --blue-model nullstate-gemma4-26b-a4b
python -m nullstate report --runs-dir runs/final-azure-gemma26b
```

`LOCALSTACK_AUTH_TOKEN` 放 `.env.local`、`.env` 或 shell，录制不展示值。

<a id="accuracy-note"></a>
## 准确性

不要说红队模型有无限 shell。V1 模型只推理，nullstate 仅运行目录生成 `attack.py` 对配置本地目标。
