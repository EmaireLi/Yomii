/**
 * 应用全局常量
 */

export const TEAM_INFO = {
  name: '软件项目综合实践小组',
  members: [
    { name: '李政杭', id: '2023141461091', role: '组长' },
    { name: '刘鑫', id: '2023141461105', role: '成员' },
    { name: '张志友', id: '2023141461090', role: '成员' },
    { name: '李昊屹', id: '2023141470286', role: '成员' },
    { name: '曹陈洋', id: '2023141490019', role: '成员' }
  ]
}

export const APP_DESCRIPTION = '这是一款专为日语学习者打造的电脑桌面软件。基于专业词典，提供查词、背单词、听发音和自测等核心功能。后续将引入AI评测技术，让能力测试更高效。'

export const VIEWS = {
  HOME: 'home',
  SEARCH: 'search',
  RECITE: 'recite',
  TEST: 'test',
  ESSAY: 'essay',
  STATS: 'stats',
  FAVORITES: 'favorites'
} as const

export const WORD_STATUS = {
  UNKNOWN: 'unknown',
  FUZZY: 'fuzzy',
  KNOWN: 'known'
} as const

export const LOCAL_STORAGE_KEYS = {
  USER_DATA: 'yomii_user_data',
  SEARCH_HISTORY: 'yomii_search_history',
  FAVORITES: 'yomii_favorites',
  WORD_PROGRESS: 'yomii_word_progress',
  STUDY_STATS: 'yomii_study_stats',
  STUDY_PLANS: 'yomii_study_plans',
  CURRENT_PLAN: 'yomii_current_plan',
  LEARNING_SESSIONS: 'yomii_learning_sessions'
} as const

export const DEFAULT_APP_CONFIG = {
  theme: 'light' as const,
  language: 'zh' as const,
  autoPlayAudio: false,
  dailyGoal: 30
}

export const DEFAULT_STUDY_PLAN = {
  id: 'default-plan',
  name: '默认学习计划',
  dailyGoal: 10,              // 默认每天背10个单词
  reviewRatio: 0.5,           // 复习为学习的50%
  dictionaryId: 'common',     // 选择的辞书
  createdAt: Date.now(),
  updatedAt: Date.now(),
  isActive: true
}

// 辞书列表
export const DICTIONARIES = [
  { id: 'common', name: '常用词典', description: '最常用的 1500 个单词', wordCount: 1500 },
  { id: 'daily', name: '日常词典', description: '日常生活中的 2500 个词汇', wordCount: 2500 },
  { id: 'jlpt3', name: 'JLPT N3', description: '日本语能力测试 N3 级词汇', wordCount: 3700 },
  { id: 'jlpt2', name: 'JLPT N2', description: '日本语能力测试 N2 级词汇', wordCount: 6000 },
  { id: 'jlpt1', name: 'JLPT N1', description: '日本语能力测试 N1 级词汇', wordCount: 10000 },
  { id: 'business', name: '商务词典', description: '商务日语常用词汇', wordCount: 2000 }
]

// 单词数量预设选项
export const WORD_COUNT_OPTIONS = [5, 10, 15, 20, 30, 50]
