/**
 * 本地存储组合函数
 */

import { ref, watch } from 'vue'
import type { UserData, StudyPlan, LearningSession } from '@/types'
import { DEFAULT_APP_CONFIG, LOCAL_STORAGE_KEYS, DEFAULT_STUDY_PLAN } from '@/utils/constants'

/**
 * 从localStorage中读取数据
 */
function getStorageItem<T>(key: string, defaultValue: T): T {
  try {
    const item = localStorage.getItem(key)
    return item ? JSON.parse(item) : defaultValue
  } catch {
    console.warn(`Failed to parse localStorage item: ${key}`)
    return defaultValue
  }
}

/**
 * 向localStorage中保存数据
 */
function setStorageItem<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (error) {
    console.error(`Failed to save to localStorage: ${key}`, error)
  }
}

/**
 * 使用本地存储 - 搜索历史
 */
export function useSearchHistory() {
  const searchHistory = ref<string[]>(
    getStorageItem(LOCAL_STORAGE_KEYS.SEARCH_HISTORY, [])
  )

  const addSearch = (query: string) => {
    if (!query.trim()) return
    
    const history = searchHistory.value
    // 移除重复项
    const index = history.indexOf(query)
    if (index > -1) history.splice(index, 1)
    
    // 新搜索加到最前面，保持最多50条
    history.unshift(query)
    if (history.length > 50) history.pop()
  }

  const removeSearch = (index: number) => {
    searchHistory.value.splice(index, 1)
  }

  const clearHistory = () => {
    searchHistory.value = []
  }

  watch(
    searchHistory,
    (newVal) => {
      setStorageItem(LOCAL_STORAGE_KEYS.SEARCH_HISTORY, newVal)
    },
    { deep: true }
  )

  return {
    searchHistory,
    addSearch,
    removeSearch,
    clearHistory
  }
}

/**
 * 使用本地存储 - 收藏夹
 */
export function useFavorites() {
  const favorites = ref<string[]>(
    getStorageItem(LOCAL_STORAGE_KEYS.FAVORITES, [])
  )

  const toggleFavorite = (wordId: string) => {
    const index = favorites.value.indexOf(wordId)
    if (index > -1) {
      favorites.value.splice(index, 1)
    } else {
      favorites.value.push(wordId)
    }
  }

  const isFavorited = (wordId: string): boolean => {
    return favorites.value.includes(wordId)
  }

  watch(
    favorites,
    (newVal) => {
      setStorageItem(LOCAL_STORAGE_KEYS.FAVORITES, newVal)
    },
    { deep: true }
  )

  return {
    favorites,
    toggleFavorite,
    isFavorited
  }
}

/**
 * 使用本地存储 - 学习统计
 */
export function useStudyStats() {
  const defaultStats = {
    totalWordsLearned: 0,
    totalWordsRecited: 0,
    todayLearned: 0,
    todayRecited: 0,
    currentStreak: 0,
    longestStreak: 0,
    lastStudyDate: 0
  }

  const stats = ref(
    getStorageItem(LOCAL_STORAGE_KEYS.STUDY_STATS, defaultStats)
  )

  const incrementRecited = () => {
    const today = new Date().toDateString()
    const lastDate = new Date(stats.value.lastStudyDate).toDateString()
    
    stats.value.totalWordsRecited++
    stats.value.todayRecited++
    
    if (today === lastDate) {
      // 同一天，延长连续天数逻辑在这里处理
    } else {
      stats.value.lastStudyDate = Date.now()
      stats.value.currentStreak = 1
    }
  }

  const resetDailyStats = () => {
    stats.value.todayLearned = 0
    stats.value.todayRecited = 0
  }

  watch(
    stats,
    (newVal) => {
      setStorageItem(LOCAL_STORAGE_KEYS.STUDY_STATS, newVal)
    },
    { deep: true }
  )

  return {
    stats,
    incrementRecited,
    resetDailyStats
  }
}

/**
 * 使用本地存储 - 词汇学习进度
 */
