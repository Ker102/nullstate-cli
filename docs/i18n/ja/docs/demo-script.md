<a id="demo-script"></a>
# デモ台本

<a id="60-second-version"></a>
## 60 秒版

1. 「`nullstate` はローカル優先 Terraform 安全検証 CLI です。」
2. 「IaC 読取、ローカル環境、赤青推論、許可攻撃、決定論的修正、遮断検証を行います。」
3. 実行：

```powershell
python -m nullstate
python -m nullstate status
python -m nullstate run examples/aws-public-s3 --target localstack-aws --runs-dir runs/final-aws-gemma26b --red-model nullstate-gemma4-26b-a4b --blue-model nullstate-gemma4-26b-a4b
python -m nullstate report --runs-dir runs/final-aws-gemma26b
```

4. 概要を表示：
   - 検出数
   - 修正前：成功
   - 修正後：遮断
   - 成果物パス
5. `events.jsonl` の `red-tool`、命令、stdout、stderr、終了、URL、時刻を示す。
6. 報告と実行ディレクトリ。`python -m nullstate report` または `python -m nullstate report <run-id> --runs-dir runs` で再表示。

<a id="mi300x-talking-points"></a>
## MI300X 要点

- 大規模 IaC と長ログ向け。
- 互換 vLLM/SGLang で長文ブルー分析。
- 決定論的判定とモデルの推論/説明/修正文脈。
- 手動プロンプト不要。ロール指示と証拠。
- API 使用量と利用可能な vLLM 指標。
- 実行内生成 `attack.py` のみ。

<a id="fallback-path"></a>
## 代替

Azure/モデルなしは `--offline`。同じ流れ。

<a id="live-sandbox-shot"></a>
## 実環境撮影

設定後に手順を示し AWS/Azure は順番。共通 edge `4566`。

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

`LOCALSTACK_AUTH_TOKEN` は `.env.local`、`.env`、シェル、値を映さない。

<a id="accuracy-note"></a>
## 正確性

無制限シェルと言わない。モデルは推論し、nullstate は実行内 `attack.py` を設定ローカル対象のみに実行。
