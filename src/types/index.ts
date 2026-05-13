/**
 * Yomii 词典应用 - 类型定义
 */

/** 词语详细信息 */
export interface Word {
  id: string
  word: string
  kana: string
  japaneseMeaning: string
  chineseMeaning: string
  example: string
  partOfSpeech?: string
  audioUrl?: string
  tags?: string[]
}

/** 搜索结果项 */
export interface SearchResult extends Word {
  relevance?: number
}

/** 用户学习进度 */
export interface WordProgress {
  wordId: string
  status: 'unknown' | 'fuzzy' | 'known'
  lastReviewedAt: number
  reviewCount: number
  correctCount: number
  interval?: number
  ease?: number
  lapseCount?: number
  nextReview?: number
  lastReview?: number
  createdAt?: number
}

export type ReviewRating = 'again' | 'hard' | 'good'

export interface ReviewWordItem {
  word: Word
  progress: WordProgress
}

export interface ReviewWordList {
  items: ReviewWordItem[]
  count: number
  limit: number
  timestamp?: number
}

/** 学习统计 */
export interface StudyStats {
  totalWordsLearned: number
  totalWordsRecited: number
  todayLearned: number
  todayRecited: number
  currentStreak: number
  longestStreak: number
  lastStudyDate: number
}

/** 测试题目 */
export interface QuizQuestion {
  id: string
  type: 'multiple-choice' | 'fill-blank' | 'listening'
  questionMode?: 'kana' | 'chinese' | string
  question: string
  word: Word
  options: string[]
  correctAnswer: string
  explanation: string
}

export interface QuizDifficultyOption {
  value: string
  label: string
  tags?: string[]
}

/** 测试结果 */
export interface QuizResult {
  questionId: string
  userAnswer: string
  isCorrect: boolean
  timestamp: number
}

/** 测试历史记录 */
export interface QuizSessionRecord {
  id: number | string
  difficulty: 'easy' | 'medium' | 'hard' | string
  totalQuestions: number
  correctAnswers: number
  accuracy: number
  durationSeconds: number
  abilityScore: number
  level: string
  summary: string
  trendDelta: number
  consistencyScore: number
  speedScore: number
  recommendations: string[]
  difficultyBreakdown: Array<{
    difficulty: string
    accuracy: number
    count: number
  }>
  completedAt: number
}

/** 能力报告（结合历史记录生成） */
export interface QuizAbilityReport {
  overallScore: number
  level: string
  trend: {
    direction: 'up' | 'down' | 'stable' | string
    delta: number
  }
  consistencyScore: number
  speedScore: number
  historyCount: number
  basedOnSessions: number
  recommendations: string[]
  summary: string
  generatedAt: number
  currentSession: QuizSessionRecord | null
  difficultyBreakdown: Array<{
    difficulty: string
    accuracy: number
    count: number
  }>
}

/** 作文提交 */
export interface Essay {
  id: string
  title: string
  content: string
  topic: string
  wordCount: number
  targetLevel: string
  status: 'pending' | 'scoring' | 'revising' | 'completed' | 'failed' | string
  progressPercent?: number
  progressMessage?: string
  submitTime: number
  evaluationRequestedAt?: number
  evaluationCompletedAt?: number
  errorMessage?: string
  scoreReport?: EssayScore
  revisionReport?: EssayRevision
  modelVersions?: {
    score?: string
    revision?: string
  }
}

/** 作文评分（AI 评测就绪） */
export interface EssayScore {
  id: string
  essayId: string
  overallScore: number
  taskCompletionScore: number
  grammarScore: number
  vocabularyScore: number
  coherenceScore: number
  naturalnessScore: number
  jlptFitScore: number
  levelEstimate: string
  summary: string
  comments: string
  aiEvaluated: boolean
  modelVersion: string
  evaluationTime: number
}

export interface EssayRevisionIssue {
  source: string
  suggestion: string
  explanation: string
  severity: string
}

export interface EssaySentenceSuggestion {
  original: string
  suggested: string
  reason: string
}

export interface EssayRevision {
  id: string
  essayId: string
  issues: EssayRevisionIssue[]
  sentenceSuggestions: EssaySentenceSuggestion[]
  fullRevision: string
  expandedRevision: string
  polishedRevision: string
  revisionNotes: string
  revisedScore?: EssayScore | null
  modelVersion: string
  generatedAt: number
}

export interface EssayEvaluationReport {
  essay: Essay
  status: Essay['status']
  scoreReport: EssayScore | null
  revisionReport: EssayRevision | null
  job?: {
    id: string
    essayId: string
    status: string
    progressPercent: number
    progressMessage: string
    errorMessage: string
    scoreModelVersion: string
    revisionModelVersion: string
    startedAt: number
    completedAt: number
  } | null
  modelVersions: {
    score?: string
    revision?: string
  }
  errorMessage?: string
}

/** 应用配置 */
export interface AppConfig {
  theme: 'light' | 'dark'
  language: 'zh' | 'en' | 'ja'
  autoPlayAudio: boolean
  dailyGoal: number
}

/** 学习计划 */
export interface StudyPlan {
  id: string
  name: string
  dailyGoal: number           // 每天背诵的单词数
  reviewRatio: number         // 复习的单词数（通常是dailyGoal的一部分）
  dictionaryId?: string
  createdAt: number
  updatedAt: number
  isActive: boolean
}

/** 学习轮次记录 */
export interface LearningSession {
  id: string
  planId: string
  date: string                // YYYY-MM-DD 格式
  learnedWords: string[]      // 当天新学的单词ID列表
  reviewedWords: string[]     // 当天复习的单词ID列表
  sessionStats: {
    knownCount: number        // 掌握的数量
    fuzzyCount: number        // 模糊的数量
    unknownCount: number      // 未掌握的数量
  }
  completedAt?: number
}

/** 辞书配置（由后端返回） */
export interface DictionaryConfig {
  id: string
  name: string
  description: string
  wordCount: number
  level: 'easy' | 'medium' | 'hard' | string
  tags?: string[]
}

/** 用户数据 */
export interface UserData {
  stats: StudyStats
  wordProgress: Record<string, WordProgress>
  favorites: string[]
  searchHistory: string[]
  quizResults: QuizResult[]
  quizHistory?: QuizSessionRecord[]
  config: AppConfig
  studyPlans?: StudyPlan[]
  currentPlan?: StudyPlan
  learningSessions?: LearningSession[]
}

/** 用户账户信息 */
export interface User {
  id: string
  username: string
  phone: string
  createdAt: number
  lastLoginAt: number
}

/** 用户注册请求 */
export interface RegisterRequest {
  username: string
  phone: string
  password: string
  confirmPassword?: string
}

/** 用户登录请求 */
export interface LoginRequest {
  phone: string
  password: string
}

/** 密码重置请求 */
export interface ResetPasswordRequest {
  phone: string
}

/** 设置新密码请求 */
export interface SetNewPasswordRequest {
  code: string
  newPassword: string
  confirmPassword?: string
}

/** 认证响应 */
export interface AuthResponse {
  success: boolean
  message: string
  token?: string
  user?: User
  error?: string
}
