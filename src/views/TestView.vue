<template>
  <section class="view-section test-view">
    <div class="test-title"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <span>智能测试</span> 
      <span class="badge">AI Ready</span>
    </div>

    <div v-if="!testStarted" class="test-intro"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <el-card class="section-card">
        <template #header>
          <div class="card-header">开始测试</div>
        </template>
        <p>通过智能题库检测您的日语水平，获取详细的能力评估报告。</p>
      
      <div class="difficulty-selector">
        <div class="selector-title">选择难度：</div>
        <div class="difficulty-buttons">
          <button
            v-for="level in visibleDifficulties"
            :key="level.value"
            @click="selectedDifficulty = level.value"
            :class="['difficulty-btn', { active: selectedDifficulty === level.value }]"
          >
            {{ level.label }}
          </button>
        </div>
      </div>

      <div class="test-info">
        <p><el-icon class="inline-icon"><Memo /></el-icon> 预计题目数量：10-15 题</p>
        <p><el-icon class="inline-icon"><Timer /></el-icon> 预计耗时：10-15 分钟</p>
        <p><el-icon class="inline-icon"><Aim /></el-icon> 题型：多选题、填空题、听力题</p>
        <p><el-icon class="inline-icon"><Memo /></el-icon> 快捷键：1-8 选难度，Enter 开始测试</p>
      </div>

      <button @click="startTest" class="btn btn-start">
        开始测试
      </button>
      </el-card>

      <el-card v-if="abilityReport && abilityReport.historyCount > 0" class="section-card">
        <template #header>
          <div class="card-header">历史能力概览</div>
        </template>
        <div class="analysis-grid">
          <div class="analysis-item">
            <span class="analysis-label">综合能力分</span>
            <span class="analysis-value" style="color: #409eff;">{{ abilityReport.overallScore }}</span>
          </div>
          <div class="analysis-item">
            <span class="analysis-label">当前等级</span>
            <span class="analysis-value" style="color: #67c23a;">{{ abilityReport.level }}</span>
          </div>
          <div class="analysis-item">
            <span class="analysis-label">趋势</span>
            <span class="analysis-value" style="color: #e6a23c;">
              {{ abilityReport.trend.direction }} ({{ abilityReport.trend.delta }})
            </span>
          </div>
        </div>
        <p class="recommendation-text">{{ abilityReport.summary }}</p>
      </el-card>

      <el-card class="section-card">
        <template #header>
          <div class="card-header">测试历史记录</div>
        </template>
        <div v-if="quizHistory.length === 0" style="padding: 4rem 2rem; text-align: center;">
          <el-empty description="暂无测试记录，快去参加测试吧" />
        </div>
        <el-table v-else :data="quizHistory" style="width: 100%" stripe>
          <el-table-column label="测试时间" min-width="160">
            <template #default="scope">
              {{ formatDateTime(scope.row.completedAt) }}
            </template>
          </el-table-column>
          <el-table-column label="难度" width="80">
            <template #default="scope">
              {{ difficultyText(scope.row.difficulty) }}
            </template>
          </el-table-column>
          <el-table-column label="答对/总数" width="100">
            <template #default="scope">
              {{ scope.row.correctAnswers }} / {{ scope.row.totalQuestions }}
            </template>
          </el-table-column>
          <el-table-column label="准确率" width="100">
            <template #default="scope">
              <el-progress :percentage="scope.row.accuracy" :status="scope.row.accuracy >= 80 ? 'success' : scope.row.accuracy < 60 ? 'exception' : ''" style="width: 8rem" />
            </template>
          </el-table-column>
          <el-table-column label="评级" width="80">
            <template #default="scope">
              <el-tag :type="scope.row.accuracy >= 80 ? 'success' : 'info'">{{ scope.row.level }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="scope">
              <el-button type="primary" link size="small" @click="viewHistoryDetail(scope.row)">详情报告</el-button>
              <el-button type="danger" link size="small" @click="confirmDeleteQuiz(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-wrap" v-if="quizTotal > quizLimit">
          <el-pagination
            v-model:current-page="quizPage"
            :page-size="quizLimit"
            :total="quizTotal"
            layout="prev, pager, next"
            @current-change="(p: number) => loadHistoryAndReport(p)"
          />
        </div>
      </el-card>
    </div>

    <!-- 测试进行中 -->
    <div v-else-if="!testCompleted && currentQuestion"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <div class="quiz-header">
        <div class="timer"><el-icon class="inline-icon"><Timer /></el-icon> {{ formatTime(timeRemaining) }}</div>
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
          <p v-if="shouldShowQuestionKana" class="word-kana">[{{ currentQuestion.word.kana }}]</p>
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
            <span class="option-text">{{ optionLabel(idx) }}. {{ option }}</span>
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
          <button
            type="button"
            @click="exitTest"
            class="btn btn-secondary"
          >
            退出测试
          </button>
        </div>

        <!-- 解析 -->
        <transition name="expand">
          <div v-if="answered" class="explanation">
            <div :class="['explanation-box', isCorrect ? 'correct' : 'incorrect']">
              <p class="explanation-status">
                <template v-if="isCorrect">
                  <el-icon class="inline-icon"><CircleCheck /></el-icon> 回答正确！
                </template>
                <template v-else>
                  <el-icon class="inline-icon"><CircleClose /></el-icon> 回答错误
                </template>
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
    <div v-else-if="testCompleted" class="test-result"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <el-card class="section-card">
        <template #header>
          <div class="card-header">测试完成！</div>
        </template>
        <p class="result-score">最终得分</p>
        <div class="score-display">
          <div class="final-score">{{ score }}</div>
          <div class="total-score">/ {{ totalQuestions }}</div>
        </div>
        <p class="accuracy">正确率: {{ accuracy }}%</p>
      </el-card>

      <el-card class="section-card">
        <template #header>
          <div class="analysis-title">成绩分析</div>
        </template>
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
        <p class="recommendation-text">快捷键：1-4 选答案，Enter/Space 提交或下一题，N 下一题，Esc 退出测试</p>
      </el-card>

      <el-card v-if="abilityReport" class="section-card">
        <template #header>
          <div class="analysis-title">能力报告（结合历史记录）</div>
        </template>
        <div class="analysis-grid">
          <div class="analysis-item">
            <span class="analysis-label">综合能力分</span>
            <span class="analysis-value" style="color: #409eff;">{{ abilityReport.overallScore }}</span>
          </div>
          <div class="analysis-item">
            <span class="analysis-label">能力等级</span>
            <span class="analysis-value" style="color: #67c23a;">{{ abilityReport.level }}</span>
          </div>
          <div class="analysis-item">
            <span class="analysis-label">稳定性</span>
            <span class="analysis-value" style="color: #e6a23c;">{{ abilityReport.consistencyScore }}</span>
          </div>
        </div>
        <p class="recommendation-text">{{ abilityReport.summary }}</p>
        <p v-if="abilityReport.recommendations[0]" class="recommendation-text">
          建议：{{ abilityReport.recommendations[0] }}
        </p>
      </el-card>

      <el-card class="section-card">
        <template #header>
          <div class="recommendation-title">评价与建议</div>
        </template>
        <p class="recommendation-text">{{ recommendation }}</p>
        <div class="action-buttons">
          <button type="button" @click="resetTest" class="btn btn-primary">重新测试</button>
          <button type="button" @click="goToRecite" class="btn btn-secondary">
            去背单词增强基础
          </button>
        </div>
      </el-card>

      <el-card class="section-card">
        <template #header>
          <div class="card-header">测试历史记录</div>
        </template>
        <div v-if="isSubmittingSession && quizHistory.length === 0" style="padding: 4rem 2rem; text-align: center; color: #909399;">
          正在保存测试历史...
        </div>
        <div v-else-if="quizHistory.length === 0" style="padding: 4rem 2rem; text-align: center;">
          <el-empty description="暂无测试记录，完成测试后会自动保存" />
        </div>
        <el-table v-else :data="quizHistory" style="width: 100%" stripe>
          <el-table-column label="测试时间" min-width="160">
            <template #default="scope">
              {{ formatDateTime(scope.row.completedAt) }}
            </template>
          </el-table-column>
          <el-table-column label="难度" width="80">
            <template #default="scope">
              {{ difficultyText(scope.row.difficulty) }}
            </template>
          </el-table-column>
          <el-table-column label="答对/总数" width="100">
            <template #default="scope">
              {{ scope.row.correctAnswers }} / {{ scope.row.totalQuestions }}
            </template>
          </el-table-column>
          <el-table-column label="准确率" width="100">
            <template #default="scope">
              <el-progress :percentage="scope.row.accuracy" :status="scope.row.accuracy >= 80 ? 'success' : scope.row.accuracy < 60 ? 'exception' : ''" style="width: 8rem" />
            </template>
          </el-table-column>
          <el-table-column label="评级" width="80">
            <template #default="scope">
              <el-tag :type="scope.row.accuracy >= 80 ? 'success' : 'info'">{{ scope.row.level }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="scope">
              <el-button type="primary" link size="small" @click="viewHistoryDetail(scope.row)">详情报告</el-button>
              <el-button type="danger" link size="small" @click="confirmDeleteQuiz(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-wrap" v-if="quizTotal > quizLimit">
          <el-pagination
            v-model:current-page="quizPage"
            :page-size="quizLimit"
            :total="quizTotal"
            layout="prev, pager, next"
            @current-change="(p: number) => loadHistoryAndReport(p)"
          />
        </div>
      </el-card>
    </div>

    <!-- 测试详情报告弹窗 -->
    <el-dialog
      v-model="historyDetailVisible"
      title="测试详细报告"
      width="60rem"
    >
      <div v-if="selectedHistoryItem" class="history-detail-body">
        <p style="color: #909399; font-size: 1.3rem; margin-bottom: 2rem;">
          测试时间: {{ formatDateTime(selectedHistoryItem.completedAt) }} | 难度: {{ difficultyText(selectedHistoryItem.difficulty) }}
        </p>

        <el-row :gutter="20" class="history-score-overview">
          <el-col :span="8" class="history-score-col">
            <div style="font-size: 2.4rem; font-weight: bold; color: #409EFF;">{{ selectedHistoryItem.correctAnswers }} / {{ selectedHistoryItem.totalQuestions }}</div>
            <div style="font-size: 1.2rem; color: #909399; margin-top: 0.5rem;">答对题数</div>
          </el-col>
          <el-col :span="8" class="history-score-col history-accuracy-col">
            <el-progress
              class="history-accuracy-progress"
              type="dashboard"
              :percentage="selectedHistoryItem.accuracy"
              :color="selectedHistoryItem.accuracy >= 80 ? '#67C23A' : '#E6A23C'"
              :width="80"
            >
              <template #default="{ percentage }">
                <span style="font-size: 1.6rem; font-weight: bold;">{{ percentage }}%</span>
              </template>
            </el-progress>
            <div style="font-size: 1.2rem; color: #909399; margin-top: 0.5rem;">准确率</div>
          </el-col>
          <el-col :span="8" class="history-score-col">
            <div style="font-size: 2.4rem; font-weight: bold; color: #67C23A;">{{ selectedHistoryItem.level }}</div>
            <div style="font-size: 1.2rem; color: #909399; margin-top: 0.5rem;">评级</div>
          </el-col>
        </el-row>

        <el-row :gutter="20" style="margin-bottom: 2rem; border: 0.1rem solid #EBEEF5; padding: 1.5rem; border-radius: 0.8rem; background: #F8F9FA;">
          <el-col :span="12">
            <div style="font-size: 1.2rem; color: #909399;">整体能力分</div>
            <div style="font-size: 2rem; font-weight: bold; color: #409EFF; margin-top: 0.5rem;">{{ selectedHistoryItem.abilityScore }}</div>
          </el-col>
          <el-col :span="12">
            <div style="font-size: 1.2rem; color: #909399;">趋势</div>
            <div style="font-size: 1.4rem; font-weight: bold; color: #E6A23C; margin-top: 0.5rem;">
              {{ selectedHistoryItem.trendDelta > 0 ? '↑' : selectedHistoryItem.trendDelta < 0 ? '↓' : '→' }}
              {{ Math.abs(selectedHistoryItem.trendDelta) }}
            </div>
          </el-col>
        </el-row>

        <el-row :gutter="20" style="margin-bottom: 2rem; border: 0.1rem solid #EBEEF5; padding: 1.5rem; border-radius: 0.8rem; background: #F8F9FA;">
          <el-col :span="12">
            <div style="font-size: 1.2rem; color: #909399;">稳定性</div>
            <div style="font-size: 2rem; font-weight: bold; color: #409EFF; margin-top: 0.5rem;">{{ selectedHistoryItem.consistencyScore }}</div>
          </el-col>
          <el-col :span="12">
            <div style="font-size: 1.2rem; color: #909399;">速度分</div>
            <div style="font-size: 2rem; font-weight: bold; color: #409EFF; margin-top: 0.5rem;">{{ selectedHistoryItem.speedScore }}</div>
          </el-col>
        </el-row>

        <div style="margin-bottom: 2rem; background-color: #F0F9FF; padding: 1.5rem; border-radius: 0.6rem; border: 0.1rem solid #B3D8FF;">
          <h4 style="margin: 0 0 1rem 0; color: #0A73EB; font-size: 1.4rem;">📊 测试总结</h4>
          <p style="margin: 0; line-height: 1.6; color: #606266; font-size: 1.4rem;">{{ selectedHistoryItem.summary }}</p>
        </div>

        <div v-if="selectedHistoryItem.recommendations.length > 0" style="margin-bottom: 2rem; background-color: #FDF6EC; padding: 1.5rem; border-radius: 0.6rem; border: 0.1rem solid #FAECD8;">
          <h4 style="margin: 0 0 1rem 0; color: #E6A23C; font-size: 1.4rem;">学习建议</h4>
          <p
            v-for="recommendationItem in selectedHistoryItem.recommendations"
            :key="recommendationItem"
            style="margin: 0.6rem 0; line-height: 1.6; color: #606266; font-size: 1.4rem;"
          >
            {{ recommendationItem }}
          </p>
        </div>

        <div v-if="selectedHistoryItem.difficultyBreakdown.length > 0" style="margin-bottom: 2rem; background-color: #FAFAFA; padding: 1.5rem; border-radius: 0.6rem; border: 0.1rem solid #EBEEF5;">
          <h4 style="margin: 0 0 1rem 0; color: #303133; font-size: 1.4rem;">难度表现</h4>
          <div
            v-for="item in selectedHistoryItem.difficultyBreakdown"
            :key="item.difficulty"
            style="display: flex; justify-content: space-between; gap: 1.2rem; color: #606266; font-size: 1.4rem; line-height: 1.8;"
          >
            <span>{{ difficultyText(item.difficulty) }}</span>
            <span>{{ item.accuracy }}% / {{ item.count }} 次</span>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="historyDetailVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Memo, Timer, Aim, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import type { QuizAbilityReport, QuizDifficultyOption, QuizQuestion, QuizSessionRecord } from '@/types'
import { VIEWS } from '@/utils/constants'
import {
  deleteQuizSessionAPI,
  getQuizAbilityReport as getQuizAbilityReportAPI,
  getQuizDifficulties as getQuizDifficultiesAPI,
  getQuizHistory as getQuizHistoryAPI,
  getQuizQuestions as getQuizQuestionsAPI,
  isAuthenticated,
  submitQuizSession as submitQuizSessionAPI
} from '@/api'

const router = useRouter()

// 测试状态
const testStarted = ref(false)
const testCompleted = ref(false)
const currentIndex = ref(0)
const score = ref(0)
const userAnswer = ref('')
const answered = ref(false)
const selectedDifficulty = ref('foundation')
const timeRemaining = ref(600) // 10分钟
const isLoading = ref(false)
const isSubmittingSession = ref(false)
const testStartAt = ref(0)
const answerRecords = ref<Array<{ questionId: string; userAnswer: string; isCorrect: boolean }>>([])
const quizHistory = ref<QuizSessionRecord[]>([])
const quizTotal = ref<number>(0)
const quizPage = ref<number>(1)
const quizLimit = 10
const abilityReport = ref<QuizAbilityReport | null>(null)

// 历史视图状态
const historyDetailVisible = ref(false)
const selectedHistoryItem = ref<QuizSessionRecord | null>(null)

const fallbackDifficulties: QuizDifficultyOption[] = [
  { label: '1. 基础（N4+N5）', value: 'foundation' },
  { label: '2. N3 高频', value: 'n3_high' },
  { label: '3. N3 全量', value: 'n3_full' },
  { label: '4. N2 高频', value: 'n2_high' },
  { label: '5. N2 全量', value: 'n2_full' },
  { label: '6. N1 高频', value: 'n1_high' },
  { label: '7. N1 中频', value: 'n1_mid' },
  { label: '8. N1 低频挑战', value: 'n1_low' }
]
const visibleDifficulties = ref<QuizDifficultyOption[]>(fallbackDifficulties)

const difficultyLabels: Record<string, string> = {
  foundation: '基础（N4+N5）',
  n3_high: 'N3 高频',
  n3_full: 'N3 全量',
  n2_high: 'N2 高频',
  n2_full: 'N2 全量',
  n1_high: 'N1 高频',
  n1_mid: 'N1 中频',
  n1_low: 'N1 低频挑战',
  easy: '基础（旧）',
  medium: '综合（旧 N3）',
  hard: '综合（旧 N2+N1）'
}

const loadQuizDifficulties = async () => {
  try {
    const remoteOptions = await getQuizDifficultiesAPI()
    if (remoteOptions.length > 0) {
      visibleDifficulties.value = remoteOptions
    }
  } catch (error) {
    console.error('Failed to load quiz difficulties:', error)
    visibleDifficulties.value = fallbackDifficulties
  }
}

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

const shouldShowQuestionKana = computed(() => {
  const question = currentQuestion.value
  if (!question?.word?.kana) return false
  return question.questionMode !== 'kana' && !question.question.includes('读音')
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
  if (!isAuthenticated()) {
    ElMessage.warning('请先登录才能参加测试')
    window.dispatchEvent(new CustomEvent('open-login-dialog'))
    return
  }
  
  testStarted.value = true
  testCompleted.value = false
  currentIndex.value = 0
  score.value = 0
  userAnswer.value = ''
  answered.value = false
  answerRecords.value = []
  testStartAt.value = Date.now()
  isLoading.value = true
  
  try {
    // 从 API 获取题目
    questions.value = await getQuizQuestionsAPI(selectedDifficulty.value, 10)
    if (questions.value.length === 0) {
      ElMessage.warning('当前层级暂无可用题目，请切换其他难度')
      testStarted.value = false
      return
    }
    
    // 启动计时器
    startTimer()
  } catch (error) {
    console.error('Failed to load quiz questions:', error)
    ElMessage.error('加载题目失败，请稍后重试')
    testStarted.value = false
  } finally {
    isLoading.value = false
  }
}

const submitAnswer = () => {
  if (answered.value || !currentQuestion.value) return
  answered.value = true
  const correct = isCorrect.value
  if (correct) {
    score.value++
  }
  answerRecords.value.push({
    questionId: currentQuestion.value.id,
    userAnswer: userAnswer.value,
    isCorrect: correct
  })
}

const finishTest = async () => {
  if (testCompleted.value || isSubmittingSession.value) return
  testCompleted.value = true
  if (timerInterval) {
    clearInterval(timerInterval)
  }

  if (!isAuthenticated() || totalQuestions.value === 0) {
    return
  }

  isSubmittingSession.value = true
  try {
    const durationSeconds = Math.max(0, Math.floor((Date.now() - testStartAt.value) / 1000))
    const response = await submitQuizSessionAPI({
      difficulty: selectedDifficulty.value,
      totalQuestions: totalQuestions.value,
      correctAnswers: score.value,
      durationSeconds,
      answers: answerRecords.value
    })
    abilityReport.value = response.report
    quizPage.value = 1
    await loadHistoryAndReport()
  } catch (error) {
    console.error('Failed to submit quiz session:', error)
    const message = error instanceof Error ? error.message : '未知错误'
    ElMessage.warning(`历史记录保存失败：${message}`)
  } finally {
    isSubmittingSession.value = false
  }
}

const confirmDeleteQuiz = async (item: QuizSessionRecord) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条测试记录吗？此操作不可恢复。',
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteQuizSessionAPI(String(item.id))
    quizHistory.value = quizHistory.value.filter(s => s.id !== item.id)
    if (selectedHistoryItem.value?.id === item.id) {
      historyDetailVisible.value = false
      selectedHistoryItem.value = null
    }
    ElMessage.success('测试记录已删除')
    quizTotal.value = Math.max(0, quizTotal.value - 1)
    if (quizHistory.value.length === 0 && quizPage.value > 1) {
      quizPage.value--
      await loadHistoryAndReport()
    }
  } catch (error: any) {
    if (error?.toString().includes('cancel')) return
    ElMessage.error(error.message || '删除失败')
  }
}

const nextQuestion = async () => {
  currentIndex.value++
  userAnswer.value = ''
  answered.value = false
  
  if (currentIndex.value >= totalQuestions.value) {
    await finishTest()
  }
}

const resetTest = () => {
  testStarted.value = false
  testCompleted.value = false
  currentIndex.value = 0
  score.value = 0
  userAnswer.value = ''
  answered.value = false
  timeRemaining.value = 600
  answerRecords.value = []
  isSubmittingSession.value = false
  if (timerInterval) {
    clearInterval(timerInterval)
  }
}

const exitTest = async () => {
  if (!testStarted.value || testCompleted.value) {
    resetTest()
    return
  }

  try {
    await ElMessageBox.confirm(
      '退出后本次未完成测试不会保存，确定退出吗？',
      '退出测试',
      {
        confirmButtonText: '退出',
        cancelButtonText: '继续测试',
        type: 'warning'
      }
    )
    resetTest()
  } catch {
    // 用户取消，保持当前测试状态
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
      finishTest()
    }
  }, 1000) as unknown as number
}

