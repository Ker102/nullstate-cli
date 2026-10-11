<a id="amd-compute-strategy"></a>
# AMD 計算戦略

<a id="decision"></a>
## 判断

主経路は難しい AMD Developer Cloud / DigitalOcean、GPU 遅延時 Fireworks AI 代替。

<a id="why-primary-path-is-digitaloceanamd-developer-cloud"></a>
## 主経路の理由

- serving、ROCm、vLLM/SGLang、GPU 観測、運用の強い証拠。
- 実 DevOps、クラウド、安全境界、推論で学習。
- 機密 IaC/証拠の私有/自主管理推論を支持。
- API 呼出だけより豊富な事例。

<a id="why-fireworks-stays-as-fallback"></a>
## Fireworks の理由

- AMD 待ちを解消。
- 互換 URL で赤青ループ。
- AMD に関連するが管理推論と説明し私設としない。

<a id="execution-plan"></a>
## 計画

<a id="track-a---digitalocean-baseline-without-gpu"></a>
### 経路 A - GPU なし DigitalOcean

先に準備：

- プロジェクト秘密
- 強化 droplet/ホスト
- Docker/Compose
- Azure LocalStack
- CLI
- Actions 環境
- 成果物保存
- 監視/ログ

GPU 前でも有用。

<a id="track-b---amd-gpu-inference"></a>
### 経路 B - AMD GPU

MI300X が利用可能なら：

- AMD/DigitalOcean GPU 配備
- ROCm/提供者イメージ
- vLLM/SGLang 互換 API
- 操作者に必要 API のみ公開
- モデル、文脈、ROCm、GPU、メモリ、速度、遅延記録
- vLLM `/metrics` と `amd-smi` または `rocm-smi` 保存

<a id="track-c---fireworks-contingency"></a>
### 経路 C - Fireworks

GPU が提出を妨げたら：

- `NULLSTATE_LLM_BASE_URL` を設定
- 同じデモ
- 管理代替と明記
- AMD を次目標とし妨げを隠さない

<a id="demo-positioning"></a>
## デモ説明

推奨説明：

```text
nullstate runs local IaC security validation and can use a private AMD MI300X-hosted model endpoint for red/blue reasoning over security evidence.
```

代替説明：

```text
nullstate is model-provider portable through OpenAI-compatible endpoints. The same CLI can run against managed inference while the private AMD GPU endpoint is being provisioned.
```

<a id="evidence-checklist"></a>
## 証拠

- `runs/<id>/report.md`
- `runs/<id>/metrics.json`
- vLLM `/metrics` 前後
- `amd-smi` または `rocm-smi`
- ROCm 版
- 起動命令
- 処理済みネットワーク図
- GPU/CLI 画像
- AMD、モック、Fireworks を記載

<a id="risks"></a>
## リスク

| リスク | 影響 | 対策 |
|---|---|---|
| AMD 遅延 | 高 | DO/Fireworks |
| GPU/ROCm 不一致 | 中 | 提供者/正確版 |
| モデル過大/低速 | 中 | 両役一モデル |
| 公開 URL | 高 | 流入制限、token、境界 |
| 私設推論誇張 | 高 | 実 URL 種別記載 |
