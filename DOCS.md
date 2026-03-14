# 📚 Yomii 文档中心

> 完整的项目文档导航和开发指南

## 📖 文档速览

### 🎯 按用途分类

#### 👨‍💻 **我是开发者，想要快速上手**
```
阅读顺序：
1. README.md（这里）- 5 分钟速览项目概况
2. API_QUICK_REFERENCE.md - 15 分钟学习 API 使用
3. 阅读源代码 - 20 分钟理解实现细节
```

#### 🔧 **我在实现后端，需要 API 规范**
```
直接查看：
→ API_SPEC.md（完整规范，可直接参考实现）
```

#### 📋 **我想了解项目架构和升级过程**
```
查看：
→ UPGRADE_SUMMARY.md（技术总结和架构设计）
```

#### ⚙️ **我需要配置环境和部署**
```
查看：
1. .env.local.example - 环境配置
2. README.md - 快速开始部分
```

---

## 📁 文档文件列表

### 核心文档

| 文件名 | 大小 | 阅读时间 | 用途 |
|--------|------|---------|------|
| **README.md** | 📄 | ~5 分钟 | **项目简介和快速开始** |
| **API_QUICK_REFERENCE.md** | 📋 | ~15 分钟 | **API 使用实操指南** |
| **API_SPEC.md** | 📚 | ~30 分钟 | **完整 API 规范** |
| **UPGRADE_SUMMARY.md** | 📖 | ~20 分钟 | **技术架构总结** |
| **.env.local.example** | ⚙️ | ~2 分钟 | **环境配置模板** |
| **DOCS.md** | 🗂️ | 当前文件 | **文档导航中心** |

---

## 🗺️ 详细导航地图

### README.md
**适合人群：** 所有人

**内容概览：**
- ✨ 核心特性（6 个）
- 🚀 快速开始（3 步启动）
- 📖 文档导航
- 🏗️ 项目结构
- 🎯 四个核心功能详解
- ⚡ API 系统说明
- 💾 数据持久化
- 🎨 设计亮点
- 🛠️ 技术栈

**快速跳转：**
```bash
# 立即启动应用
npm install && npm run dev
# 访问 http://localhost:5174
```

---

### API_QUICK_REFERENCE.md
**适合人群：** 前端开发者

**核心内容：**

#### 📌 第一部分：环境配置
```javascript
// Mock 模式（开发）
VITE_USE_MOCK=true

// 真实模式（生产）
VITE_USE_MOCK=false
VITE_API_URL=http://api.example.com
```

#### 📌 第二部分：API 导入
```typescript
import {
  searchWords,        // 搜索
  getWord,           // 详情
  getRandomWordsAPI, // 随机
  // ... 还有 12 个
} from '@/api'
```

#### 📌 第三部分：常见用法
每个 API 都附带完整示例代码：
- 基础调用
- 错误处理
- 在 Vue 组件中使用
- 性能优化建议

#### 📌 第四部分：类型定义
所有 TypeScript 接口速查：
- Word
- SearchResult
- WordProgress
- StudyStats
- QuizQuestion

#### 📌 第五部分：调试技巧
- 查看 API 请求
- 检查数据结构
- 验证 API 模式

---

### API_SPEC.md
**适合人群：** 后端开发者、系统架构师

**完整规范内容：**

#### 第一章：概述
- API 架构设计
- Mock vs 真实 API
- 环境配置方式

#### 第二章：数据模型（TypeScript）
可直接复制的类型定义：
```typescript
interface Word {
  id: string
  word: string
  kana: string
  meaning: string
  // ... 7 个字段
}

interface StudyStats {
  totalWordsLearned: number
  totalWordsRecited: number
  todayLearned: number
  // ... 5 个字段
}

// 还有 6 个核心数据模型
```

#### 第三章：15+ API 端点详解
每个端点包含：
- **请求方法** - GET / POST / DELETE
- **URL 路径** - `/words/search`
- **参数说明** - 类型、必填、示例
- **返回数据** - JSON 结构
- **错误处理** - 错误码和描述

**端点分组：**
- 词汇管理（4 个）
- 随机获取（1 个）
- 测试系统（2 个）
- 进度追踪（3 个）
- 搜索历史（1 个）
- 收藏管理（3 个）
- 用户进度（1 个）

#### 第四章：实现指南
- 数据库设计建议
- 接口实现步骤
- 错误处理规范
- 数据验证规范
- 性能优化建议

#### 第五章：测试用例
每个端点的完整测试数据和期望输出

---

### UPGRADE_SUMMARY.md
**适合人群：** 项目管理、架构研究、学习者

**文档内容：**

#### 📊 项目演变历程
```
版本 1.0（初始）
  ↓
版本 1.5（移动优化 - 需要改回）
  ↓
版本 2.0（桌面 + API）← 当前
```

#### 🎯 核心改进点
1. **UI 架构** - 从底部 TabBar → 左侧 Sidebar
2. **API 层** - 从硬编码数据 → 双模式 API
3. **视觉设计** - 移动风格 → 专业桌面风格
4. **代码质量** - TypeScript 类型安全达 100%

#### 📈 详细变更日志
- App.vue - 3 个主要改变
- SearchView.vue - API 集成
- ReciteView.vue - 异步加载
- TestView.vue - 难度选择
- 新增 src/api/index.ts - 250+ 行
- 新增文档 - 4 个文件

#### 🚀 技术亮点
- 环境驱动 API 切换
- 零依赖 Mock 层
- 动画和特效系统
- localStorage 持久化
- 完整的 TypeScript 支持

---

## 🚀 快速导航

