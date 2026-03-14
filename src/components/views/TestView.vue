<template>
  <section class="view-section test-view">
    <h1>智能测试 <span class="badge">AI Ready</span></h1>

    <div v-if="!testStarted" class="test-intro">
      <h2>开始测试</h2>
      <p>通过智能题库检测您的日语水平，获取详细的能力评估报告。</p>
      
      <div class="difficulty-selector">
        <h3>选择难度：</h3>
        <div class="difficulty-buttons">
          <button
            v-for="level in difficulties"
            :key="level.value"
            @click="selectedDifficulty = level.value"
            :class="['difficulty-btn', { active: selectedDifficulty === level.value }]"
          >
            {{ level.label }}
          </button>
        </div>
      </div>

      <div class="test-info">
        <p>📝 预计题目数量：10-15 题</p>
        <p>⏱️ 预计耗时：10-15 分钟</p>
        <p>🎯 题型：多选题、填空题、听力题</p>
      </div>

      <button @click="startTest" class="btn btn-start">
        开始测试
      </button>
    </div>

    <!-- 测试进行中 -->
    <div v-else-if="!testCompleted && currentQuestion">
      <div class="quiz-header">
        <div class="timer">⏱️ {{ formatTime(timeRemaining) }}</div>
        <div class="score">得分: {{ score }} / {{ totalQuestions }}</div>
      </div>

      <div class="progress-bar">
        <div class="progress" :style="{ width: progressPercent + '%' }"></div>
      </div>

      <div class="question-container">
        <h3 class="question-number">Q{{ currentIndex + 1 }} / {{ totalQuestions }}</h3>
        <h2 class="question-text">{{ currentQuestion.question }}</h2>
        
        <!-- 词汇展示 -->
        <div class="word-context" v-if="currentQuestion.word">
          <p class="word-display">{{ currentQuestion.word.word }}</p>
          <p class="word-kana">[{{ currentQuestion.word.kana }}]</p>
        </div>

        <!-- 选项 -->
        <div class="options">
          <label
            v-for="(option, idx) in currentQuestion.options"
            :key="idx"
            :class="['option', { selected: userAnswer === option }]"
          >
            <input
              type="radio"
              :value="option"
              v-model="userAnswer"
              :disabled="answered"
            />
            <span class="option-text">{{ option }}</span>
          </label>
        </div>

        <!-- 提交按钮 -->
        <div class="button-group">
          <button
            @click="submitAnswer"
            :disabled="!userAnswer || answered"
            class="btn btn-submit"
          >
            {{ answered ? '已提交' : '提交答案' }}
          </button>
          <button
            v-if="answered"
            @click="nextQuestion"
            class="btn btn-next"
          >
            下一题
          </button>
        </div>

        <!-- 解析 -->
        <transition name="expand">
          <div v-if="answered" class="explanation">
            <div :class="['explanation-box', isCorrect ? 'correct' : 'incorrect']">
              <p class="explanation-status">
                {{ isCorrect ? '✓ 回答正确！' : '✗ 回答错误' }}
              </p>
              <p class="explanation-text"><strong>解析：</strong> {{ currentQuestion.explanation }}</p>
              <p v-if="!isCorrect" class="correct-answer">
                <strong>正确答案：</strong> {{ currentQuestion.correctAnswer }}
              </p>
            </div>
          </div>
        </transition>
      </div>
    </div>

    <!-- 测试完成 -->
    <div v-else-if="testCompleted" class="test-result">
      <div class="result-header">
        <p class="result-icon">🎓</p>
        <h2>测试完成！</h2>
        <p class="result-score">最终得分</p>
        <div class="score-display">
          <div class="final-score">{{ score }}</div>
          <div class="total-score">/ {{ totalQuestions }}</div>
        </div>
        <p class="accuracy">正确率: {{ accuracy }}%</p>
      </div>

      <div class="result-analysis">
        <h3>成绩分析</h3>
        <div class="analysis-grid">
          <div class="analysis-item">
            <span class="analysis-label">答对题数</span>
            <span class="analysis-value" style="color: #67c23a;">{{ score }}</span>
          </div>
          <div class="analysis-item">
            <span class="analysis-label">答错题数</span>
            <span class="analysis-value" style="color: #f56c6c;">{{ totalQuestions - score }}</span>
          </div>
          <div class="analysis-item">
            <span class="analysis-label">准确率</span>
            <span class="analysis-value" style="color: #409eff;">{{ accuracy }}%</span>
          </div>
        </div>
      </div>

      <div class="result-recommendation">
        <h3>评价与建议</h3>
        <p class="recommendation-text">{{ recommendation }}</p>
        <div class="action-buttons">
          <button @click="resetTest" class="btn btn-primary">重新测试</button>
          <button @click="$emit('switchView', 'recite')" class="btn btn-secondary">
            去背单词增强基础
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import type { QuizQuestion } from '@/types'
import { getQuizQuestions as getQuizQuestionsAPI } from '@/api'

