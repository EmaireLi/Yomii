/**
 * API 客户端
 * 
 * 所有数据通过 API 接口获取和提交
 * 支持 Mock 模式和真实后端两种模型
 */

import type {
  Word,
  SearchResult,
  QuizQuestion,
  QuizDifficultyOption,
  QuizAbilityReport,
  QuizSessionRecord,
  DictionaryConfig,
  WordProgress,
  StudyStats,
  Essay,
  EssayScore,
  EssayRevision,
  EssayEvaluationReport,
  StudyPlan,
  LearningSession,
  User,
  AuthResponse,
  RegisterRequest,
  LoginRequest,
  ResetPasswordRequest,
  SetNewPasswordRequest,
  ReviewRating,
  ReviewWordItem,
  ReviewWordList
} from '@/types'
import { getRandomWords, searchWords as localSearchWords, WORDS_DATABASE } from '@/utils/mockData'
import { DEFAULT_STUDY_PLAN, LOCAL_STORAGE_KEYS, DICTIONARIES } from '@/utils/constants'

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

type WordProgressApiResponse = {
  wordId?: string | number
  word_id?: string | number
  status?: 'unknown' | 'fuzzy' | 'known'
  interval?: number
  ease?: number
  reviewCount?: number
  review_count?: number
  lapseCount?: number
  lapse_count?: number
  correctCount?: number
  correct_count?: number
  nextReview?: number
  next_review?: string
  lastReview?: number
  last_review?: string
  lastReviewedAt?: number
  last_reviewed_at?: string
  createdAt?: number
  created_at?: string
}

type ReviewWordItemApiResponse = {
  word: WordApiResponse
  progress: WordProgressApiResponse
}

type ReviewWordListApiResponse = {
  items?: ReviewWordItemApiResponse[]
  count?: number
  limit?: number
  timestamp?: number
}

function parseTimestamp(value?: number | string | null): number {
  if (typeof value === 'number') return value
  if (typeof value === 'string') {
    const numericValue = Number(value)
    if (Number.isFinite(numericValue)) return numericValue
    const ms = Date.parse(value)
    return Number.isNaN(ms) ? 0 : ms
  }
  return 0
}

function normalizeWordProgress(progress: WordProgressApiResponse): WordProgress {
  const lastReview = parseTimestamp(progress.lastReview ?? progress.last_review)
  const lastReviewedAt = parseTimestamp(progress.lastReviewedAt ?? progress.last_reviewed_at)

  return {
    wordId: String(progress.wordId ?? progress.word_id ?? ''),
    status: progress.status ?? 'unknown',
    reviewCount: Number(progress.reviewCount ?? progress.review_count ?? 0),
    correctCount: Number(progress.correctCount ?? progress.correct_count ?? 0),
    lastReviewedAt: lastReviewedAt || lastReview || Date.now(),
    interval: typeof progress.interval === 'number' ? progress.interval : undefined,
    ease: typeof progress.ease === 'number' ? progress.ease : undefined,
    lapseCount: Number(progress.lapseCount ?? progress.lapse_count ?? 0),
    nextReview: parseTimestamp(progress.nextReview ?? progress.next_review),
    lastReview: lastReview || lastReviewedAt || Date.now(),
    createdAt: parseTimestamp(progress.createdAt ?? progress.created_at)
  }
}

function normalizeReviewWordList(payload: ReviewWordListApiResponse): ReviewWordList {
  const items: ReviewWordItem[] = (payload.items ?? []).map(item => ({
    word: normalizeWord(item.word),
    progress: normalizeWordProgress(item.progress ?? {})
  }))
  return {
    items,
    count: payload.count ?? items.length,
    limit: payload.limit ?? items.length,
    timestamp: payload.timestamp
  }
}

