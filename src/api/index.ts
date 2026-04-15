/**
 * API 客户端
 * 
 * 所有数据通过 API 接口获取和提交
 * 支持 Mock 模式和真实后端两种模型
 */

import type { Word, SearchResult, QuizQuestion, WordProgress, StudyStats, Essay, EssayScore, StudyPlan, LearningSession, User, AuthResponse, RegisterRequest, LoginRequest, ResetPasswordRequest, SetNewPasswordRequest } from '@/types'
import { getRandomWords, searchWords as localSearchWords, QUIZ_QUESTIONS, WORDS_DATABASE } from '@/utils/mockData'
import { DEFAULT_STUDY_PLAN } from '@/utils/constants'

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

function getAuthHeaders(): HeadersInit {
  const token = getAuthToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/**
 * 搜索单词
 * GET /api/words/search?q=keyword&limit=10
 */
export async function searchWords(keyword: string, limit: number = 10): Promise<SearchResult[]> {
  if (USE_MOCK_API) {
    return localSearchWords(keyword).slice(0, limit)
  }
  
  const response = await fetch(`${API_BASE_URL}/words/search?q=${encodeURIComponent(keyword)}&limit=${limit}`, {
    headers: getAuthHeaders()
  })
  if (!response.ok) throw new Error(`搜索失败: ${response.statusText}`)
  const data: WordApiResponse[] = await response.json()
  return data.map(normalizeWord)
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
  
  const response = await fetch(`${API_BASE_URL}/user/stats`)
  if (!response.ok) throw new Error(`获取学习统计失败: ${response.statusText}`)
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
export async function addToFavorites(wordId: string, word: Word): Promise<{ success: boolean }> {
  if (USE_MOCK_API) {
    return { success: true }
  }
  
  const response = await fetch(`${API_BASE_URL}/user/favorites/${wordId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(word)
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
    method: 'DELETE'
  })
  if (!response.ok) throw new Error(`移除收藏失败: ${response.statusText}`)
  return response.json()
}

/**
 * 获取收藏夹列表
 * GET /api/user/favorites
 */
export async function getFavorites(): Promise<Word[]> {
  if (USE_MOCK_API) {
    return []
  }
  
  const response = await fetch(`${API_BASE_URL}/user/favorites`)
  if (!response.ok) throw new Error(`获取收藏列表失败: ${response.statusText}`)
  return response.json()
}

/**
 * 获取学习进度
 * GET /api/user/progress
 */
export async function getUserProgress(): Promise<WordProgress[]> {
  if (USE_MOCK_API) {
    return []
  }
  
  const response = await fetch(`${API_BASE_URL}/user/progress`)
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
  
  const response = await fetch(`${API_BASE_URL}/study-plans`)
  if (!response.ok) throw new Error(`获取学习计划失败: ${response.statusText}`)
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
  
  const response = await fetch(`${API_BASE_URL}/study-plans/current`)
  if (!response.ok) throw new Error(`获取当前学习计划失败: ${response.statusText}`)
  return response.json()
}

/**
 * 创建新的学习计划
 * POST /api/study-plans
 */
export async function createStudyPlan(plan: Omit<StudyPlan, 'id' | 'createdAt' | 'updatedAt'>): Promise<StudyPlan> {
  if (USE_MOCK_API) {
    return {
      ...plan,
      id: `plan_${Date.now()}`,
      createdAt: Date.now(),
      updatedAt: Date.now()
    }
  }
  
  const response = await fetch(`${API_BASE_URL}/study-plans`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(plan)
  })
  if (!response.ok) throw new Error(`创建学习计划失败: ${response.statusText}`)
  return response.json()
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
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates)
  })
  if (!response.ok) throw new Error(`更新学习计划失败: ${response.statusText}`)
  return response.json()
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
    method: 'POST'
  })
  if (!response.ok) throw new Error(`激活学习计划失败: ${response.statusText}`)
  return response.json()
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
  
  const response = await fetch(`${API_BASE_URL}/study-plans/${planId}/learn-words?date=${targetDate}`)
  if (!response.ok) throw new Error(`获取待背诵单词失败: ${response.statusText}`)
  return response.json()
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
  
  const response = await fetch(`${API_BASE_URL}/study-plans/${planId}/review-words?date=${targetDate}`)
  if (!response.ok) throw new Error(`获取复习单词失败: ${response.statusText}`)
  return response.json()
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
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(session)
  })
  if (!response.ok) throw new Error(`保存学习轮次失败: ${response.statusText}`)
  return response.json()
}

/**
 * 获取学习轮次列表
 * GET /api/study-plans/:planId/sessions
 */
export async function getLearningSessions(planId: string): Promise<LearningSession[]> {
  if (USE_MOCK_API) {
    return []
  }
  
  const response = await fetch(`${API_BASE_URL}/study-plans/${planId}/sessions`)
  if (!response.ok) throw new Error(`获取学习轮次失败: ${response.statusText}`)
  return response.json()
}

/**
 * 请求加量学习（增加当天的学习量）
 * POST /api/study-plans/:planId/add-more
 */
export async function requestAddMore(planId: string, additionalCount: number): Promise<{ success: boolean; moreWords: Word[] }> {
  if (USE_MOCK_API) {
    return {
      success: true,
      moreWords: getRandomWords(additionalCount)
    }
  }
  
  const response = await fetch(`${API_BASE_URL}/study-plans/${planId}/add-more`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ additionalCount })
  })
  if (!response.ok) throw new Error(`加量学习失败: ${response.statusText}`)
  return response.json()
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
  }
  return result
}

/**
 * 用户登出
 */
export function logout(): void {
  localStorage.removeItem('yomii_auth_token')
  localStorage.removeItem('yomii_user')
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