export function useWordProgress() {
  const wordProgress = ref(
    getStorageItem(LOCAL_STORAGE_KEYS.WORD_PROGRESS, {} as Record<string, any>)
  )

  const updateProgress = (wordId: string, status: 'unknown' | 'fuzzy' | 'known') => {
    if (!wordProgress.value[wordId]) {
      wordProgress.value[wordId] = {
        wordId,
        status,
        lastReviewedAt: Date.now(),
        reviewCount: 1,
        correctCount: status === 'known' ? 1 : 0
      }
    } else {
      const progress = wordProgress.value[wordId]
      progress.status = status
      progress.lastReviewedAt = Date.now()
      progress.reviewCount++
      if (status === 'known') progress.correctCount++
    }
  }

  const getProgress = (wordId: string) => {
    return wordProgress.value[wordId] || null
  }

  watch(
    wordProgress,
    (newVal) => {
      setStorageItem(LOCAL_STORAGE_KEYS.WORD_PROGRESS, newVal)
    },
    { deep: true }
  )

  return {
    wordProgress,
    updateProgress,
    getProgress
  }
}

/**
 * 使用本地存储 - 学习计划管理
 */
export function useStudyPlan() {
  const studyPlans = ref<StudyPlan[]>(
    getStorageItem(LOCAL_STORAGE_KEYS.STUDY_PLANS, [DEFAULT_STUDY_PLAN])
  )
  
  const currentPlan = ref<StudyPlan | null>(
    getStorageItem(LOCAL_STORAGE_KEYS.CURRENT_PLAN, DEFAULT_STUDY_PLAN)
  )
  
  const learningSessions = ref<LearningSession[]>(
    getStorageItem(LOCAL_STORAGE_KEYS.LEARNING_SESSIONS, [])
  )

  // 添加新的学习计划
  const addPlan = (name: string, dailyGoal: number, reviewRatio: number = 0.5) => {
    const newPlan: StudyPlan = {
      id: `plan_${Date.now()}`,
      name,
      dailyGoal,
      reviewRatio,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      isActive: false
    }
    studyPlans.value.push(newPlan)
    return newPlan
  }

  // 更新学习计划
  const updatePlan = (planId: string, updates: Partial<StudyPlan>) => {
    const planIndex = studyPlans.value.findIndex(p => p.id === planId)
    if (planIndex > -1) {
      studyPlans.value[planIndex] = {
        ...studyPlans.value[planIndex],
        ...updates,
        updatedAt: Date.now()
      } as StudyPlan
      
      if (currentPlan.value?.id === planId) {
        currentPlan.value = { ...studyPlans.value[planIndex] } as StudyPlan
      }
    }
  }

  // 激活学习计划
  const activatePlan = (planId: string) => {
    // 取消所有其他计划的激活状态
    studyPlans.value.forEach(p => {
      p.isActive = p.id === planId
    })
    
    const activated = studyPlans.value.find(p => p.id === planId)
    if (activated) {
      currentPlan.value = activated
    }
  }

  // 删除学习计划
  const deletePlan = (planId: string) => {
    studyPlans.value = studyPlans.value.filter(p => p.id !== planId)
    if (currentPlan.value?.id === planId) {
      currentPlan.value = studyPlans.value[0] || null
    }
  }

  // 获取计划
  const getPlan = (planId: string) => {
    return studyPlans.value.find(p => p.id === planId) || null
  }

  // 保存学习轮次
  const saveLearningSession = (session: Omit<LearningSession, 'id'>) => {
    const newSession: LearningSession = {
      ...session,
      id: `session_${Date.now()}`
    }
    learningSessions.value.push(newSession)
    return newSession
  }

  // 获取特定日期的学习轮次
  const getSessionsByDate = (date: string) => {
    return learningSessions.value.filter(s => s.date === date)
  }

  // 获取计划的所有学习轮次
  const getSessionsByPlan = (planId: string) => {
    return learningSessions.value.filter(s => s.planId === planId)
  }

  // 监听变化并保存到localStorage
  watch(
    studyPlans,
    (newVal) => {
      setStorageItem(LOCAL_STORAGE_KEYS.STUDY_PLANS, newVal)
    },
    { deep: true }
  )

  watch(
    currentPlan,
    (newVal) => {
      if (newVal) {
        setStorageItem(LOCAL_STORAGE_KEYS.CURRENT_PLAN, newVal)
      }
    },
    { deep: true }
  )

  watch(
    learningSessions,
    (newVal) => {
      setStorageItem(LOCAL_STORAGE_KEYS.LEARNING_SESSIONS, newVal)
    },
    { deep: true }
  )

  return {
    studyPlans,
    currentPlan,
    learningSessions,
    addPlan,
    updatePlan,
    activatePlan,
    deletePlan,
    getPlan,
    saveLearningSession,
    getSessionsByDate,
    getSessionsByPlan
  }
}
