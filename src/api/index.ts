/**
 * API 客户端
 * 
 * 所有数据通过 API 接口获取和提交
 * 支持 Mock 模式和真实后端两种模型
 */

import type { Word, SearchResult, QuizQuestion, WordProgress, StudyStats, Essay, EssayScore, StudyPlan, LearningSession, User, AuthResponse, RegisterRequest, LoginRequest, ResetPasswordRequest, SetNewPasswordRequest } from '@/types'
import { getRandomWords, searchWords as localSearchWords, QUIZ_QUESTIONS, WORDS_DATABASE } from '@/utils/mockData'
import { DEFAULT_STUDY_PLAN, LOCAL_STORAGE_KEYS } from '@/utils/constants'

// API 配置
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
const USE_MOCK_API = import.meta.env.VITE_USE_MOCK === 'true'

type WordApiResponse = {
  id: string | number
  word: string
  kana: string
  japaneseMeaning?: string
  japanese_meaning?: string
  chineseMeaning?: string
  chinese_meaning?: string
  meaning?: string
  example: string
  partOfSpeech?: string
  part_of_speech?: string
  audioUrl?: string
  audio_url?: string
  tags?: string[]
}

function normalizeWord(word: WordApiResponse): Word {
  const japaneseMeaning = word.japaneseMeaning ?? word.japanese_meaning ?? word.meaning ?? ''
  const chineseMeaning = word.chineseMeaning ?? word.chinese_meaning ?? ''

  return {
    id: String(word.id),
    word: word.word,
    kana: word.kana,
    japaneseMeaning,
    chineseMeaning,
    example: word.example,
    partOfSpeech: word.partOfSpeech ?? word.part_of_speech,
    audioUrl: word.audioUrl ?? word.audio_url,
    tags: word.tags ?? []
  }
}

type StudyPlanApiResponse = {
  id: string | number
  name: string
  dailyGoal?: number
  daily_goal?: number
  reviewRatio?: number
  review_ratio?: number
  dictionaryId?: string
  dictionary_id?: string
  createdAt?: number
  created_at?: string
  updatedAt?: number
  updated_at?: string
  isActive?: boolean
  is_active?: boolean
}

type LearningSessionApiResponse = {
  id: string | number
  planId?: string | number
  plan_id?: string | number
  date: string
  learnedWords?: string[]
  learned_words?: string[]
  reviewedWords?: string[]
  reviewed_words?: string[]
  sessionStats?: {
    knownCount?: number
    fuzzyCount?: number
    unknownCount?: number
  }
  known_count?: number
  fuzzy_count?: number
  unknown_count?: number
  completedAt?: number | null
  completed_at?: string | null
}

function parseTimestamp(value?: number | string | null): number {
  if (typeof value === 'number') return value
  if (typeof value === 'string') {
    const ms = Date.parse(value)
    return Number.isNaN(ms) ? 0 : ms
  }
  return 0
}

function normalizeStudyPlan(plan: StudyPlanApiResponse): StudyPlan {
  return {
    id: String(plan.id),
    name: plan.name,
    dailyGoal: plan.dailyGoal ?? plan.daily_goal ?? 10,
    reviewRatio: plan.reviewRatio ?? plan.review_ratio ?? 0.5,
    dictionaryId: plan.dictionaryId ?? plan.dictionary_id ?? 'common',
    createdAt: plan.createdAt ?? parseTimestamp(plan.created_at),
    updatedAt: plan.updatedAt ?? parseTimestamp(plan.updated_at),
    isActive: plan.isActive ?? plan.is_active ?? false
  }
}

function normalizeLearningSession(session: LearningSessionApiResponse): LearningSession {
  const normalizedSessionStats = session.sessionStats
    ? {
        knownCount: session.sessionStats.knownCount ?? 0,
        fuzzyCount: session.sessionStats.fuzzyCount ?? 0,
        unknownCount: session.sessionStats.unknownCount ?? 0
      }
    : {
        knownCount: session.known_count ?? 0,
        fuzzyCount: session.fuzzy_count ?? 0,
        unknownCount: session.unknown_count ?? 0
      }

  return {
    id: String(session.id),
    planId: String(session.planId ?? session.plan_id ?? ''),
    date: session.date,
    learnedWords: session.learnedWords ?? session.learned_words ?? [],
    reviewedWords: session.reviewedWords ?? session.reviewed_words ?? [],
    sessionStats: normalizedSessionStats,
    completedAt: session.completedAt ?? parseTimestamp(session.completed_at)
  }
}

