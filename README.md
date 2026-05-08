# 📚 Yomii - 日语学习助手

> 一个现代化的日语词汇学习应用，集词汇查询、背诵、测试于一体

## ✨ 核心特性

- 🔍 **智能词汇查询** - 快速搜索日语单词并获取详细释义
- 📚 **闪卡背诵** - 科学的间隔重复法帮助记忆
- 📝 **分级测试** - 三级难度的实用考试模式
- 📊 **学习统计** - 实时追踪学习进度和连续学习天数
- 💾 **本地缓存 + 账号体系** - 支持登录后跨设备使用，关键数据持久化到后端
- 🔄 **API 就绪** - 架构支持无缝接入后端服务
- ✨ **现代化 UI** - 炫酷视觉效果和流畅动画

## 🚀 快速开始

### 环境要求
- Node.js 18+
- npm 8+
- Python 3.11+
- MySQL 8+

### 安装和运行（前后端 + 本地模型）

```bash
# 终端 1：前端
cd yomii
npm install
npm run dev
```

再开 3 个终端：

```powershell
# 终端 2：启动后端
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
# 终端 3：启动评分模型服务
cd .
backend\.venv-training\Scripts\python.exe `
  backend\training\serve_qwen_adapter.py `
  --task score `
  --adapter backend\models\score-lora `
  --port 8011
```

```powershell
# 终端 4：启动修改模型服务
cd .
backend\.venv-training\Scripts\python.exe `
  backend\training\serve_qwen_adapter.py `
  --task revision `
  --adapter backend\models\revision-lora `
  --port 8012
```

如果你只想跑前后端联调，不启动本地模型，可以把 `backend/.env` 里的两个模型 URL 留空，然后只执行前端和后端这两个终端命令。

访问地址：
- 前端：`http://localhost:5173`
- 后端 Swagger：`http://127.0.0.1:8000/api/docs`
- 评分模型：`http://127.0.0.1:8011/infer`
- 修改模型：`http://127.0.0.1:8012/infer`

### 后端环境变量

后端默认从 `backend/.env` 读取配置，至少需要配置 MySQL。

作文双模型原型的关键配置：

```env
ESSAY_SCORE_MODEL_URL=http://127.0.0.1:8011/infer
ESSAY_SCORE_MODEL_NAME=qwen3-1.7b-score-lora
ESSAY_REVISION_MODEL_URL=http://127.0.0.1:8012/infer
ESSAY_REVISION_MODEL_NAME=qwen3-1.7b-revision-lora
ESSAY_MODEL_TIMEOUT_SECONDS=45
```

说明：
- 两个 `URL` 都留空：后端使用内置 mock 评分/改写结果，适合只做页面联调。
- 配置为上面的本地地址：表示“后端要去这两个地址调用模型”。
- 这只是接口地址配置，不会自动帮你启动模型进程。
- 所以 `.env` 配好一次之后，后面仍然需要分别启动：
  - 后端 `uvicorn`
  - `score` 模型服务
  - `revision` 模型服务

### 常用启动命令速查

完整模式：

```powershell
# 终端 1：前端
cd yomii
npm install
npm run dev
```

```powershell
# 终端 2：后端
cd yomii\backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
# 终端 3：评分模型
cd yomii
backend\.venv-training\Scripts\python.exe backend\training\serve_qwen_adapter.py --task score --adapter backend\models\score-lora --port 8011
```

```powershell
# 终端 4：修改模型
cd yomii
backend\.venv-training\Scripts\python.exe backend\training\serve_qwen_adapter.py --task revision --adapter backend\models\revision-lora --port 8012
```

仅联调模式：

```powershell
# 终端 1：前端
cd yomii
npm install
npm run dev
```

