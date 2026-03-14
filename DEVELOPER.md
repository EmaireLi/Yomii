# 👨‍💻 Yomii 辞书 - 开发者指南

## 🎯 目录
1. [项目结构](#项目结构)
2. [类型系统](#类型系统)
3. [组件使用](#组件使用)
4. [Hook 使用](#hook-使用)
5. [数据管理](#数据管理)
6. [扩展指南](#扩展指南)

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
// src/types/index.ts 中定义的所有类型

// 词语信息
interface Word {
  id: string
  word: string              // 日文词汇 (例: "勉強")
  kana: string             // 假名读音 (例: "べんきょう")
  meaning: string          // 中文释义 (例: "学习、用功")
  example: string          // 例句
  partOfSpeech?: string    // 词性 (例: "noun", "verb")
  audioUrl?: string        // 音频链接
  tags?: string[]          // 标签 (例: ["初级", "日常"])
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
  totalWordsLearned: number    // 总学习词数
  totalWordsRecited: number    // 总背词数
  todayLearned: number         // 今日新学词数
  todayRecited: number         // 今日背词数
  currentStreak: number        // 连续学习天数
  longestStreak: number        // 最长连续天数
  lastStudyDate: number        // 最后学习日期
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

### 使用类型

```typescript
import type { Word, WordProgress, StudyStats } from '@/types'

// 在组件中使用
const currentWord: Word = {
  id: '1',
  word: '勉強',
  kana: 'べんきょう',
  meaning: '学习、用功',
  example: '毎日勉強します',
  partOfSpeech: 'noun'
}

// 定义函数返回类型
function getWord(id: string): Word | undefined {
  // ...
}

// 定义变量类型
const stats: StudyStats = {
  totalWordsLearned: 0,
  totalWordsRecited: 0,
  todayLearned: 0,
  todayRecited: 0,
  currentStreak: 0,
  longestStreak: 0,
  lastStudyDate: 0
}
```

---

## 🧩 组件使用

### App.vue - 主应用组件

```vue
<template>
  <div class="yomii-app">
    <Sidebar :current-view="currentView" @select="switchView" />
    <main class="content">
      <HomeView v-if="currentView === 'home'" />
      <SearchView v-else-if="currentView === 'search'" />
      <ReciteView v-else-if="currentView === 'recite'" />
      <TestView v-else-if="currentView === 'test'" @switch-view="switchView" />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import HomeView from '@/components/views/HomeView.vue'
// ... 导入其他视图

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
import { searchWords } from '@/utils/mockData'
import { useSearchHistory, useFavorites } from '@/composables/useLocalStorage'

// 获取 Hook
const { addSearch } = useSearchHistory()
const { toggleFavorite, isFavorited } = useFavorites()

// 本地状态
const searchQuery = ref('')
const searchResult = ref<Word[]>([])

// 执行搜索
const handleSearch = () => {
  if (searchQuery.value.trim()) {
    searchResult.value = searchWords(searchQuery.value)
    addSearch(searchQuery.value)  // 保存搜索历史
  }
}

// 收藏词汇
const toggleFav = (wordId: string) => {
  toggleFavorite(wordId)
}

// 检查是否收藏
const isFav = (wordId: string): boolean => isFavorited(wordId)
</script>
```

### ReciteView - 背单词视图

```vue
<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { Word } from '@/types'
import { getRandomWords } from '@/utils/mockData'
import { useWordProgress, useStudyStats } from '@/composables/useLocalStorage'

// 获取 Hook
const { updateProgress } = useWordProgress()
const { incrementRecited } = useStudyStats()

// 状态管理
const words = ref<Word[]>([])
const currentIndex = ref(0)
const showMeaning = ref(false)

const stats = reactive({
  known: 0,
  fuzzy: 0,
  unknown: 0
})

// 初始化
const initCards = () => {
  words.value = getRandomWords(10)
  currentIndex.value = 0
}

// 评价词汇
const nextWord = (status: 'unknown' | 'fuzzy' | 'known') => {
  const currentWord = words.value[currentIndex.value]
  
  if (currentWord) {
    // 更新进度跟踪
    updateProgress(currentWord.id, status)
    
    // 更新学习统计
    incrementRecited()
    
    // 更新本地统计
    stats[status]++
    
    // 移到下一个词
    currentIndex.value++
    showMeaning.value = false
  }
}

onMounted(() => initCards())
</script>
```

---

## 🎣 Hook 使用

### useSearchHistory - 搜索历史

**功能**：管理搜索历史记录

```typescript
import { useSearchHistory } from '@/composables/useLocalStorage'

// 获取 Hook
const { searchHistory, addSearch, clearHistory } = useSearchHistory()

// 添加搜索
addSearch('勉強')
addSearch('桜')

// 获取历史
console.log(searchHistory.value)  // ['桜', '勉強']

// 清空历史
clearHistory()

// 在模板中
<button
  v-for="history in searchHistory"
  @click="searchQuery = history; handleSearch()"
>
  {{ history }}
</button>
```

### useFavorites - 收藏管理

**功能**：管理收藏词汇

```typescript
import { useFavorites } from '@/composables/useLocalStorage'

const { favorites, toggleFavorite, isFavorited } = useFavorites()

// 切换收藏
toggleFavorite('word-1')  // 如果未收藏则收藏，反之取消

// 检查是否收藏
const isLiked = isFavorited('word-1')  // true/false

// 获取所有收藏
console.log(favorites.value)  // ['word-1', 'word-2']

// 在模板中
<button
  @click="toggleFavorite(word.id)"
  :class="{ active: isFavorited(word.id) }"
>
  ❤️
</button>
```

### useStudyStats - 学习统计

**功能**：追踪学习统计数据

```typescript
import { useStudyStats } from '@/composables/useLocalStorage'

const { stats, incrementRecited, resetDailyStats } = useStudyStats()

// 查看统计
console.log(stats.value.totalWordsRecited)  // 总背词数
console.log(stats.value.todayRecited)       // 今日背词数
console.log(stats.value.currentStreak)      // 连续天数

// 增加背词计数
incrementRecited()

// 重置每日数据（午夜调用）
resetDailyStats()

// 在模板中
<div>
  <span>{{ stats.totalWordsRecited }} 词</span>
  <span>{{ stats.todayRecited }} 今日</span>
  <span>{{ stats.currentStreak }} 🔥</span>
</div>
```

### useWordProgress - 词汇进度

**功能**：跟踪个别词汇的学习进度

```typescript
import { useWordProgress } from '@/composables/useLocalStorage'

const { wordProgress, updateProgress, getProgress } = useWordProgress()

// 更新进度
updateProgress('word-1', 'known')      // 标记为已掌握
updateProgress('word-2', 'fuzzy')      // 标记为模糊
updateProgress('word-3', 'unknown')    // 标记为未学

// 获取进度
const progress = getProgress('word-1')
// {
//   wordId: 'word-1',
//   status: 'known',
//   lastReviewedAt: 1234567890,
//   reviewCount: 3,
//   correctCount: 2
// }

// 查看所有进度
console.log(wordProgress.value)
```

---

## 💾 数据管理

### 常量使用

```typescript
import { VIEWS, WORD_STATUS, TEAM_INFO } from '@/utils/constants'

// 视图常量
console.log(VIEWS.HOME)     // 'home'
console.log(VIEWS.SEARCH)   // 'search'
console.log(VIEWS.RECITE)   // 'recite'
console.log(VIEWS.TEST)     // 'test'

// 词语状态
const status = WORD_STATUS.KNOWN  // 'known'

// 团队信息
TEAM_INFO.members.forEach(member => {
  console.log(member.name, member.role)
})
```

### 模拟数据使用

```typescript
import {
  WORDS_DATABASE,
  QUIZ_QUESTIONS,
  searchWords,
  getRandomWords,
  getWordById
} from '@/utils/mockData'

// 获取所有词汇
const allWords = WORDS_DATABASE

// 搜索词汇
const results = searchWords('勉')  // 返回包含"勉"的词汇

// 随机获取词汇
const randomWords = getRandomWords(5)  // 获取 5 个随机词汇

// 根据 ID 获取词汇
const word = getWordById('1')

// 获取所有测试题目
const questions = QUIZ_QUESTIONS
```

---

## 🚀 扩展指南

### 添加新词汇

```typescript
// src/utils/mockData.ts

export const WORDS_DATABASE: Word[] = [
  // ... 现有词汇
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

### 添加新测试题目

```typescript
// src/utils/mockData.ts

export const QUIZ_QUESTIONS: QuizQuestion[] = [
  // ... 现有题目
  {
    id: 'q4',
    type: 'multiple-choice',
    question: '「新しい」的意思是？',
    word: WORDS_DATABASE[10],
    options: ['新的', '旧的', '白色', '黑色'],
    correctAnswer: '新的',
    explanation: '「新しい」(あたらしい)表示新的、刚出现的。'
  }
]
```

### 创建新的 Hook

```typescript
// src/composables/useLearningPlans.ts

import { ref, watch } from 'vue'

export function useLearningPlans() {
  const plans = ref<Plan[]>([])
  
  const addPlan = (plan: Plan) => {
    plans.value.push(plan)
  }
  
  const removePlan = (id: string) => {
    plans.value = plans.value.filter(p => p.id !== id)
  }
  
  watch(plans, (newVal) => {
    localStorage.setItem('learning_plans', JSON.stringify(newVal))
  }, { deep: true })
  
  return {
    plans,
    addPlan,
    removePlan
  }
}
```

### 创建新的视图组件

```vue
<!-- src/components/views/StatsView.vue -->

<template>
  <section class="view-section stats-view">
    <h1>学习统计</h1>
    <div class="stats-dashboard">
      <!-- 您的内容 -->
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useStudyStats, useWordProgress } from '@/composables/useLocalStorage'

const { stats } = useStudyStats()
const { wordProgress } = useWordProgress()

// 您的逻辑
</script>

<style scoped>
/* 您的样式 */
</style>
```

然后在 App.vue 中添加：

```vue
<StatsView v-else-if="currentView === 'stats'" />

<!-- 并更新 switchView 函数 -->
<Sidebar @select="switchView" />
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

// 2. 避免直接修改深层对象
stats.totalRecited = 100  // ❌ 使用 Hook 方法

// 3. 避免在模板中执行复杂逻辑
{{ words.filter(w => w.id === currentId).length }}  // ❌

// 4. 避免全局样式污染
<style>
.container { /* ... */ }  // ❌
</style>
```

---

## 🔗 相关资源

- [Vue 3 官方文档](https://vuejs.org/)
- [TypeScript 文档](https://www.typescriptlang.org/)
- [Vite 文档](https://vitejs.dev/)
- [localStorage 文档](https://developer.mozilla.org/zh-CN/docs/Web/API/Window/localStorage)

---

**最后更新**：2026-03-14  
**版本**：1.0.0  
祝编码愉快！🚀