const difficultyText = (value: string): string => {
  return difficultyLabels[value] || value
}

const viewHistoryDetail = (item: QuizSessionRecord) => {
  selectedHistoryItem.value = item
  historyDetailVisible.value = true
}

const formatDateTime = (timestamp: number): string => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString()
}

const optionLabel = (idx: number): string => {
  const labels = ['A', 'B', 'C', 'D']
  return labels[idx] || String(idx + 1)
}

const goToRecite = () => {
  // 通过路由内切换，避免触发浏览器级跳转。
  router.push({ name: VIEWS.RECITE })
}

const selectOptionByIndex = (index: number) => {
  if (!currentQuestion.value || answered.value) return
  const option = currentQuestion.value.options[index]
  if (option) {
    userAnswer.value = option
  }
}

const handleKeyboard = (event: KeyboardEvent) => {
  const target = event.target as HTMLElement | null
  if (target) {
    const tagName = target.tagName.toLowerCase()
    if (tagName === 'input' || tagName === 'textarea' || target.isContentEditable) {
      return
    }
  }

  if (!testStarted.value) {
    if (event.code === 'Digit1') selectedDifficulty.value = 'foundation'
    if (event.code === 'Digit2') selectedDifficulty.value = 'n3_high'
    if (event.code === 'Digit3') selectedDifficulty.value = 'n3_full'
    if (event.code === 'Digit4') selectedDifficulty.value = 'n2_high'
    if (event.code === 'Digit5') selectedDifficulty.value = 'n2_full'
    if (event.code === 'Digit6') selectedDifficulty.value = 'n1_high'
    if (event.code === 'Digit7') selectedDifficulty.value = 'n1_mid'
    if (event.code === 'Digit8') selectedDifficulty.value = 'n1_low'
    if (event.code === 'Enter') {
      event.preventDefault()
      void startTest()
    }
    return
  }

  if (testCompleted.value) {
    if (event.code === 'KeyR') {
      event.preventDefault()
      resetTest()
    }
    if (event.code === 'KeyB') {
      event.preventDefault()
      goToRecite()
    }
    return
  }

  if (!currentQuestion.value) return

  if (event.code === 'Digit1') selectOptionByIndex(0)
  if (event.code === 'Digit2') selectOptionByIndex(1)
  if (event.code === 'Digit3') selectOptionByIndex(2)
  if (event.code === 'Digit4') selectOptionByIndex(3)

  if (event.code === 'Enter' || event.code === 'Space') {
    event.preventDefault()
    if (!answered.value) {
      submitAnswer()
    } else {
      void nextQuestion()
    }
  }

  if (event.code === 'KeyN' && answered.value) {
    event.preventDefault()
    void nextQuestion()
  }

  if (event.code === 'Escape') {
    event.preventDefault()
    void exitTest()
  }
}

