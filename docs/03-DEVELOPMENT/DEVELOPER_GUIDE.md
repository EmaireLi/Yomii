# 👨‍💻 开发者指南

## 🎯 目录
1. [项目结构](#项目结构)
2. [类型系统](#类型系统)
3. [组件使用](#组件使用)
4. [Hook 使用](#hook-使用)
5. [数据管理](#数据管理)
6. [扩展指南](#扩展指南)
7. [最佳实践](#最佳实践)

---

## 📁 项目结构

```
src/
├── App.vue                      # 主应用组件（路由管理）
├── main.ts                      # 应用入口
│
├── components/
│   ├── Sidebar.vue             # 侧边栏导航
│   └── views/
│       ├── HomeView.vue        # 首页视图
│       ├── SearchView.vue      # 查词视图
│       ├── ReciteView.vue      # 背单词视图
│       └── TestView.vue        # 测试视图
│
├── types/
│   └── index.ts                # TypeScript 类型定义
│
├── composables/
│   └── useLocalStorage.ts      # 本地存储 Hook
│
└── utils/
    ├── constants.ts            # 全局常量
    └── mockData.ts             # 模拟数据
```

---

## 🎯 类型系统

### 核心类型

```typescript
// 词语信息
interface Word {
  id: string
  word: string              // 日文词汇
  kana: string             // 假名读音
  meaning: string          // 中文释义
  example: string          // 例句
  partOfSpeech?: string    // 词性
  audioUrl?: string        // 音频链接
  tags?: string[]          // 标签
}

// 学习进度
interface WordProgress {
  wordId: string
  status: 'unknown' | 'fuzzy' | 'known'
  lastReviewedAt: number   // 最后复习时间戳
  reviewCount: number      // 复习次数
  correctCount: number     // 正确次数
}

// 学习统计
interface StudyStats {
  totalWordsLearned: number     // 总学习词数
  totalWordsRecited: number     // 总背词数
  todayLearned: number          // 今日新学词数
  todayRecited: number          // 今日背词数
  currentStreak: number         // 连续学习天数
  longestStreak: number         // 最长连续天数
  lastStudyDate: number         // 最后学习日期
}

// 测试题目
interface QuizQuestion {
  id: string
  type: 'multiple-choice' | 'fill-blank' | 'listening'
  question: string         // 题目
  word: Word              // 关联词汇
  options: string[]       // 选项列表
  correctAnswer: string   // 正确答案
  explanation: string     // 解析说明
}
```

---

## 🧩 组件使用

### App.vue - 主应用组件

```vue
<template>
  <el-container>
    <el-aside>侧边栏</el-aside>
    <el-main>主内容</el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import HomeView from '@/components/views/HomeView.vue'

const currentView = ref('home')

const switchView = (viewName: string) => {
  currentView.value = viewName
}
</script>
```

### SearchView - 查词视图

```vue
<script setup lang="ts">
import { ref } from 'vue'
import type { Word } from '@/types'
import { searchWords } from '@/api'
import { useSearchHistory, useFavorites } from '@/composables/useLocalStorage'

const { addSearch } = useSearchHistory()
const { toggleFavorite, isFavorited } = useFavorites()

const searchQuery = ref('')
const searchResult = ref<Word[]>([])

const handleSearch = async () => {
  if (searchQuery.value.trim()) {
    searchResult.value = await searchWords(searchQuery.value)
    addSearch(searchQuery.value)
  }
}
</script>
```

---

## 🎣 Hook 使用

### useSearchHistory - 搜索历史

```typescript
import { useSearchHistory } from '@/composables/useLocalStorage'

const { searchHistory, addSearch, clearHistory } = useSearchHistory()

// 添加搜索
addSearch('勉強')

// 获取历史
console.log(searchHistory.value)

// 清空历史
clearHistory()
```

### useFavorites - 收藏管理

```typescript
import { useFavorites } from '@/composables/useLocalStorage'

const { favorites, toggleFavorite, isFavorited } = useFavorites()

// 切换收藏
toggleFavorite('word-1')

// 检查是否收藏
const isLiked = isFavorited('word-1')
```

### useStudyStats - 学习统计

```typescript
import { useStudyStats } from '@/composables/useLocalStorage'

const { stats, incrementRecited, resetDailyStats } = useStudyStats()

// 查看统计
console.log(stats.value.totalWordsRecited)

// 增加计数
incrementRecited()
```

---

## 💾 数据管理

### 常量使用

```typescript
import { VIEWS, WORD_STATUS } from '@/utils/constants'

// 视图常量
console.log(VIEWS.HOME)
console.log(VIEWS.SEARCH)

```

### 模拟数据使用

```typescript
import {
  WORDS_DATABASE,
  QUIZ_QUESTIONS,
  searchWords,
  getRandomWords
} from '@/utils/mockData'

// 搜索词汇
const results = searchWords('勉')

// 随机获取词汇
const randomWords = getRandomWords(5)
```

---

## 🚀 扩展指南

### 添加新词汇

```typescript
// src/utils/mockData.ts

export const WORDS_DATABASE: Word[] = [
  {
    id: '11',
    word: '新しい',
    kana: 'あたらしい',
    meaning: 'adj. 新的',
    example: '新しい友達ができました。',
    partOfSpeech: 'adjective',
    tags: ['初级', '形容词']
  }
]
```

### 创建新的 Hook

```typescript
// src/composables/useLearningPlans.ts

import { ref, watch } from 'vue'

export function useLearningPlans() {
  const plans = ref([])
  
  const addPlan = (plan: any) => {
    plans.value.push(plan)
  }
  
  const removePlan = (id: string) => {
    plans.value = plans.value.filter(p => p.id !== id)
  }
  
  return {
    plans,
    addPlan,
    removePlan
  }
}
```

### 创建新视图组件

```vue
<!-- src/components/views/StatsView.vue -->

<template>
  <section class="view-section stats-view">
    <h1>学习统计</h1>
    <el-card>
      <!-- 内容 -->
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { useStudyStats } from '@/composables/useLocalStorage'

const { stats } = useStudyStats()
</script>

<style scoped>
.stats-view {
  padding: 20px;
}
</style>
```

---

## 📖 最佳实践

### ✅ 推荐做法

```typescript
// 1. 始终使用 TypeScript 类型
const words: Word[] = []

// 2. 使用计算属性缓存计算结果
const totalScore = computed(() => {
  return stats.known + stats.fuzzy
})

// 3. 在组件挂载时初始化数据
onMounted(() => {
  words.value = getRandomWords(10)
})

// 4. 使用 Hook 管理状态
const { stats, incrementRecited } = useStudyStats()

// 5. 使用作用域样式避免样式污染
<style scoped>
.container { /* ... */ }
</style>
```

### ❌ 避免的做法

```typescript
// 1. 避免任何类型
const words = []  // ❌

// 2. 避免直接修改对象
stats.totalRecited = 100  // ❌

// 3. 避免在模板中执行复杂逻辑
{{ words.filter(w => w.id === currentId).length }}  // ❌

// 4. 避免全局样式
<style>
.container { /* ... */ }  // ❌
</style>
```

---

## 🔧 文件编辑规范

### Vue 单文件组件 (SFC)

```vue
<template>
  <!-- HTML 模板，只能有一个根元素 -->
  <section class="component">
    <!-- 内容 -->
  </section>
</template>

<script setup lang="ts">
  // TypeScript 逻辑
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

### TypeScript 类型定义

```typescript
// src/types/index.ts 中定义

export interface Word {
  id: string
  word: string
  kana: string
  meaning: string
}

export enum StudyStatus {
  Unknown = 'unknown',
  Fuzzy = 'fuzzy',
  Known = 'known'
}

export type WordList = Word[]
```

---

## 🔗 相关资源

- [Vue 3 官方文档](https://vuejs.org/)
- [TypeScript 文档](https://www.typescriptlang.org/)
- [Vite 文档](https://vitejs.dev/)
- [Element Plus 文档](https://element-plus.org/zh-CN/)

---

**最后更新**：2026年3月18日
