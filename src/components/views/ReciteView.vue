<template>
  <section class="recite-view">
    <!-- 学习计划管理区 -->
    <el-card class="plan-card">
      <template #header>
        <div class="card-header">
          <span>学习计划</span>
          <el-button type="primary" size="small" @click="showPlanModal = true">⚙️ 管理计划</el-button>
        </div>
      </template>
      
      <el-row :gutter="20" v-if="currentPlan">
        <el-col :xs="24" :sm="8">
          <div class="plan-item-new">
            <div class="plan-label">当前计划</div>
            <div class="plan-value">{{ currentPlan.name }}</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="plan-item-new">
            <div class="plan-label">每日目标</div>
            <div class="plan-value">{{ currentPlan.dailyGoal }} 个单词</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="plan-item-new">
            <div class="plan-label">复习比例</div>
            <div class="plan-value">{{ Math.round(currentPlan.reviewRatio * 100) }}%</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 选项卡 -->
    <el-tabs v-model="activeTab" class="study-tabs">
      <el-tab-pane label="📚 背单词" name="learn">
      <template v-if="learnWords.length > 0 && currentWord">
        <h1>背单词 <span class="counter">{{ currentLearnIndex + 1 }} / {{ learnWords.length }}</span></h1>
        
        <!-- 进度条 -->
        <div class="progress-bar">
          <div class="progress" :style="{ width: learnProgressPercent + '%' }"></div>
        </div>

        <!-- 闪卡 -->
        <div class="flashcard">
          <!-- 正面 -->
          <div class="card-face">
            <div class="card-content">
              <h2 class="word-text">{{ currentWord.word }}</h2>
              <p class="kana-text" v-if="showLearningMeaning">[{{ currentWord.kana }}]</p>
            </div>

            <!-- 翻转提示 -->
            <div v-if="!showLearningMeaning" class="flip-hint" @click="toggleLearningCard">
              <p>点击或按空格键</p>
              <p class="hint-text">查看释义</p>
            </div>

            <!-- 背面 -->
            <transition name="flip">
              <div v-if="showLearningMeaning" class="card-back">
                <hr class="divider" />
                <p class="meaning-text">{{ currentWord.meaning }}</p>
                <p v-if="currentWord.partOfSpeech" class="pos">
                  {{ currentWord.partOfSpeech }}
                </p>
                <div v-if="currentWord.example" class="example-box">
                  <p class="example-label">例句：</p>
                  <p class="example-text">{{ currentWord.example }}</p>
                </div>
              </div>
            </transition>
          </div>

          <!-- 学习状态信息 -->
          <div v-if="showLearningMeaning" class="study-info">
            <p>选择您对这个词汇的掌握程度</p>
          </div>

          <!-- 操作按钮 -->
          <div class="actions">
            <button v-if="!showLearningMeaning" @click="toggleLearningCard" class="btn btn-primary">
              查看释义 (Space)
            </button>
            <template v-else>
              <button @click="nextLearnWord('unknown')" class="btn btn-unknown">
                ❌ 不认识
              </button>
              <button @click="nextLearnWord('fuzzy')" class="btn btn-fuzzy">
                🤔 模糊
              </button>
              <button @click="nextLearnWord('known')" class="btn btn-known">
                ✓ 认识
              </button>
            </template>
          </div>

          <!-- 快捷键提示 -->
          <div class="keyboard-hints">
            <span v-if="!showLearningMeaning" class="hint">按 Space 翻转卡片</span>
            <template v-else>
              <span class="hint">1: 不认识 | 2: 模糊 | 3: 认识</span>
            </template>
          </div>
        </div>
      </template>

      <!-- 背单词完成状态 -->
      <div v-else-if="learnSessionCompleted" class="completion-state">
        <div class="completion-content">
          <p class="completion-icon">🎉</p>
          <p class="completion-text">恭喜！今天的背单词任务已完成</p>
          <div class="button-group">
            <button @click="requestAddMore" class="btn btn-primary">🚀 加量学习</button>
            <button @click="resetLearnSession" class="btn btn-secondary">再来一遍</button>
          </div>
        </div>

        <!-- 学习统计 -->
        <div class="stats-summary">
          <h3>本轮学习总结</h3>
          <div class="stats-grid">
            <div class="stat">
              <span class="stat-label">掌握</span>
              <span class="stat-number known">{{ learnSessionStats.known }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">模糊</span>
              <span class="stat-number fuzzy">{{ learnSessionStats.fuzzy }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">未掌握</span>
              <span class="stat-number unknown">{{ learnSessionStats.unknown }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 没有单词 -->
      <div v-else class="empty-state">
        <p class="empty-icon">📭</p>
        <p class="empty-text">暂无待背诵的单词</p>
        <button @click="loadLearnWords" class="btn btn-primary">重新加载</button>
      </div>
    </el-tab-pane>

    <!-- 复习部分 -->
    <el-tab-pane label="📝 复习" name="review" class="tab-content">
      <template v-if="reviewWords.length > 0 && currentReviewWord">
        <h1>复习 <span class="counter">{{ currentReviewIndex + 1 }} / {{ reviewWords.length }}</span></h1>
        
        <!-- 进度条 -->
        <div class="progress-bar">
          <div class="progress" :style="{ width: reviewProgressPercent + '%' }"></div>
        </div>

        <!-- 闪卡 -->
        <div class="flashcard">
          <!-- 正面 -->
          <div class="card-face">
            <div class="card-content">
              <h2 class="word-text">{{ currentReviewWord.word }}</h2>
              <p class="kana-text" v-if="showReviewMeaning">[{{ currentReviewWord.kana }}]</p>
            </div>

            <!-- 翻转提示 -->
            <div v-if="!showReviewMeaning" class="flip-hint" @click="toggleReviewCard">
              <p>点击或按空格键</p>
              <p class="hint-text">查看释义</p>
            </div>

            <!-- 背面 -->
            <transition name="flip">
              <div v-if="showReviewMeaning" class="card-back">
                <hr class="divider" />
                <p class="meaning-text">{{ currentReviewWord.meaning }}</p>
                <p v-if="currentReviewWord.partOfSpeech" class="pos">
                  {{ currentReviewWord.partOfSpeech }}
                </p>
                <div v-if="currentReviewWord.example" class="example-box">
                  <p class="example-label">例句：</p>
                  <p class="example-text">{{ currentReviewWord.example }}</p>
                </div>
              </div>
            </transition>
          </div>

          <!-- 学习状态信息 -->
          <div v-if="showReviewMeaning" class="study-info">
            <p>选择您对这个词汇的掌握程度</p>
          </div>

          <!-- 操作按钮 -->
          <div class="actions">
            <button v-if="!showReviewMeaning" @click="toggleReviewCard" class="btn btn-primary">
              查看释义 (Space)
            </button>
            <template v-else>
              <button @click="nextReviewWord('unknown')" class="btn btn-unknown">
                ❌ 不认识
              </button>
              <button @click="nextReviewWord('fuzzy')" class="btn btn-fuzzy">
                🤔 模糊
              </button>
              <button @click="nextReviewWord('known')" class="btn btn-known">
                ✓ 认识
              </button>
            </template>
          </div>

          <!-- 快捷键提示 -->
          <div class="keyboard-hints">
            <span v-if="!showReviewMeaning" class="hint">按 Space 翻转卡片</span>
            <template v-else>
              <span class="hint">1: 不认识 | 2: 模糊 | 3: 认识</span>
            </template>
          </div>
        </div>
      </template>

      <!-- 复习完成状态 -->
      <div v-else-if="reviewSessionCompleted" class="completion-state">
        <div class="completion-content">
          <p class="completion-icon">✨</p>
          <p class="completion-text">恭喜！今天的复习任务已完成</p>
          <button @click="resetReviewSession" class="btn btn-primary" style="margin-top: 20px;">
            再复习一遍
          </button>
        </div>

        <!-- 复习统计 -->
        <div class="stats-summary">
          <h3>本轮复习总结</h3>
          <div class="stats-grid">
            <div class="stat">
              <span class="stat-label">掌握</span>
              <span class="stat-number known">{{ reviewSessionStats.known }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">模糊</span>
              <span class="stat-number fuzzy">{{ reviewSessionStats.fuzzy }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">未掌握</span>
              <span class="stat-number unknown">{{ reviewSessionStats.unknown }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 没有复习单词 -->
      <div v-else class="empty-state">
        <p class="empty-icon">📭</p>
        <p class="empty-text">暂无复习单词</p>
        <button @click="loadReviewWords" class="btn btn-primary">重新加载</button>
      </div>
    </el-tab-pane>

    <!-- 学习计划管理模态框 -->
    <div v-if="showPlanModal" class="modal-overlay" @click.self="showPlanModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>学习计划设置</h3>
          <button @click="showPlanModal = false" class="close-btn">✕</button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label>计划名称</label>
            <input v-model="planFormData.name" type="text" placeholder="输入计划名称" />
          </div>

          <div class="form-group">
            <label>每日背诵目标</label>
            <div class="input-with-info">
              <input v-model.number="planFormData.dailyGoal" type="number" min="1" max="100" />
              <span class="info">个单词/天</span>
            </div>
          </div>

          <div class="form-group">
            <label>复习比例</label>
            <div class="input-with-info">
              <input v-model.number="planFormData.reviewRatio" type="number" min="0" max="1" step="0.1" />
              <span class="info">{{ Math.round(planFormData.reviewRatio * 100) }}%</span>
            </div>
          </div>

          <div class="button-group">
            <button @click="savePlan" class="btn btn-primary">保存计划</button>
            <button @click="showPlanModal = false" class="btn btn-secondary">取消</button>
          </div>
        </div>
      </div>
    </div>
  </el-tabs>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import type { Word } from '@/types'
import { getLearnWords, getReviewWords, requestAddMore as requestAddMoreAPI, saveLearningSession } from '@/api'
import { useWordProgress, useStudyStats, useStudyPlan } from '@/composables/useLocalStorage'

// 标签
const activeTab = ref<'learn' | 'review'>('learn')

// 学习计划管理
const { currentPlan, updatePlan, addPlan, activatePlan } = useStudyPlan()
const showPlanModal = ref(false)
const planFormData = reactive({
  name: '',
  dailyGoal: 10,
  reviewRatio: 0.5
})

// 背单词数据
const learnWords = ref<Word[]>([])
const currentLearnIndex = ref(0)
const showLearningMeaning = ref(false)
const learnSessionCompleted = ref(false)
const learnSessionStats = reactive({
  known: 0,
  fuzzy: 0,
  unknown: 0
})

// 复习数据
const reviewWords = ref<Word[]>([])
const currentReviewIndex = ref(0)
const showReviewMeaning = ref(false)
const reviewSessionCompleted = ref(false)
const reviewSessionStats = reactive({
  known: 0,
  fuzzy: 0,
  unknown: 0
})

// 其他功能
const { updateProgress } = useWordProgress()
const { incrementRecited } = useStudyStats()
const isLoading = ref(false)

// 计算属性
const currentWord = computed(() => learnWords.value[currentLearnIndex.value] || null)
const currentReviewWord = computed(() => reviewWords.value[currentReviewIndex.value] || null)

const learnProgressPercent = computed(() => {
  if (learnWords.value.length === 0) return 0
  return (currentLearnIndex.value / learnWords.value.length) * 100
})

const reviewProgressPercent = computed(() => {
  if (reviewWords.value.length === 0) return 0
  return (currentReviewIndex.value / reviewWords.value.length) * 100
})

// 背单词相关方法
const toggleLearningCard = () => {
  showLearningMeaning.value = !showLearningMeaning.value
}

const nextLearnWord = async (status: 'unknown' | 'fuzzy' | 'known') => {
  if (currentWord.value) {
    updateProgress(currentWord.value.id, status)
    incrementRecited()
    learnSessionStats[status]++

    showLearningMeaning.value = false
    currentLearnIndex.value++

    if (currentLearnIndex.value >= learnWords.value.length) {
      learnSessionCompleted.value = true
      // 保存学习轮次
      if (currentPlan.value) {
        const today = new Date().toISOString().split('T')[0] || ''
        await saveLearningSession(currentPlan.value.id, {
          planId: currentPlan.value.id,
          date: today,
          learnedWords: learnWords.value.map(w => w.id),
          reviewedWords: [],
          sessionStats: { 
            knownCount: learnSessionStats.known,
            fuzzyCount: learnSessionStats.fuzzy,
            unknownCount: learnSessionStats.unknown
          },
          completedAt: Date.now()
        })
      }
    }
  }
}

const loadLearnWords = async () => {
  isLoading.value = true
  try {
    if (currentPlan.value) {
      learnWords.value = await getLearnWords(currentPlan.value.id)
    }
  } catch (error) {
    console.error('Failed to load learn words:', error)
    learnWords.value = []
  } finally {
    isLoading.value = false
  }
}

const resetLearnSession = async () => {
  learnSessionStats.known = 0
  learnSessionStats.fuzzy = 0
  learnSessionStats.unknown = 0
  currentLearnIndex.value = 0
  showLearningMeaning.value = false
  learnSessionCompleted.value = false
  await loadLearnWords()
}

// 复习相关方法
const toggleReviewCard = () => {
  showReviewMeaning.value = !showReviewMeaning.value
}

const nextReviewWord = async (status: 'unknown' | 'fuzzy' | 'known') => {
  if (currentReviewWord.value) {
    updateProgress(currentReviewWord.value.id, status)
    incrementRecited()
    reviewSessionStats[status]++

    showReviewMeaning.value = false
    currentReviewIndex.value++

    if (currentReviewIndex.value >= reviewWords.value.length) {
      reviewSessionCompleted.value = true
    }
  }
}

const loadReviewWords = async () => {
  isLoading.value = true
  try {
    if (currentPlan.value) {
      reviewWords.value = await getReviewWords(currentPlan.value.id)
    }
  } catch (error) {
    console.error('Failed to load review words:', error)
    reviewWords.value = []
  } finally {
    isLoading.value = false
  }
}

const resetReviewSession = async () => {
  reviewSessionStats.known = 0
  reviewSessionStats.fuzzy = 0
  reviewSessionStats.unknown = 0
  currentReviewIndex.value = 0
  showReviewMeaning.value = false
  reviewSessionCompleted.value = false
  await loadReviewWords()
}

// 加量学习
const requestAddMore = async () => {
  try {
    if (currentPlan.value) {
      const result = await requestAddMoreAPI(currentPlan.value.id, 5)
      if (result.success) {
        learnWords.value.push(...result.moreWords)
        learnSessionCompleted.value = false
      }
    }
  } catch (error) {
    console.error('加量学习失败:', error)
  }
}

// 学习计划管理
const savePlan = async () => {
  if (!planFormData.name.trim()) {
    alert('请输入计划名称')
    return
  }

  if (currentPlan.value) {
    updatePlan(currentPlan.value.id, {
      name: planFormData.name,
      dailyGoal: planFormData.dailyGoal,
      reviewRatio: planFormData.reviewRatio
    })
  } else {
    const newPlan = addPlan(planFormData.name, planFormData.dailyGoal, planFormData.reviewRatio)
    activatePlan(newPlan.id)
  }

  showPlanModal.value = false
  // 重新加载单词
  await loadLearnWords()
  await loadReviewWords()
}

// 键盘快捷键
const handleKeyboard = (event: KeyboardEvent) => {
  if (activeTab.value === 'learn') {
    if (event.code === 'Space') {
      event.preventDefault()
      toggleLearningCard()
    } else if (showLearningMeaning.value && event.code === 'Digit1') {
      nextLearnWord('unknown')
    } else if (showLearningMeaning.value && event.code === 'Digit2') {
      nextLearnWord('fuzzy')
    } else if (showLearningMeaning.value && event.code === 'Digit3') {
      nextLearnWord('known')
    }
  } else if (activeTab.value === 'review') {
    if (event.code === 'Space') {
      event.preventDefault()
      toggleReviewCard()
    } else if (showReviewMeaning.value && event.code === 'Digit1') {
      nextReviewWord('unknown')
    } else if (showReviewMeaning.value && event.code === 'Digit2') {
      nextReviewWord('fuzzy')
    } else if (showReviewMeaning.value && event.code === 'Digit3') {
      nextReviewWord('known')
    }
  }
}

onMounted(() => {
  loadLearnWords()
  loadReviewWords()
  
  // 初始化计划表单
  if (currentPlan.value) {
    planFormData.name = currentPlan.value.name
    planFormData.dailyGoal = currentPlan.value.dailyGoal
    planFormData.reviewRatio = currentPlan.value.reviewRatio
  }

  window.addEventListener('keydown', handleKeyboard)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyboard)
})
</script>

<style scoped>
.recite-view {
  max-width: 900px;
  margin: 0 auto;
}

/* 学习计划管理区 */
.plan-management {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 30px;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.plan-header h2 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.plan-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.plan-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: white;
  border-radius: 6px;
}

.plan-item .label {
  color: #333333;
  font-weight: 500;
}

.plan-item .value {
  color: #409eff;
  font-weight: 600;
}

/* 选项卡 */
.tabs-container {
  display: flex;
  gap: 10px;
  margin-bottom: 30px;
  border-bottom: 2px solid #ebeef5;
}

.tab {
  padding: 12px 20px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
  color: #333333;
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
}

.tab:hover {
  color: #409eff;
}

.tab.active {
  color: #409eff;
  border-bottom-color: #409eff;
}

.tab-content {
  animation: fadeIn 0.3s ease;
}

h1 {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #000000;
}

.counter {
  font-size: 18px;
  color: #333333;
  font-weight: normal;
}

.progress-bar {
  height: 8px;
  background: #ebeef5;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 40px;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}

.progress {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.flashcard {
  position: relative;
  margin: 40px 0;
  perspective: 1000px;
}

.card-face {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  padding: 60px 40px;
  min-height: 350px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
  position: relative;
}

.card-face:hover {
  transform: translateY(-8px);
  box-shadow: 0 16px 48px rgba(102, 126, 234, 0.3);
}

.card-content {
  text-align: center;
}

.word-text {
  font-size: 38px;
  margin: 0 0 8px;
  font-weight: 700;
}

.kana-text {
  font-size: 20px;
  margin: 0;
  opacity: 0.9;
}

.flip-hint {
  margin-top: 30px;
  text-align: center;
  opacity: 0.8;
  animation: bounce 2s infinite;
}

.flip-hint p {
  margin: 5px 0;
  font-size: 14px;
}

.hint-text {
  font-size: 12px;
  opacity: 0.7;
}

.card-back {
  animation: fadeIn 0.3s ease;
}

.divider {
  border: none;
  border-top: 1px solid rgba(255, 255, 255, 0.3);
  margin: 20px 0;
}

.meaning-text {
  font-size: 24px;
  margin: 0 0 10px;
  font-weight: 600;
}

.pos {
  font-size: 14px;
  opacity: 0.8;
  margin: 0 0 20px;
  font-style: italic;
}

.example-box {
  background: rgba(255, 255, 255, 0.1);
  padding: 15px;
  border-radius: 8px;
  margin-top: 20px;
}

.example-label {
  font-size: 12px;
  margin: 0 0 8px;
  opacity: 0.8;
}

.example-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
}

.study-info {
  text-align: center;
  margin: 20px 0;
  color: #222222;
  font-size: 14px;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 30px;
  flex-wrap: wrap;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.btn:active {
  transform: translateY(1px);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-primary:hover {
  background: linear-gradient(135deg, #7b92f4 0%, #8b5ac8 100%);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
  transform: translateY(-2px);
}

.btn-secondary {
  background: #f0f2f5;
  color: #333;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.btn-secondary:hover {
  background: #e4e7eb;
}

.btn-small {
  padding: 8px 16px;
  font-size: 14px;
}

.btn-unknown {
  background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
  color: white;
  flex: 1;
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.3);
}

.btn-unknown:hover {
  background: linear-gradient(135deg, #f78989 0%, #fb9d9d 100%);
  box-shadow: 0 6px 16px rgba(245, 108, 108, 0.4);
  transform: translateY(-2px);
}

.btn-fuzzy {
  background: linear-gradient(135deg, #e6a23c 0%, #ebb563 100%);
  color: white;
  flex: 1;
  box-shadow: 0 4px 12px rgba(230, 162, 60, 0.3);
}

.btn-fuzzy:hover {
  background: linear-gradient(135deg, #ebb563 0%, #f0c282 100%);
  box-shadow: 0 6px 16px rgba(230, 162, 60, 0.4);
  transform: translateY(-2px);
}

.btn-known {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  color: white;
  flex: 1;
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
}

.btn-known:hover {
  background: linear-gradient(135deg, #85ce61 0%, #a4d885 100%);
  box-shadow: 0 6px 16px rgba(103, 194, 58, 0.4);
  transform: translateY(-2px);
}

.keyboard-hints {
  text-align: center;
  margin-top: 20px;
  color: #333333;
  font-size: 12px;
}

.hint {
  display: inline-block;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  margin: 0 5px;
}

.completion-state {
  text-align: center;
  padding: 60px 20px;
}

.completion-content {
  margin-bottom: 40px;
}

.completion-icon {
  font-size: 60px;
  margin: 0;
}

.completion-text {
  font-size: 24px;
  color: #000000;
  margin: 20px 0 0;
  font-weight: 500;
}

.button-group {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 20px;
  flex-wrap: wrap;
}

.stats-summary {
  background: linear-gradient(135deg, #f5f7fa 0%, #eef2f8 100%);
  border-radius: 8px;
  padding: 24px;
  margin-top: 20px;
  border: 1px solid #ebeef5;
}

.stats-summary h3 {
  margin-top: 0;
  color: #000000;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-top: 20px;
}

.stat {
  background: white;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  border: 1px solid #ebeef5;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.stat:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
  transform: translateY(-4px);
}

.stat-label {
  display: block;
  color: #333333;
  font-size: 14px;
  margin-bottom: 10px;
}

.stat-number {
  display: block;
  font-size: 32px;
  font-weight: 700;
}

.stat-number.known {
  color: #67c23a;
}

.stat-number.fuzzy {
  color: #e6a23c;
}

.stat-number.unknown {
  color: #f56c6c;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 60px;
  margin: 0;
}

.empty-text {
  font-size: 18px;
  color: #333333;
  margin: 15px 0;
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  max-width: 500px;
  width: 90%;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #ebeef5;
}

.modal-header h3 {
  margin: 0;
  color: #000000;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.close-btn:hover {
  color: #333333;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #000000;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.input-with-info {
  display: flex;
  gap: 10px;
  align-items: center;
}

.input-with-info input {
  flex: 1;
}

.input-with-info .info {
  color: #333333;
  font-size: 14px;
  white-space: nowrap;
}

/* 动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.flip-enter-active {
  animation: fadeIn 0.3s ease;
}

/* 响应式 */
@media (max-width: 768px) {
  .plan-info {
    grid-template-columns: 1fr;
  }
  
  .card-face {
    padding: 40px 20px;
    min-height: 280px;
  }
  
  .word-text {
    font-size: 28px;
  }
  
  .meaning-text {
    font-size: 18px;
  }
  
  .actions {
    flex-direction: column;
  }
  
  .btn-unknown,
  .btn-fuzzy,
  .btn-known {
    flex: none;
    width: 100%;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .tabs-container {
    flex-direction: column;
  }
  
  .tab {
    text-align: left;
  }
}
</style>
