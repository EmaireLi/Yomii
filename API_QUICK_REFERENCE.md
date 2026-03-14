# API 使用快速参考

## 环境配置

### 创建 `.env.local`

```bash
# Mock 模式（当前推荐）
VITE_USE_MOCK=true
VITE_API_URL=http://localhost:3000/api

# --或-- 

# 真实后端模式（后端就绪时）
VITE_USE_MOCK=false
VITE_API_URL=http://localhost:3000/api
```

## API 客户端导入

```typescript
import {
  // 词汇查询
  searchWords,           // 搜索词汇
  getWord,              // 获取单词详情
  getRandomWordsAPI,    // 获取随机单词
  getAllWords,          // 获取词汇列表（分页）
  
  // 测试
  getQuizQuestions,     // 获取测试题目
  submitQuizAnswer,     // 提交答案
  
  // 用户数据
  updateWordProgress,   // 更新单词进度
  getStudyStats,        // 获取学习统计
  getUserProgress,      // 获取学习进度
  
  // 搜索历史
  getSearchHistory,     // 获取搜索历史
  
  // 收藏
  addToFavorites,       // 添加收藏
  removeFromFavorites,  // 移除收藏
  getFavorites,         // 获取收藏列表
} from '@/api'
```

## 常见用法

### 1. 搜索词汇

**基础搜索**
```typescript
const results = await searchWords('漢字')
console.log(results)  // [Word, Word, ...]
```

**带数量限制**
```typescript
const results = await searchWords('べん', 5)  // 最多返回 5 个结果
```

**错误处理**
```typescript
try {
  const results = await searchWords('keyword')
} catch (error) {
  console.error('搜索失败:', error.message)
}
```

### 2. 背单词

**获取随机单词进行背诵**
```typescript
const words = await getRandomWordsAPI(10)  // 获取 10 个随机单词

words.forEach(word => {
  console.log(word.word)      // 日语: 辞書
  console.log(word.kana)      // 假名: じしょ
  console.log(word.meaning)   // 释义: n. 词典
})
```

**更新学习进度**
```typescript
// 用户标记为已掌握
await updateWordProgress('1', 'known', true)

// 用户标记为模糊
await updateWordProgress('2', 'fuzzy', false)

// 用户标记为不认识
await updateWordProgress('3', 'unknown', false)
```

### 3. 测试对答

**获取测试题目**
```typescript
// 中级难度，10 个问题
const questions = await getQuizQuestions('medium', 10)

questions.forEach(q => {
  console.log(q.question)      // 题目文本
  console.log(q.options)       // 选项数组
  console.log(q.correctAnswer) // 正确答案
})
```

**提交答案**
```typescript
const userAnswer = 'せかい'
const isCorrect = userAnswer === question.correctAnswer

const result = await submitQuizAnswer(
  question.id,
  userAnswer,
  isCorrect
)

if (result.success) {
  console.log(`得分: ${result.score}`)
}
```

### 4. 学习统计

**获取个人统计数据**
```typescript
const stats = await getStudyStats()

console.log(`总背词数: ${stats.totalWordsRecited}`)
console.log(`今日背词: ${stats.todayRecited}`)
console.log(`连续天数: ${stats.currentStreak}`)
console.log(`最长连续: ${stats.longestStreak}`)
```

### 5. 管理收藏

**添加到收藏**
```typescript
const word = { id: '1', word: '辞書', ... }
const result = await addToFavorites(word.id, word)

if (result.success) {
  console.log('已添加到收藏')
}
```

**获取收藏列表**
```typescript
const favorites = await getFavorites()
console.log(favorites)  // [Word, Word, ...]
```

**移除收藏**
```typescript
await removeFromFavorites('1')
console.log('已从收藏移除')
```

## Vue 组件中的使用

### 在 `<script setup>` 中

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { searchWords } from '@/api'

const searchQuery = ref('')
const isLoading = ref(false)
const results = ref([])