const loadHistoryAndReport = async (page?: number) => {
  if (!isAuthenticated()) {
    quizHistory.value = []
    abilityReport.value = null
    return
  }
  if (page !== undefined) quizPage.value = page
  const skip = (quizPage.value - 1) * quizLimit
  const [historyResult, reportResult] = await Promise.allSettled([
    getQuizHistoryAPI(skip, quizLimit),
    getQuizAbilityReportAPI(20)
  ])

  if (historyResult.status === 'fulfilled') {
    quizHistory.value = historyResult.value.items
    quizTotal.value = historyResult.value.total
  } else {
    console.error('Failed to load quiz history:', historyResult.reason)
  }

  if (reportResult.status === 'fulfilled') {
    abilityReport.value = reportResult.value
  } else {
    console.error('Failed to load quiz report:', reportResult.reason)
  }
}

const handleLogin = () => {
  loadHistoryAndReport()
}

const handleLogout = () => {
  quizHistory.value = []
  abilityReport.value = null
}

onMounted(() => {
  loadQuizDifficulties()
  loadHistoryAndReport()
  window.addEventListener('keydown', handleKeyboard)
  window.addEventListener('yomii:login', handleLogin)
  window.addEventListener('yomii:logout', handleLogout)
})

onUnmounted(() => {
  if (timerInterval) {
    clearInterval(timerInterval)
  }
  window.removeEventListener('keydown', handleKeyboard)
  window.removeEventListener('yomii:login', handleLogin)
  window.removeEventListener('yomii:logout', handleLogout)
})
</script>