function toReviewRating(status: string, isCorrect: boolean = true): ReviewRating {
  if (status === 'known' && isCorrect) return 'good'
  if (status === 'fuzzy') return 'hard'
  return 'again'
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

const QUIZ_HISTORY_STORAGE_KEY = LOCAL_STORAGE_KEYS.QUIZ_HISTORY

function getStoredQuizHistory(): QuizSessionRecord[] {
  if (typeof window === 'undefined') return []
  const raw = localStorage.getItem(QUIZ_HISTORY_STORAGE_KEY)
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw) as QuizSessionRecord[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function setStoredQuizHistory(records: QuizSessionRecord[]): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(QUIZ_HISTORY_STORAGE_KEY, JSON.stringify(records))
}

function generateQuizAbilityReport(records: QuizSessionRecord[]): QuizAbilityReport {
  if (records.length === 0) {
    return {
      overallScore: 0,
      level: '暂无评级',
      trend: { direction: 'stable', delta: 0 },
      consistencyScore: 0,
      speedScore: 0,
      historyCount: 0,
      basedOnSessions: 0,
      recommendations: ['完成至少 1 次测试后即可生成能力报告。'],
      summary: '暂无历史测试记录，无法评估能力趋势。',
      generatedAt: 0,
      currentSession: null,
      difficultyBreakdown: []
    }
  }

  const sorted = [...records].sort((a, b) => a.completedAt - b.completedAt)
  const accuracySeries = sorted.map(item => item.accuracy)
  const speedSeries = sorted
    .filter(item => item.totalQuestions > 0 && item.durationSeconds > 0)
    .map(item => item.durationSeconds / item.totalQuestions)

  let weightedAccuracy = 0
  let totalWeight = 0
  accuracySeries.forEach((value, idx) => {
    const weight = Math.exp((idx - (accuracySeries.length - 1)) / 4)
    weightedAccuracy += value * weight
    totalWeight += weight
  })
  weightedAccuracy = totalWeight > 0 ? weightedAccuracy / totalWeight : 0

  const recent = accuracySeries.slice(-3)
  const previous = accuracySeries.slice(-6, -3)
  const recentAvg = recent.length > 0 ? recent.reduce((sum, item) => sum + item, 0) / recent.length : 0
  const previousAvg = previous.length > 0
    ? previous.reduce((sum, item) => sum + item, 0) / previous.length
    : (accuracySeries[0] ?? 0)
  const trendDelta = Number((recentAvg - previousAvg).toFixed(1))

  const meanAccuracy = accuracySeries.reduce((sum, item) => sum + item, 0) / accuracySeries.length
  const variance = accuracySeries.reduce((sum, item) => sum + (item - meanAccuracy) ** 2, 0) / accuracySeries.length
  const consistencyScore = Math.max(0, Math.min(100, Number((100 - Math.sqrt(variance) * 2.2).toFixed(1))))

  const avgSecondsPerQuestion = speedSeries.length > 0
    ? speedSeries.reduce((sum, item) => sum + item, 0) / speedSeries.length
    : 60
  const speedScore = Math.max(40, Math.min(100, Number((100 * (45 / avgSecondsPerQuestion)).toFixed(1))))

  const overallScore = Number((weightedAccuracy * 0.72 + consistencyScore * 0.18 + speedScore * 0.1).toFixed(1))
  const level = overallScore >= 90
    ? 'JLPT N2+'
    : overallScore >= 80
      ? 'JLPT N3'
      : overallScore >= 70
        ? 'JLPT N4'
        : overallScore >= 60
          ? 'JLPT N5'
          : '入门阶段'

  const breakdownMap = new Map<string, { total: number; count: number }>()
  sorted.forEach(item => {
    const current = breakdownMap.get(item.difficulty) || { total: 0, count: 0 }
    current.total += item.accuracy
    current.count += 1
    breakdownMap.set(item.difficulty, current)
  })
  const difficultyBreakdown = Array.from(breakdownMap.entries())
    .map(([difficulty, value]) => ({
      difficulty,
      accuracy: Number((value.total / value.count).toFixed(1)),
      count: value.count
    }))
    .sort((a, b) => a.accuracy - b.accuracy)

  const direction = trendDelta >= 3 ? 'up' : trendDelta <= -3 ? 'down' : 'stable'
  const trendText = direction === 'up' ? '近期表现明显提升' : direction === 'down' ? '近期表现出现回落' : '近期表现整体稳定'
  const recommendations = [
    direction === 'down'
      ? '近期准确率回落，建议先复习错题词汇，再进行同难度复测。'
      : direction === 'up'
        ? '能力在提升，下一次测试可尝试更高难度以扩大能力边界。'
        : '能力表现稳定，建议固定每周 2-3 次测试保持节奏。'
  ]
  if (difficultyBreakdown[0]) {
    recommendations.push(`当前薄弱难度为 ${difficultyBreakdown[0].difficulty}（平均正确率 ${difficultyBreakdown[0].accuracy}%），可优先加强该层级训练。`)
  }

  const currentSession = sorted[sorted.length - 1] || null
  return {
    overallScore,
    level,
    trend: { direction, delta: trendDelta },
    consistencyScore,
    speedScore,
    historyCount: sorted.length,
    basedOnSessions: sorted.length,
    recommendations,
    summary: `综合能力分 ${overallScore}，${trendText}。建议持续按周进行测试并针对薄弱项复习。`,
    generatedAt: currentSession?.completedAt || Date.now(),
    currentSession,
    difficultyBreakdown
  }
}

function normalizeQuizSession(record: any): QuizSessionRecord {
  const completedAt = parseTimestamp(
    record.completedAt ?? record.completed_at ?? record.createdAt ?? record.created_at
  )

  return {
    id: record.id,
    difficulty: record.difficulty || 'medium',
    totalQuestions: Number(record.totalQuestions ?? record.total_questions ?? 0),
    correctAnswers: Number(record.correctAnswers ?? record.correct_answers ?? 0),
    accuracy: Number(record.accuracy ?? 0),
    durationSeconds: Number(record.durationSeconds ?? record.duration_seconds ?? 0),
    abilityScore: Number(record.abilityScore ?? record.ability_score ?? 0),
    level: String(record.level ?? record.reportLevel ?? record.report_level ?? '暂无评级'),
    summary: String(record.summary ?? record.reportSummary ?? record.report_summary ?? ''),
    trendDelta: Number(record.trendDelta ?? record.trend_delta ?? 0),
    consistencyScore: Number(record.consistencyScore ?? record.consistency_score ?? 0),
    speedScore: Number(record.speedScore ?? record.speed_score ?? 0),
    recommendations: Array.isArray(record.recommendations) ? record.recommendations.map((item: unknown) => String(item)) : [],
    difficultyBreakdown: Array.isArray(record.difficultyBreakdown ?? record.difficulty_breakdown)
      ? (record.difficultyBreakdown ?? record.difficulty_breakdown).map((item: any) => ({
          difficulty: String(item?.difficulty ?? ''),
          accuracy: Number(item?.accuracy ?? 0),
          count: Number(item?.count ?? 0)
        }))
      : [],
    completedAt: completedAt || Date.now()
  }
}

function getAuthHeaders(): Record<string, string> {
  const token = getAuthToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

let expiredTokenHandled = false

function decodeJwtPayload(token: string): { exp?: number } | null {
  const parts = token.split('.')
  if (parts.length !== 3 || !parts[1]) return null

  try {
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4)
    const json = atob(padded)
    return JSON.parse(json) as { exp?: number }
  } catch {
    return null
  }
}

function isTokenExpired(token: string): boolean {
  const payload = decodeJwtPayload(token)
  if (!payload?.exp) return false
  const nowSeconds = Math.floor(Date.now() / 1000)
  return payload.exp <= nowSeconds
}

function handleExpiredToken(): void {
  if (expiredTokenHandled) return
  expiredTokenHandled = true
  logout()
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('open-login-dialog'))
  }
}

