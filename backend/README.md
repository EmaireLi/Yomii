# Yomii 后端

基于 FastAPI + SQLModel 构建的 Yomii 日语学习应用后端 API。

## 技术栈

- **框架**: FastAPI
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **数据库**: 
  - **SQLite**: 词典数据（单词、测试题目）
  - **MySQL**: 用户行为数据（用户、进度、作文、学习计划）
- **认证**: JWT (python-jose)
- **AI 集成**: 日语作文双模型编排（评分模型 + 修改模型）

## 双数据库架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Yomii Backend                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐    ┌─────────────────────────────┐ │
│  │   SQLite (词典库)    │    │     MySQL (用户行为库)       │ │
│  ├─────────────────────┤    ├─────────────────────────────┤ │
│  │ • words             │    │ • users                     │ │
│  │ • word_tags         │    │ • favorites                 │ │
│  │ • quiz_questions    │    │ • search_history            │ │
│  │                     │    │ • word_progress             │ │
│  │ 📁 data/dictionary.db│    │ • study_stats               │ │
│  │                     │    │ • quiz_results              │ │
│  │                     │    │ • essays / essay_scores     │ │
│  │                     │    │ • essay_revisions           │ │
│  │                     │    │ • essay_jobs                │ │
│  │                     │    │ • study_plans / sessions    │ │
│  └─────────────────────┘    └─────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 项目结构

```
backend/
├── app/
│   ├── api/v1/endpoints/     # API 端点
│   │   ├── auth.py           # 认证 (MySQL)
│   │   ├── words.py          # 单词 (SQLite)
│   │   ├── quiz.py           # 测试 (SQLite + MySQL)
│   │   ├── essays.py         # 作文评测 (MySQL)
│   │   ├── user.py           # 用户 (MySQL)
│   │   └── study_plans.py    # 学习计划 (MySQL + SQLite)
│   ├── core/
│   │   ├── config.py         # 配置管理
│   │   ├── security.py       # JWT 认证
│   │   └── deps.py           # 依赖注入 (DictDB/UserDB)
│   ├── db/session.py         # 双数据库会话管理
│   ├── models/               # 数据模型
│   ├── schemas/              # API Schemas
│   ├── services/             # 业务服务（含作文双模型编排）
│   └── main.py               # FastAPI 入口
├── data/                     # SQLite 数据目录
├── tests/
├── requirements.txt
└── .env.example
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

如果你后续要恢复本地模型服务，再额外安装：

```bash
pip install -r requirements-model.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填写 MySQL 连接信息
```

最少需要确认：

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=yomii
```

作文双模型原型新增配置：

```env
ESSAY_SCORE_MODEL_URL=http://127.0.0.1:8011/infer
ESSAY_SCORE_MODEL_NAME=qwen3-1.7b-score-lora
ESSAY_REVISION_MODEL_URL=http://127.0.0.1:8012/infer
ESSAY_REVISION_MODEL_NAME=qwen3-1.7b-revision-lora
ESSAY_MODEL_TIMEOUT_SECONDS=30
```

说明：
- `ESSAY_SCORE_MODEL_URL`：后端调用评分模型时使用的 HTTP 地址
- `ESSAY_REVISION_MODEL_URL`：后端调用修改模型时使用的 HTTP 地址
- 这里配置的是“调用目标”，不是“自动启动服务”
- 默认应启动本地评分模型和修改模型服务，并使用上述本地地址
- 如果你已经有现成模型服务，可以把这两个 URL 改成对应的接口地址
- 两个 URL 都留空时，后端自动走 mock 评分与 mock 修改结果
- 模型服务额外依赖放在 `requirements-model.txt`

### 3. 启动 MySQL

```bash
# 使用 Docker 启动 MySQL
docker run -d \
  --name yomii-mysql \
  -e MYSQL_ROOT_PASSWORD=password \
  -e MYSQL_DATABASE=yomii \
  -p 3306:3306 \
  mysql:8
```

