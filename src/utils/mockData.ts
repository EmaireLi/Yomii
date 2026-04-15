/**
 * 模拟数据库
 */

import type { Word, QuizQuestion } from '@/types'

export const WORDS_DATABASE: Word[] = [
  {
    id: '1',
    word: '辞書',
    kana: 'じしょ',
    japaneseMeaning: '言葉の意味や使い方を調べるための本。',
    chineseMeaning: '词典，字典',
    example: '新しい辞書を買いました。(买了一本新词典。)',
    partOfSpeech: 'noun',
    tags: ['初级', '常用']
  },
  {
    id: '2',
    word: '勉強',
    kana: 'べんきょう',
    japaneseMeaning: '知識を身につけるために学ぶこと。',
    chineseMeaning: '学习，用功',
    example: '今日の勉強は楽しかった。(今天的学习很愉快。)',
    partOfSpeech: 'noun, verb',
    tags: ['初级', '日常']
  },
  {
    id: '3',
    word: '桜',
    kana: 'さくら',
    japaneseMeaning: '春に咲く、日本を代表する花。',
    chineseMeaning: '樱花',
    example: '春になると桜が咲きます。(春天樱花开放。)',
    partOfSpeech: 'noun',
    tags: ['初级', '四季']
  },
  {
    id: '4',
    word: '世界',
    kana: 'せかい',
    japaneseMeaning: '地球全体、または社会全体。',
    chineseMeaning: '世界',
    example: '世界中の人々。(世界各地的人们。)',
    partOfSpeech: 'noun',
    tags: ['中级', '地理']
  },
  {
    id: '5',
    word: '友達',
    kana: 'ともだち',
    japaneseMeaning: '親しく付き合う相手。',
    chineseMeaning: '朋友，伙伴',
    example: '良い友達がいます。(有好朋友。)',
    partOfSpeech: 'noun',
    tags: ['初级', '人际']
  },
  {
    id: '6',
    word: '家族',
    kana: 'かぞく',
    japaneseMeaning: '同じ家で生活する身近な人たち。',
    chineseMeaning: '家族，家人',
    example: '大きな家族です。(是个大家族。)',
    partOfSpeech: 'noun',
    tags: ['初级', '家庭']
  },
  {
    id: '7',
    word: '学校',
    kana: 'がっこう',
    japaneseMeaning: '勉強するための教育機関。',
    chineseMeaning: '学校',
    example: '学校に行きます。(去学校。)',
    partOfSpeech: 'noun',
    tags: ['初级', '教育']
  },
  {
    id: '8',
    word: '仕事',
    kana: 'しごと',
    japaneseMeaning: '職業として行う業務や作業。',
    chineseMeaning: '工作，职业',
    example: '毎日仕事に頑張ります。(每天努力工作。)',
    partOfSpeech: 'noun',
    tags: ['中级', '职业']
  },
  {
    id: '9',
    word: '食べる',
    kana: 'たべる',
    japaneseMeaning: '食物を口に入れて飲み込む。',
    chineseMeaning: '吃',
    example: 'ご飯を食べます。(吃饭。)',
    partOfSpeech: 'verb',
    tags: ['初级', '动词']
  },
  {
    id: '10',
    word: '美しい',
    kana: 'うつくしい',
    japaneseMeaning: '見た目や心がきれいで魅力がある。',
    chineseMeaning: '美丽的，漂亮的',
    example: '美しい景色。(美丽的风景。)',
    partOfSpeech: 'adjective',
    tags: ['中级', '形容词']
  }
]

export const QUIZ_QUESTIONS: QuizQuestion[] = [
  {
    id: 'q1',
    type: 'multiple-choice',
    question: '以下哪个选项是「世界」的正确读音？',
    word: WORDS_DATABASE[3] as Word,
    options: ['せかい', 'しゃかい', 'じだい', 'みらい'],
    correctAnswer: 'せかい',
    explanation: '「世界」的正确读音是せかい(sekai)，表示世界的意思。'
  },
  {
    id: 'q2',
    type: 'multiple-choice',
    question: '「勉強」是什么意思？',
    word: WORDS_DATABASE[1] as Word,
    options: ['学习', '工作', '休息', '玩耍'],
    correctAnswer: '学习',
    explanation: '「勉強」(べんきょう)的意思是学习或用功。'
  },
  {
    id: 'q3',
    type: 'multiple-choice',
    question: '以下哪个选项是「桜」的汉字写法对应的读音？',
    word: WORDS_DATABASE[2] as Word,
    options: ['さくら', 'あかり', 'はな', 'き'],
    correctAnswer: 'さくら',
    explanation: '「桜」(さくら)是樱花的意思，在春天开放。'
  }
]

/**
 * 模拟搜索词汇
 */
export function searchWords(query: string): Word[] {
  if (!query.trim()) return []
  
  const lowerQuery = query.toLowerCase()
  
  return WORDS_DATABASE.filter(word => 
    word.word.includes(query) ||
    word.kana.includes(query) ||
    word.japaneseMeaning.toLowerCase().includes(lowerQuery) ||
    word.chineseMeaning.toLowerCase().includes(lowerQuery)
  )
}

/**
 * 获取随机词汇
 */
export function getRandomWords(count: number = 1): Word[] {
  const shuffled = [...WORDS_DATABASE].sort(() => Math.random() - 0.5)
  return shuffled.slice(0, count)
}

/**
 * 获取词汇详情
 */
export function getWordById(id: string): Word | undefined {
  return WORDS_DATABASE.find(w => w.id === id)
}