function getAuthHeaders(): Record<string, string> {
  const token = getAuthToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function assertApiResponse(response: Response, action: string): void {
  if (response.status === 401) {
    logout()
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('open-login-dialog'))
    }
    throw new Error('登录状态已失效，请重新登录')
  }
  if (!response.ok) {
    throw new Error(`${action}失败: ${response.statusText}`)
  }
}

/**
 * 搜索单词
 * GET /api/words/search?q=keyword&page=1&limit=10
 */
export async function searchWords(
  keyword: string,
  page: number = 1,
  limit: number = 10
): Promise<{ words: SearchResult[]; total: number; page: number; limit: number }> {
  const safePage = Math.max(1, page)
  const safeLimit = Math.min(100, Math.max(1, limit))

  if (USE_MOCK_API) {
    const allWords = localSearchWords(keyword)
    const start = (safePage - 1) * safeLimit
    return {
      words: allWords.slice(start, start + safeLimit),
      total: allWords.length,
      page: safePage,
      limit: safeLimit
    }
  }
  
  const response = await fetch(
    `${API_BASE_URL}/words/search?q=${encodeURIComponent(keyword)}&page=${safePage}&limit=${safeLimit}`,
    {
    headers: getAuthHeaders()
    }
  )
  assertApiResponse(response, '搜索')
  const payload = await response.json() as
    | { words?: WordApiResponse[]; total?: number; page?: number; limit?: number }
    | WordApiResponse[]

  if (Array.isArray(payload)) {
    return {
      words: payload.map(normalizeWord),
      total: payload.length,
      page: safePage,
      limit: safeLimit
    }
  }

  return {
    words: (payload.words ?? []).map(normalizeWord),
    total: payload.total ?? 0,
    page: payload.page ?? safePage,
    limit: payload.limit ?? safeLimit
  }
}

/**
 * 获取单词详情
 * GET /api/words/:id
 */
export async function getWord(id: string): Promise<Word> {
  if (USE_MOCK_API) {
    // 从 mockData 中查找单词
    const word = WORDS_DATABASE.find((w: Word) => w.id === id)
    if (!word) throw new Error(`单词不存在: ${id}`)
    return word
  }
  
  const response = await fetch(`${API_BASE_URL}/words/${id}`, {
    headers: getAuthHeaders()
  })
  if (!response.ok) throw new Error(`获取单词失败: ${response.statusText}`)
  const data: WordApiResponse = await response.json()
  return normalizeWord(data)
}

/**
 * 获取随机单词（用于背单词）
 * GET /api/words/random?count=5
 */
export async function getRandomWordsAPI(count: number = 5): Promise<Word[]> {
  if (USE_MOCK_API) {
    return getRandomWords(count)
  }
  
  const response = await fetch(`${API_BASE_URL}/words/random?count=${count}`, {
    headers: getAuthHeaders()
  })
  if (!response.ok) throw new Error(`获取随机单词失败: ${response.statusText}`)
  const data: WordApiResponse[] = await response.json()
  return data.map(normalizeWord)
}

/**
 * 获取所有单词列表
 * GET /api/words?page=1&limit=20
 */
export async function getAllWords(page: number = 1, limit: number = 20): Promise<{ words: Word[], total: number }> {
  if (USE_MOCK_API) {
    const start = (page - 1) * limit
    return {
      words: WORDS_DATABASE.slice(start, start + limit),
      total: WORDS_DATABASE.length
    }
  }
  
  const response = await fetch(`${API_BASE_URL}/words?page=${page}&limit=${limit}`, {
    headers: getAuthHeaders()
  })
  if (!response.ok) throw new Error(`获取单词列表失败: ${response.statusText}`)
  const data: { words: WordApiResponse[]; total: number } = await response.json()
  return {
    words: data.words.map(normalizeWord),
    total: data.total
  }
}

/**
 * 获取测试题目
 * GET /api/quiz/questions?difficulty=medium&count=10
 */