<style scoped>
.test-title {
  color: #8B4513;
  font-size: 2.4rem;
  margin-bottom: 1rem;
}

.badge {
  font-size: 1.2rem;
  background: #f0f9eb;
  color: #000000;
  padding: 0.4rem 0.8rem;
  border-radius: 0.4rem;
  margin-left: 0.8rem;
}

.inline-icon {
  vertical-align: middle;
  margin-right: 0.4rem;
}

.test-intro {
  max-width: 95%;
  margin: 0 auto;
  text-align: center;
}

.test-intro h2 {
  font-size: 2rem;
  margin-bottom: 1rem;
  color: #000000;
}

.test-intro p {
  color: #333333;
  line-height: 1.6;
  margin-bottom: 2rem;
  font-size: 1.4rem;
}

.section-card {
  margin-bottom: 2rem;
}

.section-card p {
  font-size: 1.5rem;
}

.card-header {
  font-size: 1.8rem;
  font-weight: 600;
  color: #000000;
}

.difficulty-selector {
  margin: 2.5rem 0;
  padding: 1.5rem;
  background: #f5f7fa;
  border-radius: 0.8rem;
}

.difficulty-selector h3 {
  margin-top: 0;
  color: #000000;
  font-size: 1.4rem;
}

.difficulty-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(14.8rem, 1fr));
  justify-content: center;
  gap: 1rem;
}

