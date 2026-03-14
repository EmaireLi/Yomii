/**
 * Yomii 词典应用 - 类型定义
 */

/** 词语详细信息 */
export interface Word {
  id: string
  word: string
  kana: string
  meaning: string
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
  question: string
  word: Word
  options: string[]
  correctAnswer: string
  explanation: string
}

/** 测试结果 */
export interface QuizResult {
  questionId: string
  userAnswer: string
  isCorrect: boolean
  timestamp: number
}

/** 作文提交 */
export interface Essay {
  id: string
  title: string
  content: string
  topic: string
  wordCount: number
  submitTime: number
  score?: EssayScore
}

/** 作文评分（AI 评测就绪） */
export interface EssayScore {
  id: string
  essayId: string
  overallScore: number
  gramarScore: number        // 语法分
  vocabularyScore: number    // 词汇分
  fluencyScore: number       // 流畅度
  coherenceScore: number     // 连贯性
  comments: string
  aiEvaluated: boolean       // 是否由 AI 评论
  evaluationTime: number
}

/** 应用配置 */
export interface AppConfig {
  theme: 'light' | 'dark'
  language: 'zh' | 'en' | 'ja'
  autoPlayAudio: boolean
  dailyGoal: number
}

/** 用户数据 */
export interface UserData {
  stats: StudyStats
  wordProgress: Record<string, WordProgress>
  favorites: string[]
  searchHistory: string[]
  quizResults: QuizResult[]
  config: AppConfig
}