export async function getQuizQuestions(difficulty: string = 'medium', count: number = 10): Promise<QuizQuestion[]> {
  if (USE_MOCK_API) {
    // 从 mockData 返回固定的测试题目
    return QUIZ_QUESTIONS.slice(0, count)
  }
  
  const response = await fetch(`${API_BASE_URL}/quiz/questions?difficulty=${difficulty}&count=${count}`)
  if (!response.ok) throw new Error(`获取测试题目失败: ${response.statusText}`)
  return response.json()
}

/**
 * 提交测试答案
 * POST /api/quiz/submit
 */
export async function submitQuizAnswer(
  questionId: string,
  userAnswer: string,
  isCorrect: boolean
): Promise<{ success: boolean; score: number }> {
  if (USE_MOCK_API) {
    // Mock 模式直接返回无修改
    return { success: true, score: isCorrect ? 1 : 0 }
  }
  
  const response = await fetch(`${API_BASE_URL}/quiz/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ questionId, userAnswer, isCorrect })
  })
  if (!response.ok) throw new Error(`提交答案失败: ${response.statusText}`)
  return response.json()
}

/**
 * 更新单词学习进度
 * POST /api/user/progress/:wordId
 */
export async function updateWordProgress(
  wordId: string,
  status: string,
  isCorrect: boolean = true
): Promise<WordProgress> {
  if (USE_MOCK_API) {
    // Mock 模式返回更新后的进度
    const statusValues: Array<'unknown' | 'fuzzy' | 'known'> = ['unknown', 'fuzzy', 'known']
    const validStatus = status as 'unknown' | 'fuzzy' | 'known'
    const statusIndex = statusValues.indexOf(validStatus)
    const nextStatusIndex = (statusIndex + (isCorrect ? 1 : 0)) % statusValues.length
    const nextStatus: 'unknown' | 'fuzzy' | 'known' = statusValues[nextStatusIndex] || 'unknown'
    
    return {
      wordId,
      status: nextStatus,
      reviewCount: 1,
      correctCount: isCorrect ? 1 : 0,
      lastReviewedAt: Date.now()
    }
  }
  
  const response = await fetch(`${API_BASE_URL}/user/progress/${wordId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, isCorrect })
  })
  if (!response.ok) throw new Error(`更新学习进度失败: ${response.statusText}`)
  return response.json()
}

/**
 * 获取学习统计
 * GET /api/user/stats
 */