```powershell
# 终端 2：后端（确保 backend/.env 中模型 URL 为空）
cd yomii\backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 作文双模型原型运行方式

当前作文模块已支持异步双模型链路：

1. 提交作文
2. 后端创建评测任务
3. 评分模型输出 JLPT 风格结构化评分
4. 修改模型输出问题列表、逐句建议和修正版
5. 前端历史记录页查看状态和完整报告

如果你还没有本地模型服务，可以先只启动前后端，作文模块会走 mock 结果，链路仍然完整。

### 8GB 显存本地训练方案

如果你要在本机 `8GB` 显存下训练作文模型，当前仓库默认路线是：

- base model: `Qwen/Qwen3-1.7B`
- `4-bit QLoRA`
- 双 adapter：
  - `score-lora`
  - `revision-lora`

训练目录：

- [backend/training/README.md](./backend/training/README.md)

这套方案是研究原型，不是商用许可方案。

### 构建生产版本

```bash
npm run build
npm run preview
```

### 代码质量检查

```bash
npm run type-check
```

## 📖 文档导航

> 📌 **推荐首先阅读**: [COMPREHENSIVE_GUIDE.md](./COMPREHENSIVE_GUIDE.md) - 综合开发指南（包含所有功能、修复和开发文档）

| 文档 | 说明 |
|------|------|
| **[COMPREHENSIVE_GUIDE.md](./COMPREHENSIVE_GUIDE.md)** | 📚 **综合指南**（包含全部内容，推荐阅读）|
| **[快速开始](./docs/01-GETTING_STARTED/QUICK_START.md)** | 🚀 项目启动与常见操作 |
| **[开发指南](./docs/03-DEVELOPMENT/DEVELOPER_GUIDE.md)** | 👨‍💻 开发规范与工程实践 |
| **[API 参考](./docs/02-REFERENCE/API_REFERENCE.md)** | 🔌 前后端 API 调用说明 |
| **[数据库设计](./docs/DATABASE_DESIGN.md)** | 🗄️ 双数据库模型与表结构说明 |
| **[重构验收](./docs/04-REFACTORING/FIXES_VERIFICATION.md)** | ✅ Element Plus 重构修复验证 |
| **[PROJECT_PLAN.md](./PROJECT_PLAN.md)** | 📋 项目计划和需求 |
| **[功能清单](./docs/PROJECT_PLAN_REQUIRED_FEATURES.md)** | 🎯 按计划书整理的实现范围 |

## 🏗️ 项目结构

```
yomii/
├── src/
│   ├── components/
│   │   ├── views/                 # 页面视图
│   │   │   ├── HomeView.vue       # 首页（学习统计）
│   │   │   ├── SearchView.vue     # 查词页面
│   │   │   ├── ReciteView.vue     # 背单词页面
│   │   │   └── TestView.vue       # 测试页面
│   │   └── icons/                 # 图标组件
│   ├── api/
│   │   └── index.ts               # 15+ API 端点，Mock/真实切换
│   ├── composables/
│   │   └── useLocalStorage.ts     # localStorage Hooks
│   ├── utils/
│   │   ├── mockData.ts            # 测试数据（10 个单词 + 3 个题目）
│   │   └── constants.ts           # 常量定义
│   ├── types/
│   │   └── index.ts               # TypeScript 类型定义
│   ├── App.vue                    # 应用根组件（左侧导航 + 右侧内容）
│   ├── main.ts                    # 应用入口
│   └── assets/                    # 静态资源
├── public/                        # 公开资源
├── package.json                   # 依赖管理
├── tsconfig.json                  # TypeScript 配置
├── vite.config.ts                 # Vite 构建配置
└── README.md                      # 本文件
```

## 🎯 功能详解

### 📖 首页 (Home)
实时学习仪表板，展示个人成就：
- 总背单词数
- 今日学习进度
- 连续学习天数
- 最长连续记录

### 🔍 查词 (Search)
专业词汇查询工具：
- ⚡ 实时搜索
- 📖 完整释义和例句
- ⭐ 一键收藏
- 🕐 搜索历史记录

### 📚 背单词 (Recite)
闪卡间隔重复学习法：
- 🎴 随机闪卡展示
- ⌨️ 键盘快捷操作（← → 翻转，↑ ↓ 标记）
- 📊 学习进度跟踪
- 🎯 三种标记状态（不认识/模糊/已掌握）

### 📝 测试评估 (Test)
分级考试系统：
- 🎓 多个难度等级（基础到 N1 低频挑战）
- 📋 10 题快速测试
- ✔️ 即时反馈和详解
- 🏆 得分统计

### ✍️ 作文评价 (Essay)
双模型作文评测系统：
- 🧭 **JLPT 风格评分** - 任务完成度、语法、词汇、连贯性、自然度、等级匹配度
- 🛠️ **作文修改建议** - 重点问题、逐句建议、完整修正版
- 🕓 **异步评测状态** - 待评测 / 评分中 / 修改中 / 已完成 / 失败
- 🧾 **历史报告** - 支持回看每篇作文的评分与修正版

## ⚡ API 系统

### 一键切换 Mock ↔ 真实 API

**开发模式（推荐）：** 使用 Mock 数据
```js
VITE_USE_MOCK=true
```
✅ 无需后端服务，完整测试所有功能

**生产模式：** 连接真实后端
```js
VITE_USE_MOCK=false
VITE_API_URL=http://api.example.com/api
```
🚀 后端准备就绪无缝切换，一行配置搞定！

### API 端点列表

| 类别 | 功能 | 端点 |
|------|------|------|
| **词汇** | 搜索 | `GET /words/search?q=keyword` |
| | 详情 | `GET /words/:id` |
| | 列表 | `GET /words/?skip=0&limit=20` |
| | 随机 | `GET /words/random?count=10` |
| **测试** | 获取题目 | `GET /quiz/questions?difficulty=medium&count=10` |
| | 提交答案 | `POST /quiz/submit` |
| **作文** | 提交作文 | `POST /essays/submit` |
| | 触发评测 | `POST /essays/:id/evaluate` |
| | 获取报告 | `GET /essays/:id/report` |
| | 获取历史 | `GET /essays/history` |
| **用户** | 更新单词进度 | `POST /user/progress/:wordId` |
| | 获取统计 | `GET /user/stats` |
| | 搜索历史 | `GET /user/search-history` |
| | 添加收藏 | `POST /user/favorites/:wordId` |
| | 移除收藏 | `DELETE /user/favorites/:wordId` |
| | 获取收藏 | `GET /user/favorites` |
| **认证** | 注册/登录 | `POST /auth/register`, `POST /auth/login` |

👉 详见 [API 参考文档](./docs/02-REFERENCE/API_REFERENCE.md) 与后端 Swagger(`/api/docs`)

## 💾 智能数据持久化

应用同时使用浏览器 localStorage 与后端数据库进行持久化：

| 数据类型 | 说明 | 自动保存 |
|---------|------|---------|
| 🔐 **登录态** | Token 与基础用户信息（前端缓存） | ✅ 自动 |
| 🔍 **搜索历史** | 已登录用户搜索记录（后端 MySQL） | ✅ 自动 |
| ⭐ **收藏列表** | 用户收藏的单词（后端 MySQL） | ✅ 自动 |
| 📈 **单词进度** | 每个单词学习状态（后端 MySQL） | ✅ 自动 |

**离线时可使用 Mock 数据，在线时可与后端账号数据同步。**

## 🎨 设计亮点

- 🎭 **深紫色品牌色** - 专业现代的视觉风格
- ✨ **流畅动画** - 自然的过渡和交互反馈
- 🌊 **渐变背景** - 多层次的视觉深度
- 📐 **响应式布局** - 完美适配各种屏幕
- 💎 **高光效果** - 悬停、聚焦、发光等特效

## 🛠️ 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| **框架** | Vue 3 | 3.3+ |
| **语言** | TypeScript | 5.9.3 |
| **构建** | Vite | 7.3.1 |
| **样式** | Scoped CSS + 动画 | - |
| **HTTP** | Fetch API | 原生 |
| **存储** | localStorage | 原生 |

## 🚦 常用命令

```bash
# 开发服务器（热重载）
npm run dev