const handleSearch = async () => {
  isLoading.value = true
  try {
    results.value = await searchWords(searchQuery.value)
  } catch (error) {
    console.error('搜索失败:', error)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div>
    <input v-model="searchQuery" @keyup.enter="handleSearch" />
    <button @click="handleSearch">搜索</button>
    
    <div v-if="isLoading">加载中...</div>
    
    <div v-for="word in results" :key="word.id">
      <h3>{{ word.word }}</h3>
      <p>{{ word.meaning }}</p>
    </div>
  </div>
</template>
```

## 切换 API 模式

### 当前（Mock 模式）
```
API 请求
  ↓
检查 USE_MOCK_API = true
  ↓
直接从 mockData.ts 返回数据
  ↓
完成！
```

### 之后（真实后端）
```
API 请求
  ↓
检查 USE_MOCK_API = false
  ↓
发送 HTTP 请求到 http://localhost:3000/api
  ↓
后端处理并返回 JSON
  ↓
完成！
```

**只需修改这一行：**
```typescript
// .env.local
VITE_USE_MOCK=false  # 改为 false
```

## 类型定义速查

### Word 类型
```typescript
interface Word {
  id: string
  word: string              // 日语词汇
  kana: string             // 假名
  meaning: string          // 中文释义
  example?: string         // 例句
  partOfSpeech?: string    // 词性
  audioUrl?: string        // 发音URL
  tags?: string[]          // 标签
}
```

### SearchResult 类型（扩展 Word）
```typescript
interface SearchResult extends Word {
  relevance?: number  // 相关度 0-1
}
```

### WordProgress 类型
```typescript
interface WordProgress {
  wordId: string
  status: 'unknown' | 'fuzzy' | 'known'
  reviewCount: number
  correctCount: number
  lastReviewedAt: number
}
```

### StudyStats 类型
```typescript
interface StudyStats {
  totalWordsLearned: number
  totalWordsRecited: number
  todayLearned: number
  todayRecited: number
  currentStreak: number
  longestStreak: number
  lastStudyDate: number
}
```

### QuizQuestion 类型
```typescript
interface QuizQuestion {
  id: string
  type: 'multiple-choice' | 'fill-blank' | 'listening'
  question: string
  word?: Word
  options: string[]
  correctAnswer: string
  explanation: string
}
```

## 错误处理最佳实践

```typescript
// ❌ 不好
const words = await searchWords('keyword')

// ✅ 好
try {
  const words = await searchWords('keyword')
  if (words.length === 0) {
    console.log('未找到结果')
  } else {
    // 处理结果
  }
} catch (error) {
  if (error instanceof Error) {
    console.error('搜索失败:', error.message)
  }
}
```

## 性能建议

1. **避免重复请求**
```typescript
// ❌ 不好 - 重复获取同一数据
for (let i = 0; i < 10; i++) {
  await getStudyStats()
}

// ✅ 好 - 获取一次，复用数据
const stats = await getStudyStats()
for (let i = 0; i < 10; i++) {
  console.log(stats.totalWordsRecited)
}
```

2. **使用批量接口**
```typescript
// ❌ 不好 - 多个单词发多次请求
for (const wordId of wordIds) {
  const word = await getWord(wordId)
}

// ✅ 好 - 一次获取随机单词（可配置数量）
const words = await getRandomWordsAPI(wordIds.length)
```

3. **缓存搜索结果**
```typescript
const searchCache = new Map()

const cachedSearch = async (keyword: string) => {
  if (searchCache.has(keyword)) {
    return searchCache.get(keyword)
  }
  const results = await searchWords(keyword)
  searchCache.set(keyword, results)
  return results
}
```

## 调试技巧

### 1. 查看 API 请求
```javascript
// 浏览器 DevTools -> Network 标签
// 查看所有 fetch 请求
```

### 2. 检查数据结构
```typescript
const words = await getRandomWordsAPI(1)
console.log(JSON.stringify(words, null, 2))
```

### 3. 验证 API 模式
```typescript
// 检查 .env 文件
console.log(import.meta.env.VITE_USE_MOCK)  // true 或 false
console.log(import.meta.env.VITE_API_URL)   // API 地址
```

---

**需要更多帮助？**
- 查看 `API_SPEC.md` 了解完整的 API 规范
- 查看 `UPGRADE_SUMMARY.md` 了解应用架构
- 查看各个组件源代码了解实际使用示例