export async function getStudyStats(): Promise<StudyStats> {
  if (USE_MOCK_API) {
    // Mock 模式返回默认统计数据
    return {
      totalWordsLearned: 10,
      totalWordsRecited: 10,
      todayLearned: 2,
      todayRecited: 3,
      currentStreak: 5,
      longestStreak: 5,
      lastStudyDate: Date.now()
    }
  }
  
  const response = await fetch(`${API_BASE_URL}/user/stats`, {
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '获取学习统计')
  return response.json()
}

/**
 * 获取搜索历史
 * GET /api/user/search-history
 */
export async function getSearchHistory(
  limit: number = 10
): Promise<Array<{ id: number; keyword: string; resultCount: number; createdAt: number }>> {
  if (USE_MOCK_API) {
    // Mock 模式直接返回空（由 localStorage 驱动）
    return []
  }
  
  const response = await fetch(`${API_BASE_URL}/user/search-history?limit=${limit}`, {
    headers: getAuthHeaders()
  })
  if (!response.ok) throw new Error(`获取搜索历史失败: ${response.statusText}`)
  return response.json()
}

/**
 * 添加到收藏夹
 * POST /api/user/favorites/:wordId
 */
export async function addToFavorites(wordId: string): Promise<{ success: boolean }> {
  if (USE_MOCK_API) {
    return { success: true }
  }
  
  const response = await fetch(`${API_BASE_URL}/user/favorites/${wordId}`, {
    method: 'POST',
    headers: getAuthHeaders()
  })
  if (!response.ok) throw new Error(`添加收藏失败: ${response.statusText}`)
  return response.json()
}

/**
 * 从收藏夹移除
 * DELETE /api/user/favorites/:wordId
 */
export async function removeFromFavorites(wordId: string): Promise<{ success: boolean }> {
  if (USE_MOCK_API) {
    return { success: true }
  }
  
  const response = await fetch(`${API_BASE_URL}/user/favorites/${wordId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  })
  if (!response.ok) throw new Error(`移除收藏失败: ${response.statusText}`)
  return response.json()
}

/**
 * 获取收藏夹列表
 * GET /api/user/favorites?page=1&limit=20
 */
export async function getFavorites(page: number = 1, limit: number = 20): Promise<{ words: Word[], total: number, page: number, limit: number }> {
  if (USE_MOCK_API) {
    return { words: [], total: 0, page, limit }
  }
  
  const response = await fetch(`${API_BASE_URL}/user/favorites?page=${page}&limit=${limit}`, {
    headers: getAuthHeaders()
  })
  if (!response.ok) throw new Error(`获取收藏列表失败: ${response.statusText}`)
  const data: { words: WordApiResponse[], total: number, page: number, limit: number } = await response.json()
  return {
    words: data.words.map(normalizeWord),
    total: data.total,
    page: data.page,
    limit: data.limit
  }
}

/**
 * 获取学习进度
 * GET /api/user/progress
 */
export async function getUserProgress(): Promise<WordProgress[]> {
  if (USE_MOCK_API) {
    return []
  }
  
  const response = await fetch(`${API_BASE_URL}/user/progress`, {
    headers: getAuthHeaders()
  })
  if (!response.ok) throw new Error(`获取学习进度失败: ${response.statusText}`)
  return response.json()
}

/**
 * 提交作文
 * POST /api/essays/submit
 */
export async function submitEssayAPI(essayData: {
  title: string
  topic: string
  content: string
  wordCount: number
}): Promise<Essay> {
  if (USE_MOCK_API) {
    // 模拟本地作文创建
    const essay: Essay = {
      id: `essay_${Date.now()}`,
      title: essayData.title,
      content: essayData.content,
      topic: essayData.topic,
      wordCount: essayData.wordCount,
      submitTime: Date.now()
    }
    return essay
  }
  
  const response = await fetch(`${API_BASE_URL}/essays/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(essayData)
  })
  if (!response.ok) throw new Error(`提交作文失败: ${response.statusText}`)
  return response.json()
}

/**
 * 获取作文历史
 * GET /api/essays/history
 */
export async function getEssayHistoryAPI(limit: number = 20): Promise<Essay[]> {
  if (USE_MOCK_API) {
    // 从 localStorage 获取本地存储的作文
    const stored = localStorage.getItem('yomii_essays')
    return stored ? JSON.parse(stored) : []
  }
  
  const response = await fetch(`${API_BASE_URL}/essays/history?limit=${limit}`)
  if (!response.ok) throw new Error(`获取作文历史失败: ${response.statusText}`)
  return response.json()
}

/**
 * 获取作文评分（AI 评测）
 * GET /api/essays/:essayId/score
 */
export async function getEssayScore(essayId: string): Promise<EssayScore> {
  if (USE_MOCK_API) {
    return generateMockEssayScore(essayId)
  }
  
  const response = await fetch(`${API_BASE_URL}/essays/${essayId}/score`)
  if (!response.ok) throw new Error(`获取作文评分失败: ${response.statusText}`)
  return response.json()
}

/**
 * 生成模拟作文评分（用于 Mock 模式和测试）
 * 预留 AI 评分接口，未来直接调用真实 AI 服务
 */
export function generateMockEssayScore(essayId: string): EssayScore {
  // 生成随机评分（实际应用中由 AI 模型生成）
  const randomScore = (base: number = 70, range: number = 25): number => {
    return Math.min(100, Math.max(0, base + Math.random() * range - range / 2))
  }
  
  const scores = {
    gramarScore: Math.round(randomScore(75)),
    vocabularyScore: Math.round(randomScore(72)),
    fluencyScore: Math.round(randomScore(70)),
    coherenceScore: Math.round(randomScore(68))
  }
  
  const overallScore = Math.round(
    (scores.gramarScore + scores.vocabularyScore + scores.fluencyScore + scores.coherenceScore) / 4
  )

  const commentsArray = [
    '语法结构清晰，词汇运用恰当，整体流畅自然。建议多加练习复杂句式。',
    '表达简洁有力，逻辑层次分明，词汇选择得体。可以尝试使用更多的从句来丰富表达。',
    '文章结构完整，思路清晰，语言简洁。建议增加更多具体例子来支撑观点。',
    '表达流畅自然，用词准确恰当，句式多样。整体质量较好，继续保持！',
    '逻辑严密，论证有力，文笔优美。是一篇不错的作文，值得称赞。'
  ]

  return {
    id: `score_${Date.now()}`,
    essayId,
    overallScore,
    gramarScore: scores.gramarScore,
    vocabularyScore: scores.vocabularyScore,
    fluencyScore: scores.fluencyScore,
    coherenceScore: scores.coherenceScore,
    comments: commentsArray[Math.floor(Math.random() * commentsArray.length)]!,
    aiEvaluated: false,  // Mock 评分，非 AI 评分
    evaluationTime: Date.now()
  }
}

