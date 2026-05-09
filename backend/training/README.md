# 作文双 Adapter 训练说明（8GB 显存）

本目录用于在 `Qwen/Qwen3-1.7B` 上训练两个 LoRA adapter：

- `score-lora`: JLPT 风格作文评分
- `revision-lora`: 作文修改建议与修正版生成

当前项目分两个阶段：

1. 训练阶段：`Qwen3-1.7B + QLoRA 4-bit`
2. 最终接入阶段：后端通过统一接口调用评分和修改服务

如果只是保留项目成果，可以清理训练数据和旧训练缓存，只保留：

- `backend/models/score-lora`
- `backend/models/revision-lora`
- `backend/training/` 下的训练与服务代码

## 1. 安装训练依赖

```powershell
cd backend
pip install -r requirements.txt
pip install -r training\requirements.txt
```

如果你只需要恢复本地模型服务，不重新训练，可以只安装：

```powershell
cd backend
pip install -r requirements-model.txt
```

## 2. 准备原始数据

把原始语料放到：

- `backend/data/essay_raw/naist-lang8/`
- `backend/data/essay_raw/w-coleja/`
- `backend/data/essay_raw/local-essay/`

要求支持 `.json` 或 `.jsonl`。

如果你暂时拿不到有授权门槛的语料，可以先用公开 bootstrap 数据跑通训练：

```powershell
python training\bootstrap_public_essay_data.py `
  --revision-limit 256 `
  --score-limit 128 `
  --score-source grammar-correction `
  --target-level N3
```

这会生成：

- `backend/data/essay_raw/public_revision.jsonl`
- `backend/data/essay_raw/public_score.jsonl`

然后直接按 `local-essay` 源生成训练集：

```powershell
python scripts\prepare_essay_training_data.py `
  --input data\essay_raw\public_revision.jsonl `
  --output data\essay_processed\revision_train.jsonl `
  --source local-essay `
  --task revision `
  --split train

python scripts\prepare_essay_training_data.py `
  --input data\essay_raw\public_revision.jsonl `
  --output data\essay_processed\revision_eval.jsonl `
  --source local-essay `
  --task revision `
  --split eval

python scripts\prepare_essay_training_data.py `
  --input data\essay_raw\public_score.jsonl `
  --output data\essay_processed\score_train.jsonl `
  --source local-essay `
  --task score `
  --split train

python scripts\prepare_essay_training_data.py `
  --input data\essay_raw\public_score.jsonl `
  --output data\essay_processed\score_eval.jsonl `
  --source local-essay `
  --task score `
  --split eval
```

## 3. 生成 revision 样本

```powershell
python scripts\prepare_essay_training_data.py `
  --input data\essay_raw\naist-lang8 `
  --output data\essay_processed\revision_train.jsonl `
  --source naist-lang8 `
  --task revision `
  --split train

python scripts\prepare_essay_training_data.py `
  --input data\essay_raw\naist-lang8 `
  --output data\essay_processed\revision_eval.jsonl `
  --source naist-lang8 `
  --task revision `
  --split eval
```

## 4. 生成 score 原文池

```powershell
python scripts\prepare_essay_training_data.py `
  --input data\essay_raw\w-coleja `
  --output data\essay_teacher\score_teacher_requests.jsonl `
  --source w-coleja `
  --task score `
  --split train `
  --teacher-prompt-only
```

你需要把教师模型返回结果整理成 JSONL，再执行：

```powershell
python training\validate_score_labels.py `
  --input data\essay_teacher\score_teacher_labels_raw.jsonl `
  --valid-output data\essay_teacher\score_teacher_labels_valid.jsonl `
  --rejected-output data\essay_teacher\score_teacher_rejected.jsonl

python training\merge_teacher_labels.py `
  --requests data\essay_teacher\score_teacher_requests.jsonl `
  --labels data\essay_teacher\score_teacher_labels_valid.jsonl `
  --output data\essay_processed\score_train.jsonl `
  --rejected-output data\essay_teacher\score_teacher_rejected_merge.jsonl
```

同理生成 `score_eval.jsonl`。

## 5. 训练 score adapter

```powershell
python training\train_score_lora.py --config training\configs\score_lora.yaml
```

输出目录：

- `backend/models/score-lora/`

## 6. 训练 revision adapter

```powershell
python training\train_revision_lora.py --config training\configs\revision_lora.yaml
```

输出目录：

- `backend/models/revision-lora/`

## 7. 服务接入说明

当前仓库保留了训练和服务代码。默认完整运行时，建议直接启动本地评分模型和修改模型服务。

本地模型服务依赖：

```powershell
cd backend
pip install -r requirements-model.txt
```

本地评分模型：

```powershell
python training\serve_qwen_adapter.py --task score --model models\qwen3-1.7b-gptq-int4 --adapter models\score-lora --model-version qwen3-1.7b-score-lora --port 8011
```

本地修改模型：

```powershell
python training\serve_qwen_adapter.py --task revision --model models\qwen3-1.7b-gptq-int4 --adapter models\revision-lora --model-version qwen3-1.7b-revision-lora --port 8012
```

如果你有现成模型服务，只需要让它提供统一的评分/修改接口，然后在 `backend/.env` 中配置 URL。

如果你不需要接真实模型，直接把 URL 留空，后端会走 mock 结果。

## 8. 配置后端

在 `backend/.env` 中设置：

```env
ESSAY_SCORE_MODEL_URL=http://127.0.0.1:8011/infer
ESSAY_SCORE_MODEL_NAME=qwen3-1.7b-score-lora
ESSAY_REVISION_MODEL_URL=http://127.0.0.1:8012/infer
ESSAY_REVISION_MODEL_NAME=qwen3-1.7b-revision-lora
ESSAY_MODEL_TIMEOUT_SECONDS=45
```

## 9. 说明

- 当前方案是研究原型
- `NAIST Lang-8` / `W-CoLeJa` 当前按研究用途使用
- 后续若要商用，需要替换许可不清晰的数据来源