.difficulty-btn {
  min-height: 4.6rem;
  padding: 1rem 1.2rem;
  background: white;
  border: 0.2rem solid #dcdfe6;
  border-radius: 0.6rem;
  cursor: pointer;
  font-size: 1.3rem;
  line-height: 1.35;
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

.selector-title {
  font-size: 1.4rem;
  font-weight: 600;
  color: #000000;
  margin-bottom: 1rem;
}

.test-info {
  background: #ecf5ff;
  padding: 1.2rem;
  border-radius: 0.8rem;
  margin-bottom: 2rem;
  border-left: 0.4rem solid #409eff;
}

.test-info p {
  margin: 0.6rem 0;
  text-align: left;
  font-size: 1.3rem;
}

.btn-start {
  background: #67c23a;
  color: white;
  padding: 1.2rem 3.5rem;
  font-size: 1.6rem;
  border: none;
  border-radius: 0.4rem;
}

.btn-start:hover {
  background: #85ce61;
}

.quiz-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f5f7fa;
  border-radius: 0.8rem;
  font-size: 1.3rem;
}

.timer,
.score {
  font-weight: 600;
  color: #000000;
}

.progress-bar {
  height: 0.6rem;
  background: #ebeef5;
  border-radius: 0.3rem;
  overflow: hidden;
  margin-bottom: 3rem;
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
  color: #333333;
  margin: 0 0 1.2rem;
  font-size: 1.6rem;
  font-weight: 600;
}