function assertApiResponse(response: Response, action: string): void {
  if (response.status === 401) {
    handleExpiredToken()
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
  assertApiResponse(response, '获取单词')
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
  assertApiResponse(response, '获取随机单词')
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
  assertApiResponse(response, '获取单词列表')
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
  const response = await fetch(`${API_BASE_URL}/quiz/questions?difficulty=${difficulty}&count=${count}`, {
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '获取测试题目')
  return response.json()
}

/**
 * 获取测试难度配置
 * GET /api/quiz/difficulties
 */
export async function getQuizDifficulties(): Promise<QuizDifficultyOption[]> {
  const response = await fetch(`${API_BASE_URL}/quiz/difficulties`, {
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '获取测试难度配置')
  const data = await response.json() as QuizDifficultyOption[]
  return Array.isArray(data) ? data : []
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
  const response = await fetch(`${API_BASE_URL}/quiz/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify({
      question_id: Number(questionId),
      user_answer: userAnswer,
      is_correct: isCorrect
    })
  })
  assertApiResponse(response, '提交答案')
  return response.json()
}

function normalizeQuestionIdForSubmit(questionId: number | string): number {
  const numericId = Number(questionId)
  return Number.isFinite(numericId) && numericId > 0 ? numericId : 0
}

/**
 * 提交整场测试，保存历史并返回能力报告
 * POST /api/quiz/session
 */
export async function submitQuizSession(payload: {
  difficulty: string
  totalQuestions: number
  correctAnswers: number
  durationSeconds: number
  answers: Array<{ questionId: number | string; userAnswer: string; isCorrect: boolean }>
}): Promise<{ success: boolean; session: QuizSessionRecord; report: QuizAbilityReport }> {
  const response = await fetch(`${API_BASE_URL}/quiz/session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify({
      difficulty: payload.difficulty,
      total_questions: payload.totalQuestions,
      correct_answers: payload.correctAnswers,
      duration_seconds: payload.durationSeconds,
      answers: payload.answers.map(item => ({
        question_id: normalizeQuestionIdForSubmit(item.questionId),
        user_answer: item.userAnswer,
        is_correct: item.isCorrect
      }))
    })
  })
  assertApiResponse(response, '提交测试会话')
  const data = await response.json() as { success: boolean; session: any; report: QuizAbilityReport }
  return {
    success: data.success,
    session: normalizeQuizSession(data.session),
    report: data.report
  }
}

/**
 * 获取测试历史记录
 * GET /api/quiz/history
 */
export async function getQuizHistory(skip: number = 0, limit: number = 10): Promise<{ items: QuizSessionRecord[]; total: number }> {
  const response = await fetch(`${API_BASE_URL}/quiz/history?skip=${skip}&limit=${limit}`, {
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '获取测试历史')
  const data = await response.json() as { items?: any[]; total?: number }
  return {
    items: (data.items || []).map(normalizeQuizSession),
    total: data.total ?? 0
  }
}

/**
 * 删除单条测试记录
 * DELETE /api/quiz/sessions/:sessionId
 */
export async function deleteQuizSessionAPI(sessionId: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE_URL}/quiz/sessions/${sessionId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '删除测试记录')
  return response.json()
}

/**
 * 获取能力报告
 * GET /api/quiz/report
 */
export async function getQuizAbilityReport(limit: number = 20): Promise<QuizAbilityReport> {
  const response = await fetch(`${API_BASE_URL}/quiz/report?limit=${limit}`, {
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '获取能力报告')
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
  const rating = toReviewRating(status, isCorrect)

  if (USE_MOCK_API) {
    const intervalByRating: Record<ReviewRating, number> = {
      again: 0.02,
      hard: 0.05,
      good: 0.1
    }
    const statusByRating: Record<ReviewRating, 'unknown' | 'fuzzy' | 'known'> = {
      again: 'unknown',
      hard: 'fuzzy',
      good: 'known'
    }
    const interval = intervalByRating[rating]

    return {
      wordId,
      status: statusByRating[rating],
      reviewCount: 1,
      correctCount: rating === 'good' ? 1 : 0,
      lastReviewedAt: Date.now(),
      interval,
      ease: rating === 'good' ? 2.55 : rating === 'hard' ? 2.35 : 2.3,
      lapseCount: rating === 'again' ? 1 : 0,
      nextReview: Date.now() + interval * 24 * 60 * 60 * 1000,
      lastReview: Date.now(),
      createdAt: Date.now()
    }
  }
  
  const response = await fetch(`${API_BASE_URL}/review/${wordId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify({
      rating
    })
  })
  assertApiResponse(response, '更新学习进度')
  const data: { progress: WordProgressApiResponse } = await response.json()
  return normalizeWordProgress(data.progress)
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
    // Mock 模式无后端历史
    return []
  }
  
  const response = await fetch(`${API_BASE_URL}/user/search-history?limit=${limit}`, {
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '获取搜索历史')
  return response.json()
}

/**
 * 删除搜索历史
 * DELETE /api/user/search-history?keyword=xxx
 * keyword 不传则清空全部历史
 */
export async function deleteSearchHistory(
  keyword?: string
): Promise<{ success: boolean; deletedCount: number; message?: string }> {
  if (USE_MOCK_API) {
    return { success: true, deletedCount: 0 }
  }

  const query = typeof keyword === 'string' && keyword.trim()
    ? `?keyword=${encodeURIComponent(keyword.trim())}`
    : ''

  const response = await fetch(`${API_BASE_URL}/user/search-history${query}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '删除搜索历史')
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
  assertApiResponse(response, '添加收藏')
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
  assertApiResponse(response, '移除收藏')
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
  assertApiResponse(response, '获取收藏列表')
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
  assertApiResponse(response, '获取学习进度')
  const rows: WordProgressApiResponse[] = await response.json()
  return rows.map(normalizeWordProgress)
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
  targetLevel: string
}): Promise<Essay> {
  if (USE_MOCK_API) {
    const essay: Essay = {
      id: `essay_${Date.now()}`,
      title: essayData.title,
      content: essayData.content,
      topic: essayData.topic,
      wordCount: essayData.wordCount,
      targetLevel: essayData.targetLevel,
      status: 'pending',
      submitTime: Date.now(),
      evaluationRequestedAt: Date.now(),
      errorMessage: '',
      modelVersions: {
        score: 'mock-jlpt-score-v1',
        revision: 'mock-jlpt-revision-v1'
      }
    }
    return essay
  }
  
  const response = await fetch(`${API_BASE_URL}/essays/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify({
      title: essayData.title,
      topic: essayData.topic,
      content: essayData.content,
      word_count: essayData.wordCount,
      target_level: essayData.targetLevel
    })
  })
  assertApiResponse(response, '提交作文')
  const data = await response.json() as any
  return normalizeEssay(data)
}

/**
 * 获取作文历史
 * GET /api/essays/history
 */
export async function getEssayHistoryAPI(skip: number = 0, limit: number = 20): Promise<{ items: Essay[]; total: number }> {
  if (USE_MOCK_API) {
    return { items: [], total: 0 }
  }

  const response = await fetch(`${API_BASE_URL}/essays/history?skip=${skip}&limit=${limit}`, {
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '获取作文历史')
  const data = await response.json() as { items?: any[]; total?: number }
  return {
    items: (data.items || []).map(normalizeEssay),
    total: data.total ?? 0
  }
}

/**
 * 删除作文
 * DELETE /api/essays/:essayId
 */
export async function deleteEssayAPI(essayId: string): Promise<{ success: boolean; message: string }> {
  if (USE_MOCK_API) {
    return { success: true, message: '作文已删除' }
  }
  const response = await fetch(`${API_BASE_URL}/essays/${essayId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '删除作文')
  return response.json()
}

/**
 * 触发作文评测
 * POST /api/essays/:essayId/evaluate
 */
export async function requestEssayEvaluationAPI(essayId: string): Promise<Essay> {
  if (USE_MOCK_API) {
    const mockReport = generateMockEssayReport({
      id: essayId,
      title: '',
      topic: 'custom',
      content: '',
      wordCount: 0,
      targetLevel: 'N3'
    })
    return mockReport.essay
  }
  
  const response = await fetch(`${API_BASE_URL}/essays/${essayId}/evaluate`, {
    method: 'POST',
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '触发作文评测')
  const data = await response.json() as any
  return normalizeEssay(data.essay ?? data)
}

/**
 * 获取作文完整报告
 * GET /api/essays/:essayId/report
 */
export async function getEssayReportAPI(essayId: string): Promise<EssayEvaluationReport> {
  if (USE_MOCK_API) {
    return generateMockEssayReport({
      id: essayId,
      title: '',
      topic: 'custom',
      content: '',
      wordCount: 0,
      targetLevel: 'N3'
    })
  }
  
  const response = await fetch(`${API_BASE_URL}/essays/${essayId}/report`, {
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '获取作文报告')
  const data = await response.json() as any
  return normalizeEssayReport(data)
}

/**
 * 兼容旧调用：仅获取评分摘要
 */
export async function getEssayScore(essayId: string): Promise<EssayScore> {
  const report = await getEssayReportAPI(essayId)
  if (!report.scoreReport) {
    throw new Error('作文评测尚未完成')
  }
  return report.scoreReport
}

function normalizeEssayScore(data: any): EssayScore {
  return {
    id: String(data?.id ?? ''),
    essayId: String(data?.essayId ?? data?.essay_id ?? ''),
    overallScore: Number(data?.overallScore ?? data?.overall_score ?? 0),
    taskCompletionScore: Number(data?.taskCompletionScore ?? data?.task_completion_score ?? 0),
    grammarScore: Number(data?.grammarScore ?? data?.grammar_score ?? 0),
    vocabularyScore: Number(data?.vocabularyScore ?? data?.vocabulary_score ?? 0),
    coherenceScore: Number(data?.coherenceScore ?? data?.coherence_score ?? 0),
    naturalnessScore: Number(data?.naturalnessScore ?? data?.naturalness_score ?? 0),
    jlptFitScore: Number(data?.jlptFitScore ?? data?.jlpt_fit_score ?? 0),
    levelEstimate: String(data?.levelEstimate ?? data?.level_estimate ?? ''),
    summary: String(data?.summary ?? ''),
    comments: String(data?.comments ?? ''),
    aiEvaluated: Boolean(data?.aiEvaluated ?? data?.ai_evaluated ?? false),
    modelVersion: String(data?.modelVersion ?? data?.model_version ?? ''),
    evaluationTime: parseTimestamp(data?.evaluationTime ?? data?.evaluation_time)
  }
}

function normalizeEssayRevision(data: any): EssayRevision {
  return {
    id: String(data?.id ?? ''),
    essayId: String(data?.essayId ?? data?.essay_id ?? ''),
    issues: Array.isArray(data?.issues) ? data.issues : [],
    sentenceSuggestions: Array.isArray(data?.sentenceSuggestions ?? data?.sentence_suggestions)
      ? (data?.sentenceSuggestions ?? data?.sentence_suggestions)
      : [],
    fullRevision: String(data?.fullRevision ?? data?.full_revision ?? ''),
    expandedRevision: String(data?.expandedRevision ?? data?.expanded_revision ?? ''),
    polishedRevision: String(data?.polishedRevision ?? data?.polished_revision ?? ''),
    revisionNotes: String(data?.revisionNotes ?? data?.revision_notes ?? ''),
    revisedScore: data?.revisedScore ?? data?.revised_score
      ? normalizeEssayScore(data.revisedScore ?? data.revised_score)
      : null,
    modelVersion: String(data?.modelVersion ?? data?.model_version ?? ''),
    generatedAt: parseTimestamp(data?.generatedAt ?? data?.generated_at)
  }
}

function normalizeEssay(data: any): Essay {
  return {
    id: String(data?.id ?? ''),
    title: String(data?.title ?? ''),
    content: String(data?.content ?? ''),
    topic: String(data?.topic ?? ''),
    wordCount: Number(data?.wordCount ?? data?.word_count ?? 0),
    targetLevel: String(data?.targetLevel ?? data?.target_level ?? 'N3'),
    status: String(data?.status ?? 'pending'),
    submitTime: parseTimestamp(data?.submitTime ?? data?.submit_time),
    evaluationRequestedAt: parseTimestamp(data?.evaluationRequestedAt ?? data?.evaluation_requested_at),
    evaluationCompletedAt: parseTimestamp(data?.evaluationCompletedAt ?? data?.evaluation_completed_at),
    errorMessage: String(data?.errorMessage ?? data?.error_message ?? ''),
    scoreReport: data?.scoreReport ?? data?.score_report ? normalizeEssayScore(data.scoreReport ?? data.score_report) : undefined,
    revisionReport: data?.revisionReport ?? data?.revision_report ? normalizeEssayRevision(data.revisionReport ?? data.revision_report) : undefined,
    modelVersions: data?.modelVersions ?? data?.model_versions ?? {}
  }
}

function normalizeEssayReport(data: any): EssayEvaluationReport {
  return {
    essay: normalizeEssay(data?.essay ?? {}),
    status: String(data?.status ?? data?.essay?.status ?? 'pending'),
    scoreReport: data?.scoreReport ?? data?.score_report ? normalizeEssayScore(data.scoreReport ?? data.score_report) : null,
    revisionReport: data?.revisionReport ?? data?.revision_report ? normalizeEssayRevision(data.revisionReport ?? data.revision_report) : null,
    job: data?.job
      ? {
          id: String(data.job.id ?? ''),
          essayId: String(data.job.essayId ?? data.job.essay_id ?? ''),
          status: String(data.job.status ?? ''),
          errorMessage: String(data.job.errorMessage ?? data.job.error_message ?? ''),
          scoreModelVersion: String(data.job.scoreModelVersion ?? data.job.score_model_version ?? ''),
          revisionModelVersion: String(data.job.revisionModelVersion ?? data.job.revision_model_version ?? ''),
          startedAt: parseTimestamp(data.job.startedAt ?? data.job.started_at),
          completedAt: parseTimestamp(data.job.completedAt ?? data.job.completed_at)
        }
      : null,
    modelVersions: data?.modelVersions ?? data?.model_versions ?? {},
    errorMessage: String(data?.errorMessage ?? data?.error_message ?? '')
  }
}

export function generateMockEssayReport(input: {
  id: string
  title: string
  topic: string
  content: string
  wordCount: number
  targetLevel: string
}): EssayEvaluationReport {
  const randomScore = (base: number = 70, range: number = 18): number => {
    return Math.min(100, Math.max(0, Math.round(base + Math.random() * range - range / 2)))
  }
  const grammarScore = randomScore(74)
  const vocabularyScore = randomScore(72)
  const coherenceScore = randomScore(70)
  const naturalnessScore = randomScore(71)
  const taskCompletionScore = randomScore(76)
  const jlptFitScore = randomScore(73)
  const overallScore = Math.round(
    taskCompletionScore * 0.2
    + grammarScore * 0.22
    + vocabularyScore * 0.2
    + coherenceScore * 0.16
    + naturalnessScore * 0.12
    + jlptFitScore * 0.1
  )
  const now = Date.now()
  const scoreReport: EssayScore = {
    id: `score_${now}`,
    essayId: input.id,
    overallScore,
    taskCompletionScore,
    grammarScore,
    vocabularyScore,
    coherenceScore,
    naturalnessScore,
    jlptFitScore,
    levelEstimate: overallScore >= 80 ? 'N2' : overallScore >= 70 ? 'N3' : 'N4',
    summary: '已生成研究原型评分报告，可用于验证双模型链路。',
    comments: '评分模型已按 JLPT 风格维度给出总评。',
    aiEvaluated: false,
    modelVersion: 'mock-jlpt-score-v1',
    evaluationTime: now
  }
  const revisionReport: EssayRevision = {
    id: `revision_${now}`,
    essayId: input.id,
    issues: [
      {
        source: input.content.slice(0, 32),
        suggestion: input.content.slice(0, 32),
        explanation: '建议补充连接词或更完整的背景信息。',
        severity: 'medium'
      }
    ],
    sentenceSuggestions: [
      {
        original: input.content.slice(0, 60),
        suggested: input.content ? `また、${input.content.slice(0, 60)}` : '',
        reason: '增加连接词可提升连贯性。'
      }
    ],
    fullRevision: input.content,
    revisionNotes: '修改模型已给出逐句建议和修正版。',
    modelVersion: 'mock-jlpt-revision-v1',
    generatedAt: now
  }
  const essay: Essay = {
    id: input.id,
    title: input.title,
    content: input.content,
    topic: input.topic,
    wordCount: input.wordCount,
    targetLevel: input.targetLevel,
    status: 'completed',
    submitTime: now,
    evaluationRequestedAt: now,
    evaluationCompletedAt: now,
    errorMessage: '',
    scoreReport,
    revisionReport,
    modelVersions: {
      score: scoreReport.modelVersion,
      revision: revisionReport.modelVersion
    }
  }
  return {
    essay,
    status: essay.status,
    scoreReport,
    revisionReport,
    job: {
      id: `job_${now}`,
      essayId: input.id,
      status: 'completed',
      errorMessage: '',
      scoreModelVersion: scoreReport.modelVersion,
      revisionModelVersion: revisionReport.modelVersion,
      startedAt: now,
      completedAt: now
    },
    modelVersions: essay.modelVersions ?? {},
    errorMessage: ''
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
 * 获取后端辞书配置
 * GET /api/study-plans/dictionaries
 */
export async function getDictionaryCatalog(): Promise<DictionaryConfig[]> {
  if (USE_MOCK_API) {
    return DICTIONARIES as DictionaryConfig[]
  }

  const response = await fetch(`${API_BASE_URL}/study-plans/dictionaries`, {
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '获取辞书配置')
  return response.json()
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
  void planId
  void date
   
  if (USE_MOCK_API) {
    // 返回随机单词作为复习列表
    return getRandomWords(5)
  }

  const data = await getReviewToday(100)
  return data.items.map(item => item.word)
}

/**
 * 获取今日到期复习任务
 * GET /api/review/today
 */
export async function getReviewToday(limit: number = 100): Promise<ReviewWordList> {
  const safeLimit = Math.min(500, Math.max(1, limit))

  if (USE_MOCK_API) {
    const words = getRandomWords(Math.min(safeLimit, 10))
    const now = Date.now()
    return {
      items: words.map(word => ({
        word,
        progress: {
          wordId: word.id,
          status: 'unknown',
          reviewCount: 0,
          correctCount: 0,
          lastReviewedAt: now,
          interval: 0.02,
          ease: 2.5,
          lapseCount: 0,
          nextReview: now,
          lastReview: now,
          createdAt: now
        }
      })),
      count: words.length,
      limit: safeLimit,
      timestamp: now
    }
  }

  const response = await fetch(`${API_BASE_URL}/review/today?limit=${safeLimit}`, {
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '获取今日复习任务')
  const data: ReviewWordListApiResponse = await response.json()
  return normalizeReviewWordList(data)
}

/**
 * 获取强化练习随机任务
 * GET /api/review/random
 */
export async function getReviewRandom(limit: number = 20): Promise<ReviewWordList> {
  const safeLimit = Math.min(200, Math.max(1, limit))

  if (USE_MOCK_API) {
    const words = getRandomWords(Math.min(safeLimit, 10))
    const now = Date.now()
    return {
      items: words.map(word => ({
        word,
        progress: {
          wordId: word.id,
          status: 'fuzzy',
          reviewCount: 2,
          correctCount: 1,
          lastReviewedAt: now,
          interval: 1,
          ease: 2.2,
          lapseCount: 1,
          nextReview: now,
          lastReview: now,
          createdAt: now
        }
      })),
      count: words.length,
      limit: safeLimit
    }
  }

  const response = await fetch(`${API_BASE_URL}/review/random?limit=${safeLimit}`, {
    headers: getAuthHeaders()
  })
  assertApiResponse(response, '获取强化练习任务')
  const data: ReviewWordListApiResponse = await response.json()
  return normalizeReviewWordList(data)
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
    expiredTokenHandled = false
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
  expiredTokenHandled = false
  localStorage.removeItem('yomii_auth_token')
  localStorage.removeItem('yomii_user')
  localStorage.removeItem(LOCAL_STORAGE_KEYS.SEARCH_HISTORY)
  localStorage.removeItem(LOCAL_STORAGE_KEYS.QUIZ_HISTORY)
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
  const token = localStorage.getItem('yomii_auth_token')
  if (!token) return null

  if (isTokenExpired(token)) {
    handleExpiredToken()
    return null
  }
  return token
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
  getQuizDifficulties,
  submitQuizAnswer,
  submitQuizSession,
  getQuizHistory,
  deleteQuizSessionAPI,
  getQuizAbilityReport,
  updateWordProgress,
  getStudyStats,
  getSearchHistory,
  deleteSearchHistory,
  addToFavorites,
  removeFromFavorites,
  getFavorites,
  getUserProgress,
  submitEssayAPI,
  getEssayHistoryAPI,
  deleteEssayAPI,
  requestEssayEvaluationAPI,
  getEssayReportAPI,
  getEssayScore,
  generateMockEssayReport,
  // 学习计划相关
  getDictionaryCatalog,
  getStudyPlans,
  getCurrentStudyPlan,
  createStudyPlan,
  updateStudyPlan,
  activateStudyPlan,
  getLearnWords,
  getReviewWords,
  getReviewToday,
  getReviewRandom,
  saveLearningSession,
  getLearningSessions,
  requestAddMore
}
