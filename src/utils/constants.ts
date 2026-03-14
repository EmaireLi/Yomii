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
  STUDY_STATS: 'yomii_study_stats'
} as const

export const DEFAULT_APP_CONFIG = {
  theme: 'light' as const,
  language: 'zh' as const,
  autoPlayAudio: false,
  dailyGoal: 30
}