### 4. 运行应用

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

SQLite 数据库会自动在 `data/dictionary.db` 创建。
MySQL 表结构会在启动时自动补齐，包括作文双模型新增的：
- `essays.status / target_level / evaluation_*`
- `essay_scores` 新评分字段
- `essay_revisions`
- `essay_jobs`

### 5. 访问 API 文档

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 启动顺序（标准后端模式）

先区分两件事：

1. `.env`：告诉后端“去哪个地址找模型”
2. 启动命令：真正把后端进程跑起来

当前仓库的推荐方式是：

- 默认启动本地评分模型和修改模型服务
- 或者把 URL 指向现成接口，由后端调用
- 只有在不需要真实模型时，才把 URL 留空走 mock

### 终端 1：后端

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 终端 2：评分模型

```powershell
cd backend
pip install -r requirements-model.txt
python training\serve_qwen_adapter.py --task score --model models\qwen3-1.7b-gptq-int4 --adapter models\score-lora --model-version qwen3-1.7b-score-lora --port 8011
```

### 终端 3：修改模型

```powershell
cd backend
pip install -r requirements-model.txt
python training\serve_qwen_adapter.py --task revision --model models\qwen3-1.7b-gptq-int4 --adapter models\revision-lora --model-version qwen3-1.7b-revision-lora --port 8012
```

### 对应 `.env`

```env
ESSAY_SCORE_MODEL_URL=http://127.0.0.1:8011/infer
ESSAY_SCORE_MODEL_NAME=qwen3-1.7b-score-lora
ESSAY_REVISION_MODEL_URL=http://127.0.0.1:8012/infer
ESSAY_REVISION_MODEL_NAME=qwen3-1.7b-revision-lora
ESSAY_MODEL_TIMEOUT_SECONDS=45
```

### 常用命令速查

标准模式：

```powershell
# 终端 1：后端
cd yomii\backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
# 终端 2：评分模型
cd yomii\backend
pip install -r requirements-model.txt
python training\serve_qwen_adapter.py --task score --model models\qwen3-1.7b-gptq-int4 --adapter models\score-lora --model-version qwen3-1.7b-score-lora --port 8011
```

```powershell
# 终端 3：修改模型
cd yomii\backend
pip install -r requirements-model.txt
python training\serve_qwen_adapter.py --task revision --model models\qwen3-1.7b-gptq-int4 --adapter models\revision-lora --model-version qwen3-1.7b-revision-lora --port 8012
```

仅联调模式：

```powershell
# 终端 1：后端（确保 .env 中两个模型 URL 为空）
cd yomii\backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 数据库说明

### SQLite (词典数据)
- 存放静态词典数据，便于分发和更新
- 表: `words`, `word_tags`, `quiz_questions`
- 文件: `data/dictionary.db`

### MySQL (用户行为数据)
- 存放用户生成的数据，支持高并发
- 表: `users`, `favorites`, `search_history`, `word_progress`, `study_stats`, `quiz_results`, `essays`, `essay_scores`, `essay_revisions`, `essay_jobs`, `study_plans`, `learning_sessions`

## 作文双模型接口

当前作文模块已经改成异步双模型流程：

1. 用户提交作文
2. 后端保存作文并创建 `essay_jobs`
3. 评分模型返回 JLPT 风格结构化评分
4. 修改模型返回问题列表、逐句建议和修正版
5. 前端轮询或刷新历史记录查看最终报告

## 训练与最终部署说明

当前项目区分两个阶段：

1. 训练阶段：使用 `Qwen3-1.7B + QLoRA 4-bit` 分别训练 `score-lora` 和 `revision-lora`
2. 最终接入阶段：后端通过统一作文接口调用评分和修改服务，服务可以是 mock、现成模型服务，或后续你自己的推理服务

为了控制磁盘占用，训练完成后可以清理：

- `backend/data/essay_raw`
- `backend/data/essay_processed`
- `backend/data/essay_teacher`
- 旧的 Hugging Face 训练缓存
- 旧的 `Qwen3-1.7B` 全量底座缓存

最终部署只保留：

- `backend/models/score-lora`
- `backend/models/revision-lora`
- `backend/training/` 下的训练和服务代码
- `backend/requirements-model.txt` 作为可选本地模型运行依赖清单

### 主要接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/essays/submit` | 提交作文并自动触发评测 |
| `POST` | `/api/essays/{essay_id}/evaluate` | 手动重新触发评测 |
| `GET` | `/api/essays/{essay_id}/report` | 获取完整评分报告和修改建议 |
| `GET` | `/api/essays/{essay_id}/score` | 兼容旧前端，仅返回评分摘要 |
| `GET` | `/api/essays/history` | 获取作文历史记录与状态 |