const emit = defineEmits<{
  switchView: [view: string]
}>()

// 测试状态
const testStarted = ref(false)
const testCompleted = ref(false)
const currentIndex = ref(0)
const score = ref(0)
const userAnswer = ref('')
const answered = ref(false)
const selectedDifficulty = ref('medium')
const timeRemaining = ref(600) // 10分钟
const isLoading = ref(false)

const difficulties = [
  { label: '初级', value: 'easy' },
  { label: '中级', value: 'medium' },
  { label: '高级', value: 'hard' }
]

const questions = ref<QuizQuestion[]>([])
const totalQuestions = computed(() => questions.value.length)

const currentQuestion = computed(() => questions.value[currentIndex.value] || null)

const progressPercent = computed(() => {
  if (totalQuestions.value === 0) return 0
  return (currentIndex.value / totalQuestions.value) * 100
})

const isCorrect = computed(() => {
  return userAnswer.value === currentQuestion.value?.correctAnswer
})

const accuracy = computed(() => {
  if (totalQuestions.value === 0) return 0
  return Math.round((score.value / totalQuestions.value) * 100)
})

const recommendation = computed(() => {
  if (accuracy.value >= 80) {
    return '太棒了！您的日语水平已经达到中高级，继续保持学习的热情，可以尝试更高难度的内容。'
  } else if (accuracy.value >= 60) {
    return '不错！您对日语有了基本的理解，建议继续加强词汇和语法的学习。'
  } else if (accuracy.value >= 40) {
    return '继续努力！建议您多进行背单词练习，打好基础再进行更深层的学习。'
  } else {
    return '加油！建议从基础词汇开始学习，循序渐进地提高您的日语水平。'
  }
})

const startTest = async () => {
  testStarted.value = true
  testCompleted.value = false
  currentIndex.value = 0
  score.value = 0
  userAnswer.value = ''
  answered.value = false
  isLoading.value = true
  
  try {
    // 从 API 获取题目
    questions.value = await getQuizQuestionsAPI(selectedDifficulty.value, 10)
    
    // 启动计时器
    startTimer()
  } catch (error) {
    console.error('Failed to load quiz questions:', error)
    testStarted.value = false
  } finally {
    isLoading.value = false
  }
}

const submitAnswer = () => {
  answered.value = true
  if (isCorrect.value) {
    score.value++
  }
}

const nextQuestion = () => {
  currentIndex.value++
  userAnswer.value = ''
  answered.value = false
  
  if (currentIndex.value >= totalQuestions.value) {
    testCompleted.value = true
  }
}

const resetTest = () => {
  testStarted.value = false
  testCompleted.value = false
  currentIndex.value = 0
  score.value = 0
  userAnswer.value = ''
  answered.value = false
  if (timerInterval) {
    clearInterval(timerInterval)
  }
}

const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

let timerInterval: number

const startTimer = () => {
  timeRemaining.value = 600
  timerInterval = setInterval(() => {
    timeRemaining.value--
    if (timeRemaining.value <= 0) {
      clearInterval(timerInterval)
      testCompleted.value = true
    }
  }, 1000) as unknown as number
}

onUnmounted(() => {
  if (timerInterval) {
    clearInterval(timerInterval)
  }
})
</script>

<style scoped>
.test-intro {
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
}

.test-intro h2 {
  font-size: 20px;
  margin-bottom: 10px;
  color: #303133;
}

.test-intro p {
  color: #666;
  line-height: 1.6;
  margin-bottom: 20px;
  font-size: 14px;
}

.difficulty-selector {
  margin: 25px 0;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.difficulty-selector h3 {
  margin-top: 0;
  color: #303133;
  font-size: 14px;
}

.difficulty-buttons {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}

.difficulty-btn {
  padding: 8px 16px;
  background: white;
  border: 2px solid #dcdfe6;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
}

.difficulty-btn:hover {
  border-color: #409eff;
}

.difficulty-btn.active {
  background: #409eff;
  color: white;
  border-color: #409eff;
}

.test-info {
  background: #ecf5ff;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 20px;
  border-left: 4px solid #409eff;
}

.test-info p {
  margin: 6px 0;
  text-align: left;
  font-size: 13px;
}

.btn-start {
  background: #67c23a;
  color: white;
  padding: 12px 35px;
  font-size: 16px;
}

.btn-start:hover {
  background: #85ce61;
}

.quiz-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 8px;
  font-size: 13px;
}

