# 📚 Yomii - 日语学习助手

> 一个现代化的日语词汇学习应用，集词汇查询、背诵、测试于一体

## ✨ 核心特性

- 🔍 **智能词汇查询** - 快速搜索日语单词并获取详细释义
- 📚 **闪卡背诵** - 科学的间隔重复法帮助记忆
- 📝 **分级测试** - 三级难度的实用考试模式
- 📊 **学习统计** - 实时追踪学习进度和连续学习天数
- 💾 **本地存储** - 无需注册，数据安全保存在本地
- 🔄 **API 就绪** - 架构支持无缝接入后端服务
- ✨ **现代化 UI** - 炫酷视觉效果和流畅动画

## 🚀 快速开始

### 环境要求
- Node.js 18+
- npm 8+

### 安装和运行

```bash
# 1. 进入项目目录
cd yomii

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev

# 4. 打开浏览器访问
# http://localhost:5174
```

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

| 文档 | 说明 |
|------|------|
| **[API_QUICK_REFERENCE.md](./API_QUICK_REFERENCE.md)** | 👨‍💻 API 使用快速参考（开发者必读） |
| **[API_SPEC.md](./API_SPEC.md)** | 🔧 完整 API 规范（后端实现参考） |
| **[UPGRADE_SUMMARY.md](./UPGRADE_SUMMARY.md)** | 📋 项目升级技术总结 |

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
- 🎓 三个难度等级（简单/中级/困难）
- 📋 10 题快速测试
- ✔️ 即时反馈和详解
- 🏆 得分统计

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
| | 列表 | `GET /words?page=1&limit=20` |
| | 随机 | `GET /words/random?count=10` |
| **测试** | 获取题目 | `GET /quiz/questions?difficulty=medium&count=10` |
| | 提交答案 | `POST /quiz/answer` |
| **进度** | 更新单词进度 | `POST /progress/word/:id` |
| | 获取统计 | `GET /progress/stats` |
| | 获取历史 | `GET /progress/history?limit=20` |
| **收藏** | 添加收藏 | `POST /favorites` |
| | 移除收藏 | `DELETE /favorites/:id` |
| | 获取列表 | `GET /favorites` |

👉 详见 [API_SPEC.md](./API_SPEC.md) 了解完整规范

## 💾 智能数据持久化

应用自动保存用户数据到浏览器 localStorage，无需配置：

| 数据类型 | 说明 | 自动保存 |
|---------|------|---------|
| 🔍 **搜索历史** | 最近 20 条搜索记录 | ✅ 自动 |
| ⭐ **收藏列表** | 用户收藏的单词 | ✅ 自动 |
| 📊 **学习统计** | 背词数、连续天数、最长记录 | ✅ 自动 |
| 📈 **单词进度** | 每个单词的学习状态 | ✅ 自动 |

**完全离线可用，数据安全私密！**

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