/**
 * 获取学习计划列表
 * GET /api/study-plans
 */
export async function getStudyPlans(): Promise<StudyPlan[]> {
  if (USE_MOCK_API) {
    return [DEFAULT_STUDY_PLAN]
  }
  
  const response = await fetch(`${API_BASE_URL}/study-plans`, {
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '获取学习计划')
  const data: StudyPlanApiResponse[] = await response.json()
  return data.map(normalizeStudyPlan)
}

/**
 * 获取当前活跃的学习计划
 * GET /api/study-plans/current
 */
export async function getCurrentStudyPlan(): Promise<StudyPlan> {
  if (USE_MOCK_API) {
    return DEFAULT_STUDY_PLAN
  }
  
  const response = await fetch(`${API_BASE_URL}/study-plans/current`, {
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '获取当前学习计划')
  const data: StudyPlanApiResponse = await response.json()
  return normalizeStudyPlan(data)
}

/**
 * 创建新的学习计划
 * POST /api/study-plans
 */
export async function createStudyPlan(plan: {
  name: string
  dailyGoal: number
  reviewRatio: number
  dictionaryId?: string
}): Promise<StudyPlan> {
  if (USE_MOCK_API) {
    return {
      ...plan,
      id: `plan_${Date.now()}`,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      isActive: true
    }
  }
  
  const response = await fetch(`${API_BASE_URL}/study-plans`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify({
      name: plan.name,
      daily_goal: plan.dailyGoal,
      review_ratio: plan.reviewRatio,
      dictionary_id: plan.dictionaryId ?? 'common'
    })
  })
  assertApiResponse(response, '创建学习计划')
  const data: StudyPlanApiResponse = await response.json()
  return normalizeStudyPlan(data)
}

/**
 * 更新学习计划
 * PUT /api/study-plans/:planId
 */
export async function updateStudyPlan(planId: string, updates: Partial<StudyPlan>): Promise<StudyPlan> {
  if (USE_MOCK_API) {
    return {
      ...DEFAULT_STUDY_PLAN,
      ...updates,
      id: planId,
      updatedAt: Date.now()
    }
  }
  
  const response = await fetch(`${API_BASE_URL}/study-plans/${planId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify({
      name: updates.name,
      daily_goal: updates.dailyGoal,
      review_ratio: updates.reviewRatio,
      dictionary_id: updates.dictionaryId,
      is_active: updates.isActive
    })
  })
  assertApiResponse(response, '更新学习计划')
  const data: StudyPlanApiResponse = await response.json()
  return normalizeStudyPlan(data)
}

/**
 * 激活学习计划
 * POST /api/study-plans/:planId/activate
 */
export async function activateStudyPlan(planId: string): Promise<StudyPlan> {
  if (USE_MOCK_API) {
    return { ...DEFAULT_STUDY_PLAN, id: planId, isActive: true }
  }
  
  const response = await fetch(`${API_BASE_URL}/study-plans/${planId}/activate`, {
    method: 'POST',
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '激活学习计划')
  const data: StudyPlanApiResponse = await response.json()
  return normalizeStudyPlan(data)
}

/**
 * 获取待背诵的单词列表
 * GET /api/study-plans/:planId/learn-words?date=YYYY-MM-DD
 */
export async function getLearnWords(planId: string, date?: string): Promise<Word[]> {
  const targetDate = date || new Date().toISOString().split('T')[0]
  
  if (USE_MOCK_API) {
    // 返回随机单词作为待背诵列表
    return getRandomWords(10)
  }
  
  const response = await fetch(`${API_BASE_URL}/study-plans/${planId}/learn-words?date=${targetDate}`, {
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '获取待背诵单词')
  const data: WordApiResponse[] = await response.json()
  return data.map(normalizeWord)
}

/**
 * 获取复习单词列表
 * GET /api/study-plans/:planId/review-words?date=YYYY-MM-DD
 */
export async function getReviewWords(planId: string, date?: string): Promise<Word[]> {
  const targetDate = date || new Date().toISOString().split('T')[0]
  
  if (USE_MOCK_API) {
    // 返回随机单词作为复习列表
    return getRandomWords(5)
  }
  
  const response = await fetch(`${API_BASE_URL}/study-plans/${planId}/review-words?date=${targetDate}`, {
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '获取复习单词')
  const data: WordApiResponse[] = await response.json()
  return data.map(normalizeWord)
}

/**
 * 保存学习轮次
 * POST /api/study-plans/:planId/sessions
 */
export async function saveLearningSession(planId: string, session: Omit<LearningSession, 'id'>): Promise<LearningSession> {
  if (USE_MOCK_API) {
    return {
      ...session,
      id: `session_${Date.now()}`
    }
  }
  
  const response = await fetch(`${API_BASE_URL}/study-plans/${planId}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify({
      date: session.date,
      learned_words: session.learnedWords,
      reviewed_words: session.reviewedWords,
      known_count: session.sessionStats.knownCount,
      fuzzy_count: session.sessionStats.fuzzyCount,
      unknown_count: session.sessionStats.unknownCount
    })
  })
  assertApiResponse(response, '保存学习轮次')
  const data: LearningSessionApiResponse = await response.json()
  return normalizeLearningSession(data)
}

