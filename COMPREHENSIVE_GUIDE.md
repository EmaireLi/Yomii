# 📚 Yomii 日语学习助手 - 综合开发指南

> 一个现代化的日语词汇学习应用，集词汇查询、背诵、测试于一体

**最后更新**: 2026年3月18日  
**项目状态**: ✅ 稳定版 (Element Plus 重构完成，所有修复已验证)

---

## 📖 目录

1. [项目概述](#项目概述)
2. [快速开始](#快速开始)
3. [项目结构](#项目结构)
4. [功能详解](#功能详解)
5. [技术栈](#技术栈)
6. [Element Plus 重构说明](#element-plus-重构说明)
7. [修复报告](#修复报告)
8. [API 参考](#api-参考)
9. [开发者指南](#开发者指南)
10. [常见问题](#常见问题)
11. [学习计划建议](#学习计划建议)

---

## 项目概述

### 核心特性

- 🔍 **智能词汇查询** - 快速搜索日语单词并获取详细释义
- 📚 **闪卡背诵** - 科学的间隔重复法帮助记忆
- 📝 **分级测试** - 三级难度的实用考试模式
- 📊 **学习统计** - 实时追踪学习进度和连续学习天数
- 💾 **本地存储** - 无需注册，数据安全保存在本地
- 🔄 **API 就绪** - 架构支持无缝接入后端服务
- ✨ **现代化 UI** - 使用 Element Plus 组件库，炫酷视觉效果和流畅动画

### 项目信息

| 项目 | 说明 |
|-----|------|
| 名称 | Yomii (阅读) |
| 类型 | Web 应用（前端） |
| 最低要求 | Node.js 18+ |
| 构建工具 | Vite 7.3.1 |
| 框架 | Vue 3.5.29 |
| 语言 | TypeScript |
| UI 库 | Element Plus |

---

## 快速开始

### 环境要求

```bash
Node.js:   20.19.0+  (建议) 或 22.12.0+
npm:       8.0.0+
```

> ⚠️ 当前项目使用 20.17.0 版本，建议升级以获得最佳兼容性

### 项目安装

```bash
# 1. 进入项目目录
cd yomii

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev

# 4. 打开浏览器访问
# http://localhost:5174
# (如果 5173 被占用，Vite 会自动选择其他端口)
```

### 常用命令

```bash
# 开发服务器（热重载）
npm run dev

# 类型检查
npm run type-check

# 生产构建
npm run build

# 本地预览构建结果
npm run preview
```

### 开发工具

```bash
# 启动 Vue DevTools（开发服务器运行时）
# 按快捷键: Alt + Shift + D

# 或在浏览器访问
# http://localhost:5174/__devtools__/
```

---

## 项目结构

### 目录树

```
yomii/
├── src/
│   ├── App.vue                                # 主应用组件（路由管理）
│   ├── main.ts                                # 应用入口（Element Plus 配置）
│   │
│   ├── components/
│   │   ├── HelloWorld.vue                     # 欢迎组件
│   │   ├── Sidebar.vue                        # 侧边栏导航
│   │   ├── TheWelcome.vue                     # 欢迎页面
│   │   ├── WelcomeItem.vue                    # 欢迎项目
│   │   ├── icons/
│   │   │   ├── IconCommunity.vue
│   │   │   ├── IconDocumentation.vue
│   │   │   ├── IconEcosystem.vue
│   │   │   ├── IconSupport.vue
│   │   │   └── IconTooling.vue
│   │   └── views/
│   │       ├── HomeView.vue                   # 首页视图（学习统计）
│   │       ├── SearchView.vue                 # 查词视图
│   │       ├── ReciteView.vue                 # 背单词视图（闪卡）
│   │       ├── TestView.vue                   # 测试视图（分级考试）
│   │       └── EssayView.vue                  # 作文评价视图（AI 就绪）
│   │
│   ├── api/
│   │   └── index.ts                           # 15+ API 端点（Mock/切换支持）
│   │
│   ├── composables/
│   │   └── useLocalStorage.ts                 # localStorage Hooks
│   │
│   ├── types/
│   │   └── index.ts                           # TypeScript 类型定义
│   │
│   ├── utils/
│   │   ├── constants.ts                       # 全局常量（团队信息等）
│   │   ├── mockData.ts                        # 模拟数据（10个词汇+3个题目）
│   │   └── ...
│   │
│   └── assets/
│       ├── base.css                           # 基础样式
│       └── main.css                           # 全局样式（Element Plus 主题）
│
├── public/                                    # 静态资源
├── dist/                                      # 构建输出（npm run build 生成）
│
├── package.json                               # NPM 依赖和脚本
├── tsconfig.json                              # TypeScript 配置
├── tsconfig.app.json                          # 应用 TS 配置
├── tsconfig.node.json                         # Node TS 配置
├── vite.config.ts                             # Vite 构建配置
├── env.d.ts                                   # 环境变量类型定义
│
├── README.md                                  # 项目说明（简版）
├── QUICK_START.md                             # 快速参考指南
├── DEVELOPER.md                               # 开发者指南
├── PROJECT_PLAN.md                            # 项目计划书
├── API_SPEC.md                                # 完整 API 规范
├── API_QUICK_REFERENCE.md                     # API 快速参考
├── UPGRADE_SUMMARY.md                         # 升级技术总结
├── IMPROVEMENTS.md                            # 改进建议
├── VERIFICATION.md                            # 验证清单
│
├── ELEMENT_PLUS_GUIDE.md                      # Element Plus 集成指南
├── ELEMENT_UI_REFACTOR.md                     # Element UI 重构文档
├── REFACTOR_SUMMARY.md                        # Element Plus 重构总结
├── VERIFICATION_CHECKLIST.md                  # 重构验证清单
├── FIXES_REPORT.md                            # 修复报告（详细）
│
└── COMPREHENSIVE_GUIDE.md                     # 本文件（综合指南）
```

---

## 功能详解

### 📖 首页 (Home View)

实时学习仪表板，展示个人成就和项目介绍：

**功能模块**:
- **学习统计卡片** (Responsive Grid)
  - 总背单词数
  - 今日学习进度
  - 连续学习天数
  - 最长连续记录

- **团队信息块**
  - 开发小组成员名单
  - 成员角色标签
  - 成员 ID 显示

- **功能导航区**
  - 查词、背单词、测试、收藏管理各功能描述
  - Emoji 图标展示

**使用的 Element Plus 组件**:
```vue
<el-card>          <!-- 卡片容器 -->
<el-row>           <!-- 响应式行 -->
<el-col>           <!-- 响应式列 -->
<el-statistic>     <!-- 统计数字展示 -->
<el-tag>           <!-- 标签 -->
```

### 🔍 查词 (Search View)

专业词汇查询工具集：

**功能模块**:
- **搜索框** (Input + Button)
  - 支持假名、汉字、中文三种输入方式
  - 实时反馈和加载状态

- **搜索历史**
  - 快速重新搜索
  - 可删除单条历史记录
  - 显示最近 5 条

- **搜索结果**
  - 词汇详情卡片
  - 释义和例句
  - 词性标签
  - 收藏按钮

- **交互功能**
  - ❤️ 收藏词汇
  - 📋 复制内容
  - 🔊 播放音频（准备中）

**使用的 Element Plus 组件**:
```vue
<el-input>         <!-- 输入框 -->
<el-button>        <!-- 按钮 -->
<el-tag>           <!-- 标签 -->
<el-card>          <!-- 卡片 -->
<el-empty>         <!-- 空状态 -->
<el-divider>       <!-- 分割线 -->
<el-notification>  <!-- 通知 -->
```

### 📚 背单词 (Recite View)

高效的闪卡学习系统：

**功能模块**:
- **学习计划管理**
  - 当前计划显示
  - 每日目标设置
  - 复习比例调整
  - 模态框编辑

- **背单词 Tab**
  - 闪卡翻转（点击或 Space）
  - 三级评价（不认识/模糊/认识）
  - 进度条实时显示
  - 快捷键提示

- **复习 Tab**
  - 类似背的工作流
  - 独立的复习单词库
  - 完成统计

- **学习统计**
  - 掌握/模糊/未掌握 统计
  - 本轮学习总结

**使用的 Element Plus 组件**:
```vue
<el-card>          <!-- 卡片 -->
<el-row>/<el-col>  <!-- 响应式布局 -->
<el-tabs>          <!-- 选项卡 -->
<el-tab-pane>      <!-- 标签页 -->
<el-button>        <!-- 按钮 -->
<el-progress>      <!-- 进度条 -->
<el-dialog>        <!-- 模态框 -->
<el-form>          <!-- 表单 -->
<el-input-number>  <!-- 数字输入 -->
<el-slider>        <!-- 滑块 -->
```

**快捷键支持**:
```
Space  → 翻转卡片
1      → 评价为"不认识"
2      → 评价为"模糊"
3      → 评价为"认识"
```

### 📝 能力测试 (Test View)

评估日语水平的分级考试系统：

**功能模块**:
- **难度选择**
  - 初级 (N5)
  - 中级 (N4-N3)
  - 高级 (N2-N1)

- **测试进行中**
  - 实时计时器
  - 得分显示
  - 进度条
  - 题目和选项展示

- **成绩报告**
  - 最终分数
  - 正确率统计
  - 个性化学习建议

**使用的 Element Plus 组件**:
```vue
<el-button>        <!-- 按钮 -->
<el-progress>      <!-- 进度条 -->
<el-radio>         <!-- 单选框 -->
<el-card>          <!-- 卡片 -->
<el-alert>         <!-- 提示框 -->
```

### ✍️ 作文评价 (Essay View)

日语作文写作和 AI 评价系统（准备中）：

**功能模块**:
- **话题选择**
  - 日常生活
  - 旅行经历
  - 爱好兴趣
  - 家庭成员
  - 未来计划
  - 自定义话题

- **作文编辑**
  - 大文本框输入
  - 字数统计
  - 实时验证

- **AI 评价** (后端支持)
  - 语法错误标记
  - 用词建议
  - 表达优化

---

## 技术栈

### 核心框架

| 类别 | 技术 | 版本 |
|------|------|------|
| **前端框架** | Vue | 3.5.29 |
| **构建工具** | Vite | 7.3.1 |
| **语言** | TypeScript | 5.4+ |
| **UI 组件库** | Element Plus | 最新 |
| **运行环境** | Node.js | 20.19+ (建议) |
| **包管理器** | npm | 8+ |

### 依赖程序包

#### 核心依赖
- `vue@^3.5.29` - Vue 框架
- `element-plus` - Element Plus UI 组件库
- `@element-plus/icons-vue` - Icon 图标库

#### 开发依赖
- `typescript@^5.4.0` - TypeScript 编译器
- `vite@^7.3.1` - 构建工具
- `vue-tsc@^2` - Vue TypeScript 编译器

### 项目配置

#### TypeScript
```json
{
  "compilerOptions": {
    "target": "ES2021",
    "jsx": "preserve",
    "module": "ESNext",
    "lib": ["ES2021", "DOM"],
    "strict": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "skipLibCheck": true
  }
}
```

#### Vite
```javascript
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})
```

---

## Element Plus 重构说明

### 重构背景

原始项目使用自定义 CSS 样式和基础 HTML 元素构建。为了提升代码质量、开发效率和用户体验，我们将所有组件重构为使用 Element Plus 组件库。

### 重构成果

✅ **已完成**:
- App.vue - 完全使用 Element Plus 容器/菜单系统
- HomeView.vue - 统计卡片、网格布局
- SearchView.vue - 输入框、按钮、标签、卡片
- ReciteView.vue - 选项卡、进度条、对话框、表单
- TestView.vue - 按钮、进度条、单选框
- EssayView.vue - 文本框、标签、表单

### 配置变化

#### main.ts 中的配置

```typescript
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const app = createApp(App)

// 全局注册 Element Plus
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
```

**关键点**:
- 导入 Element Plus 库
- 导入样式文件 (`element-plus/dist/index.css`)
- 配置中文本地化 (`zh-cn`)
- 全局注册组件（无需单个引入）

### 组件对应关系

| 场景 | 原始 HTML | Element Plus |
|------|----------|--------------|
| 页面布局 | `<div class="container">` | `<el-container>` |
| 侧边栏 | `<aside class="sidebar">` | `<el-aside>` |
| 内容区 | `<main class="content">` | `<el-main>` |
| 菜单 | `<nav class="menu">` | `<el-menu>` |
| 菜单项 | `<li class="menu-item">` | `<el-menu-item>` |
| 卡片 | `<div class="card">` | `<el-card>` |
| 按钮 | `<button>` | `<el-button>` |
| 输入框 | `<input>` | `<el-input>` |
| 标签 | `<span class="tag">` | `<el-tag>` |
| 网格行 | `<div class="row">` | `<el-row>` |
| 网格列 | `<div class="col">` | `<el-col>` |
| 统计数字 | `<div>100</div>` | `<el-statistic>` |
| 进度条 | `<div class="progress">` | `<el-progress>` |
| 选项卡 | 自定义实现 | `<el-tabs>` |

### 样式定制

#### CSS 变量 (main.css)

```css
:root {
  /* Element Plus 主题色 */
  --el-color-primary: #667eea;
  
  /* 自定义动画 */
  @keyframes slideUp {
    from { transform: translateY(20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
  }
}
```

#### 响应式断点

```vue
<el-col :xs="24" :sm="12" :md="8" :lg="6">
  <!-- xs: 超小屏 (手机) -->
  <!-- sm: 小屏 (竖屏平板) -->
  <!-- md: 中屏 (横屏平板) -->
  <!-- lg: 大屏 (桌面) -->
</el-col>
```

---

## 修复报告

### 📋 执行总结

在 Element Plus 重构过程中，发现并修复了多个 Vue 组件的语法错误。所有问题已解决，项目现已稳定运行。

### 错误修复清单

#### 1. **App.vue** ✅ 已修复
- **错误**: 第298行重复的 `</style>` 标签
- **根本原因**: 文件末尾不小心复制了关闭标签
- **修复**: 删除了多余的 `</style>` 标签
- **验证**: ✅ 路由导航正常

#### 2. **HomeView.vue** ✅ 已修复
- **错误**: 第284行"Invalid end tag"
- **根本原因**: 第一个 `</style>` 之后有额外的CSS规则，后跟第二个 `</style>` 标签
- **修复**: 删除了重复的样式规则和额外的 `</style>`
- **验证**: ✅ 统计卡片显示正常

#### 3. **SearchView.vue** ✅ 已修复
- **错误**: 第347行"Invalid end tag"
- **根本原因**: 文件中有两个独立的 `<style scoped>` 块，中间夹了多余 `</script>`
- **修复**: 
  - 删除了第347行的多余 `</script>` 标签
  - 删除了第349行的多余 `<style scoped>` 开始标签
  - 将两个样式块合并为一个
- **验证**: ✅ 搜索功能正常

#### 4. **ReciteView.vue** ✅ 已修复
- **错误**: 第146行、258行的标签匹配错误
- **根本原因**: 
  - 第37行的 `<el-tab-pane>` 没有正确关闭
  - 第149行混合使用了条件渲染 div 和 tab-pane
- **修复**:
  - 在第107行添加了 `</el-tab-pane>` 关闭第一个背单词 tab
  - 将第149行改为正确的 `<el-tab-pane label="📝 复习">` 
  - 修复了模态框结构（从 tab-pane 改为 div）
  - 确保正确的标签关闭顺序
- **验证**: ✅ 两个tab正常切换

#### 5. **TestView.vue** ✅ 无问题
- **验证**: 结构正确，语法无误

#### 6. **EssayView.vue** ✅ 无问题
- **验证**: 结构正确，语法无误

### 🛣️ 路由验证 ✅

| 项目 | 状态 | 说明 |
|------|------|------|
| 实现方式 | ✅ | 条件渲染，无需 Vue Router |
| 导航菜单 | ✅ | El-Menu 正确绑定 |
| 视图导入 | ✅ | 5个视图正确注册 |
| 导航项目 | ✅ | 首页、查词、背单词、测试、作文 |
| 链接跳转 | ✅ | switchView() 正常工作 |

### 📊 构建验证结果

```
✓ 1610 modules transformed
✓ dist/index.html (0.96 kB, gzip: 0.55 kB)
✓ dist/assets/index-CWB6Ic_S.css (382.68 kB, gzip: 52.75 kB)
✓ dist/assets/index-CQlWmdfQ.js (1,002.47 kB, gzip: 330.55 kB)
✓ Built successfully in 4.78s

⚠️ Warning: Chunks larger than 500 kB
   建议: 使用动态 import() 或 rollupOptions.output.manualChunks 优化
```

### 🚀 开发服务器验证 ✅

```
✓ VITE v7.3.1 ready in 747 ms
✓ Port: http://localhost:5174/
✓ Vue DevTools: Available
```

### 修复原则总结

1. **Vue 单文件组件结构** (SFC) 必须按顺序：`<template>` → `<script>` → `<style>`
2. **标签成对匹配** - 每个开标签都需要对应的闭标签，不能交叉
3. **避免代码重复** - 不要复制样式块或脚本块
4. **路由实现一致** - 不能混合不同的路由方式
5. **使用编辑器工具** - 启用实时语法检查和标签匹配提示

---

## API 参考

### RESTful API 端点

项目包装了 15+ 个 API 端点，支持 Mock 数据和真实后端切换。

#### 词汇相关

```typescript
// 搜索词汇
GET /api/words/search?q=勉強
// Response: Word[]

// 获取词汇详情
GET /api/words/{id}
// Response: Word

// 获取词汇列表（分页）
GET /api/words/list?page=1&pageSize=20
// Response: { data: Word[], total: number }
```

#### 学习数据

```typescript
// 获取学习统计
GET /api/study/stats
// Response: StudyStats

// 获取词汇进度
GET /api/study/progress/{wordId}
// Response: WordProgress

// 更新学习状态
POST /api/study/progress
// Body: { wordId: string, status: 'known' | 'fuzzy' | 'unknown' }
```

#### 测试相关

```typescript
// 获取测试题目
GET /api/questions/random?difficulty=medium&count=10
// Response: Question[]

// 提交测试答案
POST /api/questions/submit
// Body: { questionId: string, answer: string }

// 获取成绩报告
GET /api/results/{resultId}
// Response: TestResult
```

#### 收藏和历史

```typescript
// 获取收藏词汇
GET /api/favorites
// Response: Word[]

// 添加收藏
POST /api/favorites/{wordId}

// 删除收藏
DELETE /api/favorites/{wordId}

// 获取搜索历史
GET /api/history
// Response: string[]
```

### 数据类型定义

#### Word（词汇）

```typescript
interface Word {
  id: string                  // 词汇 ID
  word: string               // 日文词汇（如: "勉強"）
  kana: string               // 假名读音（如: "べんきょう"）
  meaning: string            // 中文释义
  example?: string           // 例句
  partOfSpeech?: string      // 词性（noun, verb, adj...）
  audioUrl?: string          // 音频链接
  tags?: string[]            // 标签（如: ["初级", "日常"]）
  frequency?: number         // 使用频率（0-100）
}
```

#### WordProgress（学习进度）

```typescript
interface WordProgress {
  wordId: string
  status: 'unknown' | 'fuzzy' | 'known'
  lastReviewedAt: number     // 最后复习时间（时间戳）
  reviewCount: number        // 复习次数
  correctCount: number       // 正确次数
}
```

#### StudyStats（学习统计）

```typescript
interface StudyStats {
  totalWordsLearned: number      // 总学习词数
  totalWordsRecited: number      // 总背词数
  todayLearned: number           // 今日新学词数
  todayRecited: number           // 今日背词数
  currentStreak: number          // 连续学习天数
  longestStreak: number          // 最长连续天数
  lastStudyDate: number          // 最后学习日期
}
```

#### Question（测试题目）

```typescript
interface Question {
  id: string
  question: string           // 题目内容
  type: 'choice' | 'fill'   // 题目类型
  options?: string[]         // 选项（多选题时）
  answer: string             // 正确答案
  explanation?: string       // 答案解析
  difficulty: 'easy' | 'medium' | 'hard'
}
```

### Mock vs 真实数据切换

#### 启用 Mock 数据

```typescript
// src/api/index.ts
const USE_MOCK_DATA = true  // 启用模拟数据

if (USE_MOCK_DATA) {
  // 使用本地 mockData.ts 中的测试数据
} else {
  // 连接真实后端服务
}
```

#### 后端集成步骤

1. 将 `USE_MOCK_DATA` 改为 `false`
2. 修改 API 基础 URL：
```typescript
const API_BASE_URL = 'http://your-backend.com/api'
```
3. 后端应实现相同的端点和数据格式

---

## 开发者指南

### 文件编辑规范

#### Vue 单文件组件 (.vue)

**标准结构**:
```vue
<template>
  <!-- HTML 模板，只能有一个根元素 -->
  <section class="component">
    <!-- 内容 -->
  </section>
</template>

<script setup lang="ts">
  // TypeScript 逻辑
  // 使用 setup lang="ts" 写法（推荐）
  import { ref, computed } from 'vue'
  
  const count = ref(0)
  const doubled = computed(() => count.value * 2)
</script>

<style scoped>
  /* 仅作用于本组件的样式 */
  .component {
    display: flex;
    gap: 10px;
  }
</style>
```

**关键原则**:
1. `<template>` 必须位于最前
2. `<script>` 段只能有一个
3. `<style scoped>` 只能有一个
4. 不能混合不同的脚本类型

#### TypeScript 类型定义

```typescript
// src/types/index.ts 中定义所有类型

// 导出接口
export interface Word {
  id: string
  word: string
  kana: string
  meaning: string
}

// 导出枚举
export enum StudyStatus {
  Unknown = 'unknown',
  Fuzzy = 'fuzzy',
  Known = 'known'
}

// 导出类型别名
export type WordList = Word[]
```

### 添加新组件

#### 创建新视图组件

```typescript
// src/components/views/NewView.vue

<template>
  <section class="new-view">
    <el-card>
      <h1>新功能</h1>
      <el-button type="primary" @click="doSomething">操作</el-button>
    </el-card>
  </section>
</template>

<script setup lang="ts">
  import { ref } from 'vue'
  
  const count = ref(0)
  
  const doSomething = () => {
    count.value++
  }
</script>

<style scoped>
  .new-view {
    padding: 20px;
  }
</style>
```

#### 注册新视图到 App.vue

```vue
<template>
  <el-container>
    <!-- ... 菜单项 ... -->
    <el-menu-item index="newview">🆕 新功能</el-menu-item>
  </el-container>
  
  <el-main>
    <!-- ... 其他视图 ... -->
    <NewView v-else-if="currentView === 'newview'" />
  </el-main>
</template>

<script setup lang="ts">
  import NewView from '@/components/views/NewView.vue'
  
  const switchView = (viewName: string) => {
    currentView.value = viewName
  }
</script>
```

### 使用 Composable Hooks

#### 访问本地存储

```typescript
import { useSearchHistory, useFavorites, useStudyStats } from '@/composables/useLocalStorage'

// 搜索历史
const { searchHistory, addSearch, removeSearch } = useSearchHistory()

// 收藏夹
const { favorites, toggleFavorite } = useFavorites()

// 学习统计
const { stats, updateProgress } = useStudyStats()
```

#### 创建自定义 Hook

```typescript
// src/composables/useCustom.ts

import { ref, computed } from 'vue'

export function useCustom() {
  const data = ref<string[]>([])
  
  const isEmpty = computed(() => data.value.length === 0)
  
  const addItem = (item: string) => {
    data.value.push(item)
  }
  
  return {
    data,
    isEmpty,
    addItem
  }
}

// 在组件中使用
import { useCustom } from '@/composables/useCustom'

const { data, isEmpty, addItem } = useCustom()
```

### API 集成

#### 调用 API 端点

```typescript
import { getWordList, searchWords, updateProgress } from '@/api'

// 搜索词汇
const words = await searchWords('勉強')
console.log(words)  // Word[]

// 获取词汇列表
const { data, total } = await getWordList(1, 20)

// 更新学习进度
await updateProgress({
  wordId: 'word-123',
  status: 'known'
})
```

#### 错误处理

```typescript
import { ElNotification } from 'element-plus'

try {
  const words = await searchWords('勉強')
} catch (error) {
  ElNotification({
    title: '错误',
    message: '搜索失败，请重试',
    type: 'error'
  })
}
```

### 性能优化

#### 代码分割

```typescript
// 使用动态导入实现路由级别的代码分割
import { defineAsyncComponent } from 'vue'

const SearchView = defineAsyncComponent(() => 
  import('@/components/views/SearchView.vue')
)
```

#### 响应式优化

```typescript
// ✅ 好的做法
const data = ref([])
const filteredData = computed(() => {
  return data.value.filter(item => item.active)
})

// ❌ 避免的做法
const filteredData = ref([])
watch(data, () => {
  filteredData.value = data.value.filter(...)  // 过度订阅
})
```

---

## 常见问题

### Q: 如何修改页面样式？

A: 有三种方法：

1. **全局样式** (`src/assets/main.css`)
   ```css
   :root {
     --el-color-primary: #your-color;
   }
   ```

2. **组件样式** (组件内的 `<style scoped>`)
   ```vue
   <style scoped>
   .my-component {
     color: red;
   }
   </style>
   ```

3. **Element Plus 主题**
   - 修改 CSS 变量
   - 参考: https://element-plus.org/en-US/guide/theming.html

### Q: 如何添加新功能？

A: 基本步骤：

1. 创建新的 Vue 组件文件 (`src/components/views/Feature.vue`)
2. 在 App.vue 中导入组件
3. 添加菜单项到侧边栏
4. 在条件渲染中添加视图显示逻辑
5. 如需新 API，在 `src/api/index.ts` 中添加

### Q: 如何连接真实后端？

A: 修改 `src/api/index.ts`：

```typescript
// 改为
const USE_MOCK_DATA = false

// 设置后端 URL
const API_BASE_URL = 'http://your-api.com/api'

// 所有 fetch 请求会自动使用真实端点
```

### Q: 数据会丢失吗？

A: 不会。所有数据存储在浏览器 localStorage：

- **清除方法**: 在浏览器开发者工具 → Application → Local Storage → 删除
- **导出数据**: 使用浏览器开发者工具导出 JSON
- **无消间隔存储**: 关闭浏览器后数据仍保留

### Q: 如何升级依赖包？

A: 

```bash
# 更新所有包到最新版本
npm update

# 更新特定包
npm update element-plus

# 升级到新大版本（如 Vue 4.0）
npm install vue@latest
```

### Q: 支持离线使用吗？

A: 当前不支持（不是 PWA 应用）。若需支持，可：

1. 使用 Service Worker
2. 添加 PWA 支持（workbox）
3. 缓存所有资源文件

---

## 学习计划建议

### 初学者路线

**第 1 周 - 基础积累**
```
每日 30 个新词汇
└─ 使用"背单词"模块
└─ 配合"查词"了解详细用法
└─ 目标: 210 个词汇
```

**第 2-4 周 - 巩固提升**
```
每日 30 个复习 + 15 个测试
└─ 在"复习"标签页复习昨天的词汇
└─ 定期参加"能力测试"
└─ 跟踪"首页"统计数据
└─ 目标: 准确率 > 80%
```

### 进阶学习者路线

**提高学习量**
```
每日 50+ 词汇
└─ 优先学习高频词
└─ 参加"高级"难度测试
└─ 使用"收藏"管理重点词汇
```

**强化应用**
```
定期参加分级考试
└─ 初级 (N5) → 中级 (N4-N3) → 高级 (N2-N1)
└─ 追踪成绩进度
└─ 针对弱项加强复习
```

### 连续学习激励

```
学习日程表建议:
- 工作日: 每天 30-60 分钟
- 周末: 每天 90-120 分钟
- 目标: 保持连续学习，追踪"连续天数"
- 奖励: 达到 30 天/60 天/100 天 里程碑
```

### 利用数据追踪

```
关注首页统计:
✓ 总背词数: 目标 1000+
✓ 连续天数: 目标 30+ 天（一个月）
✓ 掌握率: 目标 > 85%
✓ 复习率: 目标 100%（不落下）
```

---

## 快捷键列表

### 全局快捷键

| 快捷键 | 功能 | 模块 |
|--------|------|------|
| `Enter` | 提交搜索 | 查词 |
| `Alt + Shift + D` | 打开 Vue DevTools | 全局 |

### 背单词模块快捷键

| 快捷键 | 功能 |
|--------|------|
| `Space` | 翻转卡片显示/隐藏释义 |
| `1` | 评价为"不认识" |
| `2` | 评价为"模糊" |
| `3` | 评价为"认识" |

### 浏览器开发者工具

| 快捷键 | 功能 |
|--------|------|
| `F12` | 打开开发者工具 |
| `Ctrl + Shift + I` | 打开开发者工具（Windows） |
| `Cmd + Option + I` | 打开开发者工具（Mac） |

---

## 故障排除

### 端口被占用

**问题**: `Port 5173 is in use`

**解决方案**:
```bash
# 方案 1: Vite 会自动使用下一个可用端口
npm run dev
# 查看输出的实际端口

# 方案 2: 指定端口
npm run dev -- --port 3000
```

### 依赖冲突

**问题**: `npm ERR! peer dep missing`

**解决方案**:
```bash
# 清除和重新安装
rm -rf node_modules package-lock.json
npm install

# 或强制安装
npm install --force
```

### TypeScript 错误

**问题**: Type errors in IDE

**解决方案**:
```bash
# 运行类型检查
npm run type-check

# 查看详细错误
npm run type-check -- --listFiles
```

### 样式不生效

**问题**: Element Plus 样式没有应用

**解决方案**:
1. 检查 `main.ts` 是否导入了 Element Plus 样式
2. 检查 `package.json` 是否有 `element-plus`
3. 重启开发服务器

### 构建体积过大

**问题**: Build output > 500 kB

**解决方案**:
```typescript
// vite.config.ts 中启用代码分割
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        vue: ['vue'],
        'element-plus': ['element-plus']
      }
    }
  }
}
```

---

## 贡献和支持

### 报告问题

遇到问题请：
1. 查看本文档的"常见问题"部分
2. 运行 `npm run type-check` 检查错误
3. 查看浏览器控制台错误信息
4. 在问题跟踪中提交详细描述

### 代码提交规范

```bash
# 提交前检查
npm run type-check
npm run build

# 提交信息格式
git commit -m "feat: 添加新功能"
git commit -m "fix: 修复 bug"
git commit -m "docs: 更新文档"
```

---

## 许可证和致谢

### 技术栈致谢

- Vue.js 团队 - 前端框架
- Element Plus 团队 - UI 组件库
- Vite 团队 - 构建工具
- TypeScript 团队 - 类型系统

### 项目信息

- **项目名称**: Yomii (阅读)
- **当前版本**: 1.0.0 (Element Plus 版本)
- **最后更新**: 2026年3月18日
- **开发人员**: Yomii 开发小组

---

## 快速导航

**相关文档** (详细信息):
- [README.md](./README.md) - 项目简介
- [QUICK_START.md](./QUICK_START.md) - 快速参考
- [DEVELOPER.md](./DEVELOPER.md) - 完整开发指南
- [API_SPEC.md](./API_SPEC.md) - 完整 API 规范
- [PROJECT_PLAN.md](./PROJECT_PLAN.md) - 项目计划
- [FIXES_REPORT.md](./FIXES_REPORT.md) - 详细修复报告

**快速链接**:
- 🚀 [启动开发服务器](#快速开始)
- 📖 [功能详解](#功能详解)
- 💻 [API 参考](#api-参考)
- 👨‍💻 [开发指南](#开发者指南)
- ❓ [常见问题](#常见问题)

---

**文档版本**: 1.0  
**同步时间**: 2026年3月18日  
**状态**: ✅ 完整、验证、准生产

需要帮助？查看上方导航或访问相关文档文件。