.timer,
.score {
  font-weight: 600;
  color: #303133;
}

.progress-bar {
  height: 6px;
  background: #ebeef5;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 30px;
}

.progress {
  height: 100%;
  background: linear-gradient(90deg, #409eff, #66b1ff);
  transition: width 0.3s ease;
}

.question-container {
  animation: slideIn 0.3s ease;
}

.question-number {
  color: #909399;
  margin: 0 0 10px;
  font-size: 13px;
}

.question-text {
  font-size: 18px;
  color: #303133;
  margin: 0 0 15px;
  line-height: 1.6;
}

.word-context {
  background: #ecf5ff;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 15px;
  border-left: 4px solid #409eff;
}

.word-display {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 5px;
  color: #409eff;
}

.word-kana {
  font-size: 13px;
  margin: 0;
  color: #606266;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.option {
  display: flex;
  align-items: center;
  padding: 12px;
  background: #f5f7fa;
  border: 2px solid #e4e7ed;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.option:hover {
  border-color: #409eff;
  background: #ecf5ff;
}

.option.selected {
  background: #ecf5ff;
  border-color: #409eff;
}

.option input[type='radio'] {
  margin-right: 10px;
  cursor: pointer;
}

.option-text {
  flex: 1;
  font-size: 13px;
}

.button-group {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.btn-submit,
.btn-next {
  flex: 1;
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
}

.btn-submit {
  background: #409eff;
  color: white;
}

.btn-submit:hover:not(:disabled) {
  background: #66b1ff;
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-next {
  background: #67c23a;
  color: white;
}

.btn-next:hover {
  background: #85ce61;
}

.explanation {
  margin-top: 15px;
}

.explanation-box {
  padding: 12px;
  border-radius: 8px;
  border-left: 4px solid;
}

.explanation-box.correct {
  background: #f0f9eb;
  border-left-color: #67c23a;
}

.explanation-box.incorrect {
  background: #fef0f0;
  border-left-color: #f56c6c;
}

.explanation-status {
  font-weight: 600;
  margin: 0 0 8px;
  font-size: 13px;
}

.explanation-status.correct {
  color: #67c23a;
}

.explanation-status.incorrect {
  color: #f56c6c;
}

.explanation-text,
.correct-answer {
  margin: 8px 0;
  color: #606266;
  line-height: 1.6;
  font-size: 12px;
}

.test-result {
  animation: slideIn 0.3s ease;
}

.result-header {
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  margin-bottom: 20px;
}

.result-icon {
  font-size: 40px;
  margin: 0;
}

.result-header h2 {
  font-size: 20px;
  margin: 12px 0 8px;
}

.result-score {
  margin: 0 0 12px;
  opacity: 0.9;
  font-size: 12px;
}

.score-display {
  display: flex;
  justify-content: center;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 10px;
}

.final-score {
  font-size: 36px;
  font-weight: 700;
}

.total-score {
  font-size: 16px;
  opacity: 0.8;
}

.accuracy {
  font-size: 14px;
  margin: 0;
}

.result-analysis,
.result-recommendation {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 15px;
}

.result-analysis h3,
.result-recommendation h3 {
  margin-top: 0;
  color: #303133;
  font-size: 15px;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 15px;
}

.analysis-item {
  background: white;
  padding: 10px;
  border-radius: 8px;
  text-align: center;
  border: 1px solid #ebeef5;
}

.analysis-label {
  display: block;
  font-size: 11px;
  color: #909399;
  margin-bottom: 8px;
}

.analysis-value {
  display: block;
  font-size: 20px;
  font-weight: 700;
}

.recommendation-text {
  color: #606266;
  line-height: 1.6;
  margin: 10px 0;
  font-size: 13px;
}

.action-buttons {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.btn-primary,
.btn-secondary {
  flex: 1;
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
}

.btn-primary {
  background: #409eff;
  color: white;
}

.btn-primary:hover {
  background: #66b1ff;
}

.btn-secondary {
  background: white;
  color: #409eff;
  border: 1px solid #409eff;
}

.btn-secondary:hover {
  background: #f0f9ff;
}

.badge {
  font-size: 12px;
  background: #f0f9eb;
  color: #67c23a;
  padding: 4px 8px;
  border-radius: 4px;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes expand {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 500px;
  }
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
}
</style>
