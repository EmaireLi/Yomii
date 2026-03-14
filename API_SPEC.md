# Yomii API 后端接口文档

## 概述

Yomii 应用现已支持后端 API 集成。目前使用 **Mock API** 模式，前端可以立即测试所有功能。当您准备好后端实现时，只需更新环境变量即可切换到真实 API。

## 配置

### 环境变量设置

在项目根目录创建 `.env.local` 文件：

```bash
# Mock 模式（默认）- 使用内置数据测试
VITE_USE_MOCK=true
VITE_API_URL=http://localhost:3000/api

# 真实后端模式 - 连接到实际服务器
# VITE_USE_MOCK=false
# VITE_API_URL=http://localhost:3000/api
```

## API 端点规范

### 1. 词汇查询

#### 搜索词汇
```
GET /api/words/search?q=keyword&limit=10
```

**参数：**
- `q` (string, required): 搜索关键词（支持假名、汉字、中文）
- `limit` (number, optional): 返回结果数量，默认 10

**响应：**
```json
[
  {
    "id": "1",
    "word": "辞書",
    "kana": "じしょ",
    "meaning": "n. 词典，字典",
    "example": "新しい辞書を買いました。(买了一本新词典。)",
    "partOfSpeech": "noun",
    "audioUrl": "https://example.com/audio/1.mp3",
    "tags": ["初级", "常用"]
  }
]
```

#### 获取单词详情
```
GET /api/words/:id
```

**响应：** 单个 Word 对象

#### 获取随机单词（背单词用）
```
GET /api/words/random?count=5
```

**参数：**
- `count` (number): 返回随机单词数量，默认 5

**响应：**
```json
[
  { Word 对象1 },
  { Word 对象2 },
  ...
]
```

#### 获取所有单词列表（分页）
```
GET /api/words?page=1&limit=20
```

**参数：**
- `page` (number): 页码，从 1 开始
- `limit` (number): 每页数量，默认 20

**响应：**
```json
{
  "words": [ 单词数组 ],
  "total": 130
}
```

### 2. 测试/答题

#### 获取测试题目
```
GET /api/quiz/questions?difficulty=medium&count=10
```

**参数：**
- `difficulty` (string): 难度等级 - 'easy' | 'medium' | 'hard'
- `count` (number): 题目数量，默认 10

**响应：**
```json
[
  {
    "id": "q1",
    "type": "multiple-choice",
    "question": "以下哪个选项是「世界」的正确读音？",
    "word": { Word 对象 },
    "options": ["せかい", "しゃかい", "じだい", "みらい"],
    "correctAnswer": "せかい",
    "explanation": "「世界」的正确读音是せかい(sekai)..."
  }
]
```

#### 提交答案
```
POST /api/quiz/submit
Content-Type: application/json

{
  "questionId": "q1",
  "userAnswer": "せかい",
  "isCorrect": true
}
```

**响应：**
```json
{
  "success": true,
  "score": 1
}
```

### 3. 用户学习进度

#### 更新单词学习状态
```
POST /api/user/progress/:wordId
Content-Type: application/json

{
  "status": "known" | "fuzzy" | "unknown",
  "isCorrect": true
}
```

**响应：**
```json
{
  "wordId": "1",
  "status": "known",
  "reviewCount": 5,
  "correctCount": 4,
  "lastReviewedAt": 1704067200000
}
```

#### 获取用户学习统计
```
GET /api/user/stats
```

**响应：**
```json
{
  "totalWordsLearned": 50,
  "totalWordsRecited": 150,
  "todayLearned": 5,
  "todayRecited": 15,
  "currentStreak": 7,
  "longestStreak": 14,
  "lastStudyDate": 1704067200000
}
```

#### 获取用户学习进度
```
GET /api/user/progress
```

**响应：**
```json
[
  {
    "wordId": "1",
    "status": "known",
    "reviewCount": 5,
    "correctCount": 4,
    "lastReviewedAt": 1704067200000
  },
  ...
]
```

### 4. 搜索历史

#### 获取搜索历史
```
GET /api/user/search-history?limit=10
```

**参数：**
- `limit` (number): 返回记录数，默认 10

**响应：**
```json
[
  { SearchResult 对象 },
  ...
]
```

### 5. 收藏管理