/**
 * 获取学习轮次列表
 * GET /api/study-plans/:planId/sessions
 */
export async function getLearningSessions(planId: string): Promise<LearningSession[]> {
  if (USE_MOCK_API) {
    return []
  }
  
  const response = await fetch(`${API_BASE_URL}/study-plans/${planId}/sessions`, {
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '获取学习轮次')
  const data: LearningSessionApiResponse[] = await response.json()
  return data.map(normalizeLearningSession)
}

/**
 * 请求加量学习（增加当天的学习量）
 * POST /api/study-plans/:planId/add-more
 */
export async function requestAddMore(
  planId: string,
  additionalCount: number,
  excludeWordIds: number[] = []
): Promise<{ success: boolean; moreWords: Word[] }> {
  if (USE_MOCK_API) {
    return {
      success: true,
      moreWords: getRandomWords(additionalCount)
    }
  }
  
  const query = new URLSearchParams({ additional_count: String(additionalCount) })
  for (const id of excludeWordIds) {
    query.append('exclude_word_ids', String(id))
  }

  const response = await fetch(`${API_BASE_URL}/study-plans/${planId}/add-more?${query.toString()}`, {
    method: 'POST',
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '加量学习')
  const data: { success: boolean; moreWords: WordApiResponse[] } = await response.json()
  return {
    success: data.success,
    moreWords: (data.moreWords || []).map(normalizeWord)
  }
}

/**
 * 用户注册
 * POST /api/auth/register
 */
export async function register(data: RegisterRequest): Promise<AuthResponse> {
  if (USE_MOCK_API) {
    // Mock 模式：验证输入
    if (!data.phone || !data.password) {
      return { success: false, message: '电话和密码不能为空', error: '验证失败' }
    }
    if (data.password.length < 8) {
      return { success: false, message: '密码至少8位', error: '密码过短' }
    }
    // 模拟成功注册
    const mockToken = `token_${Date.now()}`
    const mockUser: User = {
      id: `user_${Date.now()}`,
      username: data.username || '新用户',
      phone: data.phone,
      createdAt: Date.now(),
      lastLoginAt: Date.now()
    }
    localStorage.setItem('yomii_auth_token', mockToken)
    localStorage.setItem('yomii_user', JSON.stringify(mockUser))
    return { success: true, message: '注册成功', token: mockToken, user: mockUser }
  }
  
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  const result: AuthResponse = await response.json()
  if (response.ok && result.token) {
    localStorage.setItem('yomii_auth_token', result.token)
    if (result.user) {
      localStorage.setItem('yomii_user', JSON.stringify(result.user))
    }
  }
  return result
}

/**
 * 用户登录
 * POST /api/auth/login
 */
export async function login(data: LoginRequest): Promise<AuthResponse> {
  if (USE_MOCK_API) {
    // Mock 模式：验证输入
    if (!data.phone || !data.password) {
      return { success: false, message: '电话和密码不能为空', error: '验证失败' }
    }
    // 模拟成功登录
    const mockToken = `token_${Date.now()}`
    const mockUser: User = {
      id: `user_${Date.now()}`,
      username: data.phone.slice(-4),
      phone: data.phone,
      createdAt: Date.now(),
      lastLoginAt: Date.now()
    }
    localStorage.setItem('yomii_auth_token', mockToken)
    localStorage.setItem('yomii_user', JSON.stringify(mockUser))
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('yomii:login'))
    }
    return { success: true, message: '登录成功', token: mockToken, user: mockUser }
  }
  
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  const result: AuthResponse = await response.json()
  if (response.ok && result.token) {
    localStorage.setItem('yomii_auth_token', result.token)
    if (result.user) {
      localStorage.setItem('yomii_user', JSON.stringify(result.user))
    }
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('yomii:login'))
    }
  }
  return result
}

