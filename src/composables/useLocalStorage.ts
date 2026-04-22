import { ref, watch, onUnmounted } from 'vue'
import type { UserData, StudyPlan, LearningSession } from '@/types'
import { DEFAULT_APP_CONFIG, LOCAL_STORAGE_KEYS, DEFAULT_STUDY_PLAN } from '@/utils/constants'
import {
  getStudyStats,
  isAuthenticated,
  addToFavorites as addToFavoritesAPI,
  removeFromFavorites as removeFromFavoritesAPI,
  getSearchHistory as getSearchHistoryAPI,
  getUserProgress,
  updateWordProgress as updateWordProgressAPI,
} from '@/api'

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

  const syncSearchHistory = async () => {
    if (!isAuthenticated()) {
      searchHistory.value = []
      return
    }

    try {
      const rows = await getSearchHistoryAPI(50)
      searchHistory.value = rows.map(row => row.keyword)
    } catch (error) {
      console.error('Failed to sync search history:', error)
    }
  }

  const handleLogoutClear = () => {
    searchHistory.value = []
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('yomii:logout', handleLogoutClear)
  }

  onUnmounted(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('yomii:logout', handleLogoutClear)
    }
  })

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

  if (isAuthenticated()) {
    void syncSearchHistory()
  }

  return {
    searchHistory,
    addSearch,
    removeSearch,
    clearHistory,
    syncSearchHistory
  }
}

/**
 * 使用本地存储 - 收藏夹 (支持后端同步)
 */
export function useFavorites() {
  const favorites = ref<string[]>(
    getStorageItem(LOCAL_STORAGE_KEYS.FAVORITES, [])
  )

  /**
   * 切换收藏状态 (同步到后端)
   */
  const toggleFavorite = async (wordId: string) => {
    const index = favorites.value.indexOf(wordId)
    const isFavorited = index > -1

    try {
      if (isFavorited) {
        // 移除收藏
        if (isAuthenticated()) {
          await removeFromFavoritesAPI(wordId)
        }
        favorites.value.splice(index, 1)
      } else {
        // 添加收藏
        if (isAuthenticated()) {
          await addToFavoritesAPI(wordId)
        }
        favorites.value.push(wordId)
      }
    } catch (error) {
      // 如果后端操作失败，回滚本地状态
      if (isFavorited) {
        favorites.value.push(wordId) // 还原已删除的项
      } else {
        favorites.value.splice(index, 1) // 还原已添加的项
      }
      throw error
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

  const resetStats = () => {
    stats.value = { ...defaultStats }
  }

  const toDayStartMs = (timestamp: number): number => {
    if (!timestamp) return 0
    const date = new Date(timestamp)
    return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
  }

  const dayDiff = (fromTimestamp: number, toTimestamp: number): number => {
    if (!fromTimestamp || !toTimestamp) return 0
    const oneDayMs = 24 * 60 * 60 * 1000
    const from = toDayStartMs(fromTimestamp)
    const to = toDayStartMs(toTimestamp)
    return Math.floor((to - from) / oneDayMs)
  }

  const normalizeDailyStats = () => {
    const lastStudyDate = stats.value.lastStudyDate
    if (!lastStudyDate) return

    const diff = dayDiff(lastStudyDate, Date.now())
    if (diff >= 1) {
      stats.value.todayLearned = 0
      stats.value.todayRecited = 0
    }
    if (diff > 1) {
      stats.value.currentStreak = 0
    }
  }

  normalizeDailyStats()

  const incrementRecited = () => {
    const now = Date.now()
    const lastStudyDate = stats.value.lastStudyDate
    const isSameDay = toDayStartMs(lastStudyDate) === toDayStartMs(now)

    if (!isSameDay) {
      stats.value.todayLearned = 0
      stats.value.todayRecited = 0
    }

    stats.value.totalWordsRecited++
    stats.value.todayRecited++

    if (!lastStudyDate) {
      stats.value.currentStreak = 1
    } else if (!isSameDay) {
      const diff = dayDiff(lastStudyDate, now)
      if (diff === 1) {
        stats.value.currentStreak += 1
      } else if (diff > 1) {
        stats.value.currentStreak = 1
      }
    }

    stats.value.longestStreak = Math.max(
      stats.value.longestStreak,
      stats.value.currentStreak
    )
    stats.value.lastStudyDate = now
  }

  const resetDailyStats = () => {
    stats.value.todayLearned = 0
    stats.value.todayRecited = 0
  }

  const syncStudyStats = async () => {
    if (!isAuthenticated()) return
    try {
      const remoteStats = await getStudyStats()
      stats.value = {
        ...defaultStats,
        ...remoteStats
      }
      normalizeDailyStats()
    } catch (error) {
      console.error('Failed to sync study stats:', error)
    }
  }

  const handleLoginSync = () => {
    void syncStudyStats()
  }

  const handleLogoutReset = () => {
    resetStats()
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('yomii:login', handleLoginSync)
    window.addEventListener('yomii:logout', handleLogoutReset)
  }

  onUnmounted(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('yomii:login', handleLoginSync)
      window.removeEventListener('yomii:logout', handleLogoutReset)
    }
  })

  watch(
    stats,
    (newVal) => {
      setStorageItem(LOCAL_STORAGE_KEYS.STUDY_STATS, newVal)
    },
    { deep: true }
  )

  if (isAuthenticated()) {
    void syncStudyStats()
  }

  return {
    stats,
    incrementRecited,
    resetDailyStats,
    syncStudyStats
  }
}

/**
 * 使用本地存储 - 词汇学习进度
 */
export function useWordProgress() {
  const wordProgress = ref(
    getStorageItem(LOCAL_STORAGE_KEYS.WORD_PROGRESS, {} as Record<string, any>)
  )

  const syncWordProgress = async () => {
    if (!isAuthenticated()) {
      wordProgress.value = {}
      return
    }

    try {
      const rows = await getUserProgress()
      const mapped: Record<string, any> = {}
      for (const row of rows) {
        mapped[String(row.wordId)] = row
      }
      wordProgress.value = mapped
    } catch (error) {
      console.error('Failed to sync word progress:', error)
    }
  }

  const handleLogoutClear = () => {
    wordProgress.value = {}
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('yomii:logout', handleLogoutClear)
  }

  onUnmounted(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('yomii:logout', handleLogoutClear)
    }
  })

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

    if (isAuthenticated()) {
      void updateWordProgressAPI(wordId, status, status === 'known').catch((error) => {
        console.error('Failed to sync progress update:', error)
      })
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

  if (isAuthenticated()) {
    void syncWordProgress()
  }

  return {
    wordProgress,
    updateProgress,
    getProgress,
    syncWordProgress
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
