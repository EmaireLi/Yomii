# Yomii

Yomii 是一个面向日语学习场景的桌面化应用，覆盖查词、背单词、分级测试和 AI 作文评测四条主链路。项目采用前后端分离架构，并支持 Electron 打包为本地桌面应用。

## 功能概览

- 搜索：多字段查词，联动搜索历史和收藏
- 背单词：基于间隔重复和薄弱项强化的复习流程
- 测试：按词级与难度出题，生成能力报告
- 作文评测：本地双模型评测，DeepSeek API 作为补充候选和兜底

## 技术架构

- 前端：Vue 3 + TypeScript + Element Plus + Vite
- 桌面端：Electron
- 后端：FastAPI + SQLModel
- 数据库：
  - SQLite：词典、题库等静态数据
  - MySQL：用户、进度、收藏、作文、测试记录等行为数据
- AI：
  - 本地模型：`Qwen/Qwen3-1.7B` 双 LoRA 路线（评分 / 修订）
  - 在线兜底：DeepSeek API

## 目录结构

```text
yomii/
├── backend/                 # FastAPI 后端、训练脚本、测试
├── docs/                    # 项目文档
│   ├── 00-PROJECT/          # 项目总览
│   ├── 01-GETTING_STARTED/  # 快速开始
│   ├── 02-REFERENCE/        # API 和参考资料
│   ├── 03-DEVELOPMENT/      # 开发说明
│   └── 90-ARCHIVE/          # 历史归档
├── electron/                # Electron 主进程与预加载脚本
├── public/                  # 静态资源
├── src/                     # Vue 前端代码
├── .env.example             # 环境变量模板
├── package.json             # 前端与 Electron 脚本
└── README.md                # 仓库入口文档
```

## 环境要求

- Node.js 20+
- npm 10+
- Python 3.11+
- MySQL 8+
- 可选：支持 CUDA 的显卡环境，用于本地作文模型推理

## 快速开始

### 1. 安装依赖

前端：

```powershell
npm install
```

后端：

```powershell
cd backend
pip install -r requirements.runtime.txt
```

如果需要本地作文模型推理或训练，改为安装完整依赖：

```powershell
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```powershell
Copy-Item .env.example .env
```

至少需要确认：

```env
VITE_API_URL=http://127.0.0.1:8000/api
VITE_USE_MOCK=false
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=yomii
```

### 3. 运行模式

#### 模式 A：前后端开发联调

终端 1：

```powershell
npm run dev
```

终端 2：

```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

#### 模式 B：Electron 桌面开发

```powershell
npm run electron
```

#### 模式 C：完整作文评测链路

终端 1：前端或 Electron  
终端 2：后端  
终端 3：评分模型  
终端 4：修订模型

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

如果只演示前后端链路，可以将 `.env` 中的模型 URL 留空，后端会走 mock 结果。

## 常用命令

```powershell
# 前端开发
npm run dev

# Electron 开发
npm run electron

# 类型检查
npm run type-check

# 前端生产构建
npm run build

# Windows 打包
npm run build:win
```

## 文档入口

- [文档索引](./docs/README.md)
- [后端说明](./backend/README.md)
- [训练与模型服务说明](./backend/training/README.md)
- [项目总览](./docs/00-PROJECT/PROJECT_OVERVIEW.md)
- [API 参考](./docs/02-REFERENCE/API_REFERENCE.md)

## 说明

- `backend/requirements.runtime.txt` 用于纯后端运行
- `backend/requirements.txt` 包含本地模型推理和训练依赖，体积明显更大
- `release/`、`backend/build/`、模型目录和数据库文件都视为本地产物，不作为源码目录的一部分提交

## 许可证

MIT