.question-text {
  font-size: 2.4rem;
  color: #000000;
  margin: 0 0 2rem;
  line-height: 1.8;
  font-weight: 600;
}

.word-context {
  background: #ecf5ff;
  padding: 1.2rem;
  border-radius: 0.8rem;
  margin-bottom: 1.5rem;
  border-left: 0.4rem solid #409eff;
}

.word-display {
  font-size: 2.6rem;
  font-weight: 700;
  margin: 0 0 0.8rem;
  color: #409eff;
}

.word-kana {
  font-size: 1.6rem;
  margin: 0;
  color: #333333;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.option {
  display: flex;
  align-items: center;
  padding: 1.6rem;
  background: #f5f7fa;
  border: 0.2rem solid #e4e7ed;
  border-radius: 0.6rem;
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
  margin-right: 1.2rem;
  cursor: pointer;
}

.option-text {
  flex: 1;
  font-size: 1.5rem;
  font-weight: 500;
}

.button-group {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.btn-submit,
.btn-next {
  flex: 1;
  padding: 1.4rem 2.8rem;
  border: none;
  border-radius: 0.6rem;
  font-size: 1.6rem;
  cursor: pointer;
  font-weight: 600;
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
  margin-top: 1.5rem;
}

.explanation-box {
  padding: 1.2rem;
  border-radius: 0.8rem;
  border-left: 0.4rem solid;
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
  margin: 0 0 0.8rem;
  font-size: 1.3rem;
}

.explanation-status.correct {
  color: #67c23a;
}

.explanation-status.incorrect {
  color: #f56c6c;
}

.explanation-text,
.correct-answer {
  margin: 0.8rem 0;
  color: #333333;
  line-height: 1.6;
  font-size: 1.2rem;
}

.test-result {
  animation: slideIn 0.3s ease;
}

.result-header {
  text-align: center;
  padding: 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 1.2rem;
  color: white;
  margin-bottom: 2rem;
}

.result-icon {
  font-size: 4rem;
  margin: 0;
}

.result-header h2 {
  font-size: 2rem;
  margin: 1.2rem 0 0.8rem;
}

.result-score {
  margin: 0 0 1.2rem;
  opacity: 0.9;
  font-size: 1.2rem;
}

.score-display {
  display: flex;
  justify-content: center;
  align-items: baseline;
  gap: 0.8rem;
  margin-bottom: 1rem;
}

.final-score {
  font-size: 4.8rem;
  font-weight: 700;
}

.total-score {
  font-size: 2rem;
  opacity: 0.8;
}

.accuracy {
  font-size: 1.4rem;
  margin: 0;
}

.analysis-title,
.recommendation-title {
  font-size: 1.6rem;
  font-weight: 600;
  color: #000000;
  margin-bottom: 1.5rem;
}

.result-analysis,
.result-recommendation {
  background: #f5f7fa;
  padding: 1.2rem;
  border-radius: 0.8rem;
  margin-bottom: 1.5rem;
}

.result-analysis h3,
.result-recommendation h3 {
  margin-top: 0;
  color: #000000;
  font-size: 1.5rem;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-top: 1.5rem;
}

.analysis-item {
  background: white;
  padding: 1rem;
  border-radius: 0.8rem;
  text-align: center;
  border: 0.1rem solid #ebeef5;
}

.analysis-label {
  display: block;
  font-size: 1.1rem;
  color: #333333;
  margin-bottom: 0.8rem;
}

.analysis-value {
  display: blo8k;
  font-size: 2rem;
  font-weight: 700;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.history-item {
  background: #f5f7fa;
  border: 0.1rem solid #ebeef5;
  border-radius: 0.8rem;
  padding: 1rem;
}

.history-main {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
  font-size: 1.3rem;
  color: #303133;
}

.history-sub {
  margin-top: 0.6rem;
  font-size: 1.2rem;
  color: #909399;
}

.history-score-overview {
  margin-bottom: 2rem;
  border: 0.1rem solid #ebeef5;
  padding: 1.5rem;
  border-radius: 0.8rem;
  background: #fafafa;
}

.history-score-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.history-accuracy-col {
  border-left: 0.1rem solid #ebeef5;
  border-right: 0.1rem solid #ebeef5;
}

.history-accuracy-progress {
  align-self: center;
  flex: 0 0 auto;
}

.history-accuracy-progress :deep(.el-progress__text) {
  left: 50%;
  width: auto;
  min-width: 0;
  transform: translate(-50%, -50%);
}

.recommendation-text {
  color: #333333;
  line-height: 1.6;
  margin: 1rem 0;
  font-size: 1.3rem;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn-primary,
.btn-secondary {
  flex: 1;
  padding: 1rem 2rem;
  border: none;
  border-radius: 0.6rem;
  font-size: 1.3rem;
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
  border: 0.1rem solid #409eff;
}

.btn-secondary:hover {
  background: #f0f9ff;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(1rem);
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
    max-height: 50rem;
  }
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  padding: 1.6rem 0 0.8rem;
}
</style>
