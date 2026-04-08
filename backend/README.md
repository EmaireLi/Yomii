# Yomii 后端

基于 FastAPI + SQLModel 构建的 Yomii 日语学习应用后端 API。

## 技术栈

- **框架**: FastAPI
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **数据库**: 
  - **SQLite**: 词典数据（单词、测试题目）
  - **MySQL**: 用户行为数据（用户、进度、作文、学习计划）
- **认证**: JWT (python-jose)
- **AI 集成**: 预训练模型微调

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
│  │ • word_tags         │    │ • word_progress             │ │
│  │ • quiz_questions    │    │ • quiz_results              │ │
│  │                     │    │ • essays                    │ │
│  │ 📁 data/dictionary.db│    │ • essay_scores              │ │
│  │                     │    │ • study_plans               │ │
│  │                     │    │ • learning_sessions         │ │
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
│   │   ├── essays.py         # 作文 (MySQL)
│   │   ├── user.py           # 用户 (MySQL)
│   │   └── study_plans.py    # 学习计划 (MySQL + SQLite)
│   ├── core/
│   │   ├── config.py         # 配置管理
│   │   ├── security.py       # JWT 认证
│   │   └── deps.py           # 依赖注入 (DictDB/UserDB)
│   ├── db/session.py         # 双数据库会话管理
│   ├── models/               # 数据模型
│   ├── schemas/              # API Schemas
│   ├── services/             # 业务服务
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
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填写 MySQL 连接信息
```

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
uvicorn app.main:app --reload --host 0.0.0.0 --port 3000
```

SQLite 数据库会自动在 `data/dictionary.db` 创建。

### 5. 访问 API 文档

- Swagger UI: http://localhost:3000/api/docs
- ReDoc: http://localhost:3000/api/redoc

## 数据库说明

### SQLite (词典数据)
- 存放静态词典数据，便于分发和更新
- 表: `words`, `word_tags`, `quiz_questions`
- 文件: `data/dictionary.db`

### MySQL (用户行为数据)
- 存放用户生成的数据，支持高并发
- 表: `users`, `word_progress`, `quiz_results`, `essays`, `essay_scores`, `study_plans`, `learning_sessions`

## 许可证

MIT