# 类型检查（零错误）
npm run type-check

# 生产构建
npm run build

# 预览生产版本
npm run preview
```

## 📊 学习建议

### 🌱 初学者行动计划
1. **首页** - 了解自己的学习进度
2. **查词** - 探索感兴趣的词汇
3. **背单词** - 每天坚持 10-15 分钟背诵
4. **收藏** - 积累难点词汇

### 📈 中级学习者行动计划
1. 每日 **背单词** 保持连续学习记录
2. 定期进行 **简单/中级** 测试
3. 复习错题，加强薄弱环节
4. 扩充个人词库

### 🏆 高级学习者行动计划
1. 挑战 **困难** 模式
2. 追求更长的连续学习天数
3. 建立专业领域词汇库
4. 为日语考试强化训练

## 📱 桌面应用打包（可选）

本应用架构已完全支持 Electron 打包成桌面应用：

```bash
# 安装 electron 工具
npm install -D electron electron-builder

# 构建桌面应用
npm run electron:build
```

生成的应用可在 Windows、macOS、Linux 上运行。

## 🐛 常见问题排除

### ❓ 应用无法加载
```bash
# 清空浏览器缓存
localStorage.clear()
# 重启开发服务器
npm run dev
```

### ❓ 找不到模块
```bash
# 重新安装依赖
npm install
npm run dev
```

### ❓ API 请求失败

检查清单：
- [ ] `.env.local` 配置是否正确
- [ ] `VITE_USE_MOCK=true`（开发时）
- [ ] 后端服务是否运行（生产时）
- [ ] MySQL 是否可连接
- [ ] 作文双模型服务地址是否配置正确（如有）
- [ ] 查看浏览器控制台的错误信息

## 📚 开发工具推荐

- **编辑器** - [VS Code](https://code.visualstudio.com/)
- **Vue 扩展** - [Vue - Official](https://marketplace.visualstudio.com/items?itemName=Vue.volar)
- **调试工具** - [Vue DevTools](https://chrome.google.com/webstore)
- **浏览器** - Chrome / Edge（支持 Vue DevTools）

## 📄 许可证

MIT - 可自由使用和修改

## 🌟 项目版本

**当前版本：2.0** | **发布日期：2026-03-14**

### 版本历史
- **v2.0** - 桌面版本 + API 集成（当前）
- **v1.0** - 初始版本（本地 Mock 数据）

---

**准备好开始学习日语了吗？** 🇯🇵✨