/**
 * 用户登出
 */
export function logout(): void {
  localStorage.removeItem('yomii_auth_token')
  localStorage.removeItem('yomii_user')
  localStorage.removeItem(LOCAL_STORAGE_KEYS.SEARCH_HISTORY)
  localStorage.removeItem(LOCAL_STORAGE_KEYS.WORD_PROGRESS)
  localStorage.removeItem(LOCAL_STORAGE_KEYS.STUDY_STATS)
  localStorage.removeItem(LOCAL_STORAGE_KEYS.FAVORITES)
  // 兼容旧版本可能使用的键名
  localStorage.removeItem('searchHistory')

  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('yomii:logout'))
  }
}

/**
 * 获取当前用户信息
 */
export function getCurrentUser(): User | null {
  const userStr = localStorage.getItem('yomii_user')
  if (!userStr) return null
  try {
    return JSON.parse(userStr) as User
  } catch {
    return null
  }
}

/**
 * 获取认证令牌
 */
export function getAuthToken(): string | null {
  return localStorage.getItem('yomii_auth_token')
}

/**
 * 检查是否已登录
 */
export function isAuthenticated(): boolean {
  return !!getAuthToken() && !!getCurrentUser()
}

/**
 * 请求重置密码
 * POST /api/auth/request-reset
 */
export async function requestPasswordReset(data: ResetPasswordRequest): Promise<AuthResponse> {
  if (USE_MOCK_API) {
    if (!data.phone) {
      return { success: false, message: '电话不能为空', error: '验证失败' }
    }
    // 模拟成功请求
    return { success: true, message: '重置码已发送到短信' }
  }
  
  const response = await fetch(`${API_BASE_URL}/auth/request-reset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  return response.json()
}

/**
 * 重置密码（使用重置码）
 * POST /api/auth/reset-password
 */
export async function resetPassword(data: SetNewPasswordRequest): Promise<AuthResponse> {
  if (USE_MOCK_API) {
    if (!data.newPassword || data.newPassword.length < 8) {
      return { success: false, message: '密码至少8位', error: '密码过短' }
    }
    // 模拟成功重置
    return { success: true, message: '密码重置成功，请重新登录' }
  }
  
  const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  return response.json()
}

export default {
  // 认证相关
  register,
  login,
  logout,
  getCurrentUser,
  getAuthToken,
  isAuthenticated,
  requestPasswordReset,
  resetPassword,
  // 单词相关
  searchWords,
  getWord,
  getRandomWordsAPI,
  getAllWords,
  getQuizQuestions,
  submitQuizAnswer,
  updateWordProgress,
  getStudyStats,
  getSearchHistory,
  addToFavorites,
  removeFromFavorites,
  getFavorites,
  getUserProgress,
  submitEssayAPI,
  getEssayHistoryAPI,
  getEssayScore,
  generateMockEssayScore,
  // 学习计划相关
  getStudyPlans,
  getCurrentStudyPlan,
  createStudyPlan,
  updateStudyPlan,
  activateStudyPlan,
  getLearnWords,
  getReviewWords,
  saveLearningSession,
  getLearningSessions,
  requestAddMore
}