#### 添加到收藏夹
```
POST /api/user/favorites/:wordId
Content-Type: application/json

{
  "id": "1",
  "word": "辞書",
  "kana": "じしょ",
  ...
}
```

**响应：**
```json
{
  "success": true
}
```

#### 从收藏夹移除
```
DELETE /api/user/favorites/:wordId
```

**响应：**
```json
{
  "success": true
}
```

#### 获取收藏夹
```
GET /api/user/favorites
```

**响应：**
```json
[
  { Word 对象 },
  ...
]
```

## 数据模型

### Word（词汇）
```typescript
interface Word {
  id: string                 // 唯一标识
  word: string              // 日语词汇
  kana: string              // 假名读音
  meaning: string           // 中文释义
  example?: string          // 例句
  partOfSpeech?: string     // 词性
  audioUrl?: string         // 发音音频URL
  tags?: string[]           // 分类标签
}
```

### SearchResult（搜索结果）
```typescript
interface SearchResult extends Word {
  relevance?: number        // 相关度分数 (0-1)
}
```

### WordProgress（单词学习进度）
```typescript
interface WordProgress {
  wordId: string           // 单词ID
  status: 'unknown' | 'fuzzy' | 'known'  // 掌握程度
  reviewCount: number      // 复习次数
  correctCount: number     // 正确次数
  lastReviewedAt: number   // 最后复习时间戳
}
```

### QuizQuestion（测试题目）
```typescript
interface QuizQuestion {
  id: string              // 题目ID
  type: 'multiple-choice' | 'fill-blank' | 'listening'
  question: string        // 题目内容
  word?: Word            // 关联词汇
  options: string[]       // 选项
  correctAnswer: string   // 正确答案
  explanation: string     // 解释说明
}
```

### StudyStats（学习统计）
```typescript
interface StudyStats {
  totalWordsLearned: number    // 总学习词汇数
  totalWordsRecited: number    // 总背诵词汇数
  todayLearned: number         // 今日学习数
  todayRecited: number         // 今日背诵数
  currentStreak: number        // 当前连续天数
  longestStreak: number        // 最长连续天数
  lastStudyDate: number        // 最后学习日期时间戳
}
```

## 实现指南

### 后端实现建议

1. **数据库设计**
   - `words` 表：存储所有日语词汇
   - `users` 表：用户账户信息
   - `user_progress` 表：用户学习进度
   - `study_history` 表：学习历史记录
   - `quiz_questions` 表：测试题库

2. **认证方案**
   建议添加基本认证或 JWT token 验证

3. **分页处理**
   所有列表接口支持分页，使用 `offset` 和 `limit` 参数

4. **错误处理**
   返回标准 HTTP 状态码：
   - `200`: 成功
   - `400`: 请求参数错误
   - `401`: 未授权
   - `404`: 资源不存在
   - `500`: 服务器错误

### 切换到真实后端

1. 实现后端 API
2. 启动后端服务，例如 http://localhost:3000
3. 修改 `.env.local`：
   ```bash
   VITE_USE_MOCK=false
   VITE_API_URL=http://localhost:3000/api
   ```
4. 重启前端开发服务器

## 前端 API 调用示例

```typescript
import * as API from '@/api'

// 搜索单词
const results = await API.searchWords('漢字', 10)

// 获取随机单词用于背单词
const words = await API.getRandomWordsAPI(5)

// 获取测试题目
const questions = await API.getQuizQuestions('medium', 10)

// 提交答案
const result = await API.submitQuizAnswer('q1', 'せかい', true)

// 更新学习进度
const progress = await API.updateWordProgress('1', 'known', true)

// 获取学习统计
const stats = await API.getStudyStats()
```

## 现状

✅ **前端完全准备就绪**
- 所有 API 调用已实现
- Mock API 可立即测试所有功能
- TypeScript 类型定义完整
- 错误处理已配置

⏳ **等待后端实现**
- 按上述规范实现 API 端点
- 配置数据库
- 实现认证机制

## 问题排查

### 如何测试当前应用
```bash
npm run dev
# 访问 http://localhost:5174
```

### 如何切换 API 模式
编辑 `.env.local` 并重启开发服务器

### 获取详细 API 调试日志
在浏览器 DevTools Console 中查看所有 fetch 请求

---

**Last Updated**: 2026-03-14
**API Version**: 1.0
**Status**: Mock Mode (Ready for Backend Integration)