### 场景 1: "我想现在就开始使用"
```bash
# 只需 3 个命令
npm install          # 安装依赖
npm run dev          # 启动服务
# 打开浏览器 http://localhost:5174
```

### 场景 2: "我想理解一个特定的 API"
1. 打开 [API_QUICK_REFERENCE.md](./API_QUICK_REFERENCE.md)
2. Ctrl+F 搜索函数名
3. 查看示例代码
4. 复制粘贴使用

### 场景 3: "我需要实现后端 API"
1. 阅读 [API_SPEC.md](./API_SPEC.md) 第二、三章
2. 复制数据模型定义
3. 按照规范实现端点
4. 在 `.env` 中设置 `VITE_USE_MOCK=false`

### 场景 4: "我想修改 UI 或添加新功能"
1. 查看 [UPGRADE_SUMMARY.md](./UPGRADE_SUMMARY.md) 了解架构
2. 阅读 [README.md](./README.md) 中的项目结构
3. 查看相关源代码
4. 运行 `npm run type-check` 验证更改

### 场景 5: "我想部署这个应用"
1. 阅读 [README.md](./README.md) 部分和构建部分
2. 运行 `npm run build` 生成生产版本
3. 部署 `dist` 文件夹到任何静态托管服务
4. 可选：使用 Electron 打包成桌面应用

---

## 📚 学习路径建议

### 🌱 初学者路径（1-2 小时）
```
1. 阅读 README.md（概览）        → 5 分钟
2. npm run dev（体验应用）       → 5 分钟
3. 探索 4 个功能（搜索、背、测） → 10 分钟
4. API_QUICK_REFERENCE 快速入门  → 20 分钟
5. 修改一个 API 调用（实践）    → 15 分钟
```

### 📈 中级开发者路径（3-4 小时）
```
1. API_QUICK_REFERENCE 完整学习  → 30 分钟
2. 阅读 src/api/index.ts 源代码  → 30 分钟
3. 理解 Mock API 实现逻辑       → 20 分钟
4. 修改组件并集成新 API          → 40 分钟
5. UPGRADE_SUMMARY 架构深度理解  → 30 分钟
```

### 🏆 高级开发者路径（1-2 天）
```
1. API_SPEC.md 完整阅读           → 1 小时
2. 设计后端数据库和接口          → 3 小时
3. 实现全部 15 个 API 端点        → 8 小时
4. 集成测试和质量保证            → 2 小时
```

---

## 🔗 文档关系图

```
README.md（项目主页）
    ↓
    ├─→ 快速开始 → npm run dev
    ├─→ 功能说明 → 了解 4 个核心页面
    ├─→ 文档导航 → 你现在看到的地方
    └─→ 技术栈说明
         ↓
    API_QUICK_REFERENCE.md（开发者指南）
         ↓
    实际 API 使用示例
         ↓
    API_SPEC.md（规范文档）
         ↓
    后端实现参考
    
UPGRADE_SUMMARY.md（架构文档）
    ↓
    ├─→ 版本演变
    ├─→ 代码变更
    ├─→ 技术亮点
    └─→ 已知问题
```

---

## ✅ 文档完整性检查清单

- [x] README.md - 项目概览（主要文档）
- [x] API_QUICK_REFERENCE.md - 开发指南
- [x] API_SPEC.md - 完整规范
- [x] UPGRADE_SUMMARY.md - 技术总结
- [x] .env.local.example - 配置模板
- [x] DOCS.md - 这个文件（导航）
- [x] 源代码注释 - JSDoc 文档

---

## 🎯 常见问题指南

### Q: 我应该从哪个文档开始？
**A:** 新用户请从 README.md 开始，5 分钟快速了解。

### Q: 如何快速找到某个 API 的用法？
**A:** 打开 API_QUICK_REFERENCE.md，Ctrl+F 搜索函数名。

### Q: 我要实现后端，需要什么？
**A:** 阅读 API_SPEC.md 第 2-3 章，有完整的数据模型和端点规范。

### Q: 修改了代码后怎么验证没有错误？
**A:** 运行 `npm run type-check`，确保零 TypeScript 错误。

### Q: 如何在 Mock API 和真实 API 间切换？
**A:** 修改 `.env.local` 中的 `VITE_USE_MOCK` 值，然后重启开发服务器。

### Q: 我能离线使用这个应用吗？
**A:** 可以！使用 Mock 模式完全离线，所有数据本地存储。

### Q: 如何部署到生产？
**A:** 运行 `npm run build`，部署 `dist` 文件夹到任何静态托管服务。

---

## 📞 获取帮助

### 本地开发问题
→ 查看 [README.md 故障排除部分](./README.md#-故障排除)

### API 集成问题
→ 查看 [API_QUICK_REFERENCE.md 错误处理部分](./API_QUICK_REFERENCE.md#错误处理最佳实践)

### 后端实现问题
→ 查看 [API_SPEC.md 实现指南部分](./API_SPEC.md#实现指南)

### UI/设计问题
→ 查看 [UPGRADE_SUMMARY.md 技术亮点部分](./UPGRADE_SUMMARY.md#设计亮点)

---

## 🎓 额外资源

### 官方文档
- [Vue 3 官方文档](https://vuejs.org/)
- [TypeScript 官方文档](https://www.typescriptlang.org/docs/)
- [Vite 官方文档](https://vitejs.dev/guide/)

### 在线工具
- [TypeScript Playground](https://www.typescriptlang.org/play)
- [Vue 3 SFC Playground](https://play.vuejs.org/)

---

**文档最后更新：2026-03-14**
**所有文档均已组织完毕，保持同步更新** ✨