### 评分模型服务协议

后端会向 `ESSAY_SCORE_MODEL_URL` 发送：

```json
{
  "task": "jlpt_essay_scoring",
  "topic": "daily-life",
  "target_level": "N3",
  "content": "..."
}
```

期望返回：

```json
{
  "overall_score": 82,
  "task_completion_score": 84,
  "grammar_score": 80,
  "vocabulary_score": 81,
  "coherence_score": 83,
  "naturalness_score": 79,
  "jlpt_fit_score": 82,
  "level_estimate": "N3",
  "summary": "......",
  "comments": "......",
  "model_version": "score-model-v1"
}
```

### 修改模型服务协议

后端会向 `ESSAY_REVISION_MODEL_URL` 发送：

```json
{
  "task": "jlpt_essay_revision",
  "topic": "daily-life",
  "target_level": "N3",
  "content": "...",
  "score_report": {
    "overall_score": 82
  }
}
```

期望返回：

```json
{
  "issues": [
    {
      "source": "...",
      "suggestion": "...",
      "explanation": "...",
      "severity": "medium"
    }
  ],
  "sentence_suggestions": [
    {
      "original": "...",
      "suggested": "...",
      "reason": "..."
    }
  ],
  "full_revision": "...",
  "revision_notes": "...",
  "model_version": "revision-model-v1"
}
```

## 8GB 显存训练方案

当前本地训练默认方案：

- base model: `Qwen/Qwen3-1.7B`
- 训练方式: `4-bit QLoRA`
- 双 adapter:
  - `score-lora`
  - `revision-lora`

训练脚本位于：

- `backend/training/train_score_lora.py`
- `backend/training/train_revision_lora.py`
- `backend/training/serve_qwen_adapter.py`

完整训练流程见：

- `backend/training/README.md`

## 训练数据整理脚本

新增了公开语料整理脚本：

`backend/scripts/prepare_essay_training_data.py`

用途：
- 把公开纠错/改写语料转成修改模型训练样本
- 把作文语料转成评分模型训练样本
- 为评分任务生成教师打标 prompt

### 用法

```bash
cd backend

# 整理修改模型训练样本
python scripts/prepare_essay_training_data.py ^
  --input data/revision_source.jsonl ^
  --output data/revision_train.jsonl ^
  --source naist-lang8 ^
  --task revision

# 整理评分模型训练样本
python scripts/prepare_essay_training_data.py ^
  --input data/score_source.jsonl ^
  --output data/score_train.jsonl ^
  --source local-essay ^
  --task score

# 仅生成教师打标 prompt
python scripts/prepare_essay_training_data.py ^
  --input data/score_source.jsonl ^
  --output data/score_teacher_prompts.jsonl ^
  --source w-coleja ^
  --task score ^
  --teacher-prompt-only
```

Windows PowerShell 也可以写成单行：

```powershell
python scripts/prepare_essay_training_data.py --input data/score_source.jsonl --output data/score_train.jsonl --source local-essay --task score --split train
```

## 许可证

MIT
