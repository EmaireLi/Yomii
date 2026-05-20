# Yomii 后端

Yomii 后端基于 FastAPI + SQLModel，负责账号体系、学习进度、测试报告、作文评测编排，以及 SQLite / MySQL 双数据库接入。

## 技术栈

- FastAPI
- SQLModel / SQLAlchemy
- SQLite + MySQL
- JWT 认证
- 本地作文模型服务编排 + DeepSeek API 兜底

## 目录结构

```text
backend/
├── app/                 # API、模型、服务、配置
├── scripts/             # 初始化和数据处理脚本
├── tests/               # 后端测试
├── training/            # 作文模型训练、合并、量化、服务脚本
├── requirements.txt     # 完整依赖（含模型推理 / 训练）
├── requirements.runtime.txt
└── README.md
```

## 数据库职责

- SQLite：词典、词级、题库等静态数据
- MySQL：用户、收藏、学习进度、测试记录、作文、学习计划等行为数据

## 依赖说明

### 纯后端运行

```powershell
cd backend
pip install -r requirements.runtime.txt
```

适用于：

- 查词
- 背单词
- 测试
- 不启用本地作文模型的 API 开发

### 完整依赖

```powershell
cd backend
pip install -r requirements.txt
```

适用于：

- 本地作文模型推理
- LoRA 训练
- 模型合并与量化

## 启动方式

### 1. 配置根目录 `.env`

至少确认 MySQL 连接：

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=yomii
```

如果启用本地作文模型，还需要：

```env
ESSAY_SCORE_MODEL_URL=http://127.0.0.1:8011/infer
ESSAY_SCORE_MODEL_NAME=qwen3-1.7b-score-merged
ESSAY_REVISION_MODEL_URL=http://127.0.0.1:8012/infer
ESSAY_REVISION_MODEL_NAME=qwen3-1.7b-revision-merged
DEEPSEEK_API_KEY=your_real_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

### 2. 启动 API

```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Swagger：

- [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)

### 3. 可选：启动本地作文模型

评分模型：

```powershell
cd backend
python training\serve_qwen_adapter.py --task score --model models\qwen3-1.7b-score-merged --model-version qwen3-1.7b-score-merged --port 8011 --device-map auto --quantize bnb-nf4
```

修订模型：

```powershell
cd backend
python training\serve_qwen_adapter.py --task revision --model models\qwen3-1.7b-revision-merged --model-version qwen3-1.7b-revision-merged --port 8012 --device-map auto --quantize bnb-nf4
```

## 相关文档

- [仓库入口 README](../README.md)
- [训练与模型服务文档](./training/README.md)
- [API 参考](../docs/02-REFERENCE/API_REFERENCE.md)
- [数据库设计](../docs/DATABASE_DESIGN.md)
