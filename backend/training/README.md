# 作文双模型训练与部署说明（8GB 显存）

本目录用于在 `Qwen/Qwen3-1.7B` 上完成：
1. **数据生成** — Teacher 模型直接生成高质量日语作文评分+修改训练数据
2. **训练阶段**（QLoRA 4-bit）— 训练两个 LoRA adapter
3. **合并量化阶段** — 将 adapter 合并回 base model 并 4-bit 量化，生成独立部署模型（无需 PEFT 依赖）

最终产物是两个独立模型（已合并量化）：
- `models/qwen3-1.7b-score-merged/` — JLPT 风格评分（1.3 GB，BNB 4-bit）
- `models/qwen3-1.7b-revision-merged/` — 作文修改建议与修正版生成（1.3 GB，BNB 4-bit）

同时，后端运行阶段已支持第三方 API 参与择优：
- 原文评分：本地评分模型与 `DeepSeek V4 Flash` 同时参与比较，后端择优返回
- 修订结果：本地修订、规则增强修订与 `DeepSeek` 修订共同参与比较，后端按复评分择优返回
- 只有所有候选都不可靠时，才进入最后的规则保底

> 当前模型使用 **398 条 Teacher 生成的高质量训练数据**（覆盖 N5-N1）。LoRA adapter 在合并后已清理，仓库只保留最终模型和训练/服务代码。

## 0. 快速部署（已有模型）

```bash
cd backend

# 安装统一依赖
pip install -r requirements.txt

# 启动评分模型（端口 8011）
python training/serve_qwen_adapter.py --task score --model models/qwen3-1.7b-score-merged --model-version qwen3-1.7b-score-merged --port 8011 --device-map auto --quantize bnb-nf4

# 启动修改模型（端口 8012）
python training/serve_qwen_adapter.py --task revision --model models/qwen3-1.7b-revision-merged --model-version qwen3-1.7b-revision-merged --port 8012 --device-map auto --quantize bnb-nf4

# macOS CPU 模式
python training/serve_qwen_adapter.py --task score --model models/qwen3-1.7b-score-merged --model-version qwen3-1.7b-score-merged --port 8011 --device-map cpu
python training/serve_qwen_adapter.py --task revision --model models/qwen3-1.7b-revision-merged --model-version qwen3-1.7b-revision-merged --port 8012 --device-map cpu

# 启动后端 API（端口 8000）
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 1. 训练流程

### 1.1 生成训练数据

使用内置 Teacher 数据生成器（无需外部 API，无需下载数据集）：

```bash
cd backend
python scripts/local_generate_dataset.py --samples 500
```

生成的数据在 `data/essay_processed/`，包含 score/revision 各约 500 条。

> 当前模型使用 398 条 Teacher 逐个手动生成的高质量数据，也可通过上述脚本扩展。

### 1.2 训练评分模型（Score LoRA）

```bash
cd backend
python training/train_score_lora.py
```

输出：`models/score-lora/`

### 1.3 训练修改模型（Revision LoRA）

```bash
cd backend
python training/train_revision_lora.py
```

输出：`models/revision-lora/`

### 1.4 合并 LoRA → 独立部署模型

```bash
cd backend

# 评分模型
python training/merge_and_quantize.py --base-model Qwen/Qwen3-1.7B --adapter models/score-lora --output-dir models/qwen3-1.7b-score-merged --quantize bnb-nf4 --clean-cache

# 修改模型
python training/merge_and_quantize.py --base-model Qwen/Qwen3-1.7B --adapter models/revision-lora --output-dir models/qwen3-1.7b-revision-merged --quantize bnb-nf4 --clean-cache
```

产物说明：
- `model.safetensors` — BNB 4-bit NF4 量化权重（~1.3GB）
- `config.json`, `tokenizer.json` 等 — 独立推理所需的完整配置
- 合并后 adapter 可删除，后续推理**不再需要 PEFT**

## 2. 效果对比

### 修正前

**作文：**
> 私の趣味は写真を撮りますことです。先月、カメラを買いました。
> 写真を撮るはとても楽しいです。特に、花の写真を撮ることが好きです。
> 休みの日に、公園に行って写真を撮っています。
> 写真を撮りながら、自然を感じることができます。ストレスも解消されます。
> 私は写真をもっと上手になりたいです。将来、写真展を開きたいです。

| 指标 | 分数 |
|------|------|
| 総合 | 76 |
| 文法 | 73 |
| 一貫性 | 76 |
| 自然さ | 74 |
| 推定 | N3 |

**误用：**
- 「撮りますこと」→「撮ること」（動詞の名詞化の誤り）
- 「撮るは」→「撮るのは」（助詞「の」の欠落）

### 修正後

**作文：**
> 私の趣味は写真を撮ることです。先月、カメラを買いました。
> 写真を撮るのはとても楽しいです。特に、花の写真を撮ることが好きです。
> 休みの日に公園に行って写真を撮っています。
> 写真を撮りながら、自然の中を写真に収めることができます。ストレスも解消されます。
> 私は写真をもっと上手に精進したいです。将来、写真展を開きたいです。

| 指标 | 分数 | 変化 |
|------|------|------|
| 総合 | **77** | **+1** |
| 文法 | 73 | — |
| 一貫性 | **77** | **+1** |
| 自然さ | 74 | — |
| 推定 | N3 | — |

## 3. 配置后端

在项目根目录 `.env` 中设置：

```env
ESSAY_SCORE_MODEL_URL=http://127.0.0.1:8011/infer
ESSAY_SCORE_MODEL_NAME=qwen3-1.7b-score-merged
ESSAY_REVISION_MODEL_URL=http://127.0.0.1:8012/infer
ESSAY_REVISION_MODEL_NAME=qwen3-1.7b-revision-merged
ESSAY_MODEL_TIMEOUT_SECONDS=180
```

## 4. 兼容性问题记录

### 4.1 gptqmodel + transformers 兼容

`gptqmodel==7.0.0` + `transformers==5.x` 下，AWQ 量化线性类名变更，PEFT 加载时按旧名导入失败。在 `merge_and_quantize.py` 中通过 compat shim 修复。

### 4.2 Windows 符号链接限制

HF hub 在 Windows 上默认使用符号链接管理缓存。使用 `HF_HUB_DISABLE_SYMLINKS_WARNING=1` 抑制警告，配合 `--clean-cache` 清理冗余缓存。

### 4.3 退出时 ResourceTracker 异常

Windows 上 Python 退出时 `multiprocess.resource_tracker` 报错，是第三方库已知问题，不影响训练结果，可忽略。

## 5. 说明

- 当前模型使用 398 条 Teacher 手动生成的高质量训练数据
- 如需更多数据，可用 `scripts/local_generate_dataset.py` 扩展到任意数量
- 后续优化方向：增加数据多样性、优化 LoRA 超参数
