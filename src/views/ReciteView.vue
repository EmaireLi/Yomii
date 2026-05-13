<template>
  <section class="recite-view">
    <!-- 学习计划管理区 -->
    <el-card class="plan-card"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <template #header>
        <div class="card-header">
          <span>学习计划</span>
        </div>
      </template>
      
      <el-row :gutter="20" v-if="currentPlan">
        <!-- 当前计划显示 -->
        <el-col :xs="24" :sm="8">
          <div class="plan-item-new">
            <div class="plan-label">当前计划</div>
            <div class="plan-value">{{ currentPlan.name }}</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="plan-item-new">
            <div class="plan-label">今日目标</div>
            <div class="plan-value">{{ currentPlan.dailyGoal }} 个单词</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="plan-item-new">
            <div class="plan-label">当前辞书</div>
            <div class="plan-value">{{ currentDictionaryName }}</div>
          </div>
        </el-col>
      </el-row>

      <div class="plan-switch-row">
        <div class="plan-switch-label">切换当前学习计划</div>
        <div class="plan-switch-controls">
          <el-select
            v-model="selectedPlanId"
            class="plan-switch-select"
            placeholder="请选择学习计划"
            @change="handlePlanSwitch"
          >
            <el-option
              v-for="plan in studyPlans"
              :key="plan.id"
              :label="`${plan.name}（${plan.dailyGoal}词/天）`"
              :value="plan.id"
            />
          </el-select>
          <el-tag type="info" effect="plain">{{ studyPlans.length }} 个计划</el-tag>
        </div>
      </div>

      <el-collapse v-model="planPanelOpenNames" class="plan-collapse">
        <el-collapse-item name="edit">
          <template #title>
            <div class="config-title-row">
              <el-icon><Setting /></el-icon>
              <span>调整当前计划</span>
            </div>
          </template>

          <div class="config-grid">
            <div class="config-item">
              <label class="config-label">选择辞书</label>
              <select v-model="selectedDictionaryId" class="config-select">
                <option v-for="dict in dictionaries" :key="dict.id" :value="dict.id">
                  {{ dict.name }} ({{ dict.wordCount }} 个单词)
                </option>
              </select>
              <div class="dict-description" v-if="selectedDictionary">
                {{ selectedDictionary.description }}
              </div>
              <div class="dict-tags" v-if="selectedDictionary?.tags?.length">
                标签：{{ selectedDictionary.tags.join(' / ') }}
              </div>
            </div>

            <div class="config-item">
              <label class="config-label">每日学习单词数</label>
              <div class="word-count-options">
                <button
                  v-for="count in wordCountOptions"
                  :key="count"
                  @click="currentDailyGoal = count"
                  :class="['word-count-btn', { active: currentDailyGoal === count }]"
                >
                  {{ count }}
                </button>
              </div>
              <input
                v-model.number="customWordCount"
                type="number"
                class="custom-input"
                placeholder="或输入自定义数量"
                min="1"
                max="100"
                @change="updateCustomWordCount"
              />
            </div>
          </div>

          <div class="config-actions">
            <button @click="savePlanConfig" class="btn btn-primary">保存配置</button>
            <button @click="resetPlanConfig" class="btn btn-secondary">重置</button>
          </div>
        </el-collapse-item>

        <el-collapse-item name="create">
          <template #title>
            <div class="config-title-row">
              <el-icon><Setting /></el-icon>
              <span>新增学习计划</span>
            </div>
          </template>

          <div class="config-grid">
            <div class="config-item">
              <label class="config-label">计划名称</label>
              <input v-model="newPlanName" type="text" class="custom-input" placeholder="请输入计划名称" />
            </div>

            <div class="config-item">
              <label class="config-label">选择辞书</label>
              <select v-model="newPlanDictionaryId" class="config-select">
                <option v-for="dict in dictionaries" :key="dict.id" :value="dict.id">
                  {{ dict.name }} ({{ dict.wordCount }} 个单词)
                </option>
              </select>
              <div class="dict-description" v-if="newSelectedDictionary">
                {{ newSelectedDictionary.description }}
              </div>
              <div class="dict-tags" v-if="newSelectedDictionary?.tags?.length">
                标签：{{ newSelectedDictionary.tags.join(' / ') }}
              </div>
            </div>

            <div class="config-item">
              <label class="config-label">每日学习单词数</label>
              <div class="word-count-options">
                <button
                  v-for="count in wordCountOptions"
                  :key="`new-${count}`"
                  @click="newPlanDailyGoal = count"
                  :class="['word-count-btn', { active: newPlanDailyGoal === count }]"
                >
                  {{ count }}
                </button>
              </div>
              <input
                v-model.number="newPlanDailyGoal"
                type="number"
                class="custom-input"
                min="1"
                max="100"
              />
            </div>

            <div class="config-item">
              <label class="config-label">复习比例（0-1）</label>
              <input
                v-model.number="newPlanReviewRatio"
                type="number"
                class="custom-input"
                min="0"
                max="1"
                step="0.1"
              />
            </div>
          </div>

          <div class="config-actions">
            <button @click="createNewPlanConfig" class="btn btn-primary">创建并切换</button>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <!-- 选项卡 -->
    <el-tabs v-model="activeTab" class="study-tabs"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <el-tab-pane name="learn">
      <template #label>
        <span class="tab-label"><el-icon><Reading /></el-icon> 背单词</span>
      </template>
      <template v-if="learnWords.length > 0 && currentWord && !learnSessionCompleted">
        <h1>背单词 <span class="counter">{{ currentLearnIndex + 1 }} / {{ learnWords.length }}</span></h1>
        
        <!-- 进度条 -->
        <div class="progress-bar">
          <div class="progress" :style="{ width: learnProgressPercent + '%' }"></div>
        </div>

        <!-- 学习进度 -->
        <div class="mark-progress">
          <span class="progress-primary">已背完 {{ learnWordsMarkedCount }} / {{ learnWords.length }} 个单词</span>
          <span v-if="learnRemainingCount > 0" class="warn-text">未背单词位置（点击跳转）：</span>
          <div v-if="learnRemainingCount > 0" class="remaining-list">
            <button
              v-for="item in learnUnmarkedItems"
              :key="item.word.id"
              class="remaining-chip"
              :class="{ active: currentWord && currentWord.id === item.word.id }"
              @click="jumpToLearnWord(item.word.id)"
            >
              {{ item.position }}. {{ item.word.word }}
            </button>
          </div>
          <span v-else class="done-text">全部单词已完成标记</span>
        </div>

        <!-- 闪卡 -->
        <div class="flashcard">
          <!-- 3D 翻转容器 -->
          <div class="flip-container" :class="{ flipped: showLearningMeaning, 'no-flip': skipFlipAnimation }">
            <!-- 卡片正面 -->
            <div class="flip-inner">
              <!-- 正面 -->
              <div class="card-face">
                <!-- 状态标签 -->
                <div v-if="learnWordStatus" class="status-badge" :class="`status-${learnWordStatus}`">
                  {{ { unknown: '不认识', fuzzy: '模糊', known: '认识' }[learnWordStatus] }}
                </div>

                <div class="card-content">
                  <h2 class="word-text">{{ currentWord.word }}</h2>
                  <p class="kana-text" v-if="currentWord.kana">[{{ currentWord.kana }}]</p>
                </div>
                
                <!-- 收藏按钮 -->
                <div class="favorite-btn-container">
                  <button
                    @click="toggleFavorite(currentWord.id)"
                    class="favorite-btn"
                    :class="{ active: isFavorited(currentWord.id) }"
                  >
                    <el-icon>
                      <component :is="isFavorited(currentWord.id) ? StarFilled : Star" />
                    </el-icon>
                  </button>
                </div>

                <!-- 翻转提示 -->
                <div v-if="!showLearningMeaning" class="flip-hint" @click="toggleLearningCard">
                  <p>点击或按空格键</p>
                  <p class="hint-text">查看释义</p>
                </div>
              </div>

              <!-- 背面 -->
              <div class="card-back">
                <div class="back-content">
                  <hr class="divider" />
                  <p class="meaning-text">中文：{{ currentWord.chineseMeaning || '暂无' }}</p>
                  <p class="meaning-text">日文：{{ currentWord.japaneseMeaning }}</p>
                  <p v-if="currentWord.partOfSpeech" class="pos">
                    {{ currentWord.partOfSpeech }}
                  </p>
                  <div v-if="currentWord.example" class="example-box">
                    <p class="example-label">例句：</p>
                    <p class="example-text">{{ currentWord.example }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="actions">
          <button 
            @click="prevLearnWord" 
            class="btn btn-secondary"
            :class="{ 'btn-disabled': currentLearnIndex === 0 }"
          >
            <el-icon><ArrowLeft /></el-icon> 上一个
          </button>
          <button @click="toggleLearningCard" class="btn btn-primary">
            查看释义 (Space)
          </button>
          <button 
            @click="skipLearnWord" 
            class="btn btn-secondary"
            :class="{ 'btn-disabled': currentLearnIndex === learnWords.length - 1 }"
          >
            下一个 <el-icon><ArrowRight /></el-icon>
          </button>
          <button @click="nextLearnWord('unknown')" class="btn btn-unknown">
            <el-icon><CircleClose /></el-icon> 不认识
          </button>
          <button @click="nextLearnWord('fuzzy')" class="btn btn-fuzzy">
            <el-icon><QuestionFilled /></el-icon> 模糊
          </button>
          <button @click="nextLearnWord('known')" class="btn btn-known">
            <el-icon><Check /></el-icon> 认识
          </button>
        </div>

        <!-- 快捷键提示 -->
        <div class="keyboard-hints">
          <span class="hint">← → 切换卡片 | Space 查看释义 | 1: 不认识 | 2: 模糊 | 3: 认识</span>
        </div>
      </template>

      <!-- 背单词完成状态 -->
      <div v-else-if="learnSessionCompleted" class="completion-state">
        <div v-if="showLearnCelebration" class="celebration-layer" aria-hidden="true">
          <span v-for="n in 18" :key="`confetti-${n}`" class="confetti-piece" :style="{ '--i': n }"></span>
          <div class="celebration-glow"></div>
        </div>
        <div class="completion-content">
          <p class="completion-icon"><el-icon><Promotion /></el-icon></p>
          <p class="completion-text">恭喜！今天的背单词任务已完成</p>
          <div class="button-group">
            <button @click="requestAddMore" class="btn btn-primary"><el-icon><Promotion /></el-icon> 加量学习</button>
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
        <p class="empty-icon"><el-icon><Warning /></el-icon></p>
        <p class="empty-text">暂无待背诵的单词</p>
        <button @click="loadLearnWords" class="btn btn-primary">重新加载</button>
      </div>
    </el-tab-pane>

    <!-- 复习部分 -->
    <el-tab-pane name="review" class="tab-content">
      <template #label>
        <span class="tab-label"><el-icon><EditPen /></el-icon> 复习</span>
      </template>
      <div class="review-mode-switch">
        <button
          class="mode-btn"
          :class="{ active: reviewMode === 'today' }"
          @click="switchReviewMode('today')"
        >
          今日复习任务
        </button>
        <button
          class="mode-btn"
          :class="{ active: reviewMode === 'random' }"
          @click="switchReviewMode('random')"
        >
          强化练习
        </button>
        <button class="mode-refresh-btn" @click="refreshReviewWords">
          刷新当前模式
        </button>
      </div>
      <template v-if="reviewWords.length > 0 && currentReviewWord && !reviewSessionCompleted">
        <h1>{{ reviewModeLabel }} <span class="counter">{{ currentReviewIndex + 1 }} / {{ reviewWords.length }}</span></h1>
        
        <!-- 进度条 -->
        <div class="progress-bar">
          <div class="progress" :style="{ width: reviewProgressPercent + '%' }"></div>
        </div>

        <!-- 复习进度 -->
        <div class="mark-progress">
          <span class="progress-primary">已背完 {{ reviewWordsMarkedCount }} / {{ reviewWords.length }} 个单词</span>
          <span v-if="reviewRemainingCount > 0" class="warn-text">未复习单词：{{ reviewRemainingWordsText }}</span>
          <span v-else class="done-text">全部单词已完成标记</span>
        </div>

        <!-- 闪卡 -->
        <div class="flashcard">
          <!-- 3D 翻转容器 -->
          <div class="flip-container" :class="{ flipped: showReviewMeaning, 'no-flip': skipFlipAnimation }">
            <!-- 卡片正面 -->
            <div class="flip-inner">
              <!-- 正面 -->
              <div class="card-face">
                <!-- 状态标签 -->
                <div v-if="reviewWordStatus" class="status-badge" :class="`status-${reviewWordStatus}`">
                  {{ { unknown: '不认识', fuzzy: '模糊', known: '认识' }[reviewWordStatus] }}
                </div>

                <div class="card-content">
                  <h2 class="word-text">{{ currentReviewWord.word }}</h2>
                  <p class="kana-text" v-if="currentReviewWord.kana">[{{ currentReviewWord.kana }}]</p>
                </div>

                <!-- 翻转提示 -->
                <div v-if="!showReviewMeaning" class="flip-hint" @click="toggleReviewCard">
                  <p>点击或按空格键</p>
                  <p class="hint-text">查看释义</p>
                </div>
              </div>

              <!-- 背面 -->
              <div class="card-back">
                <div class="back-content">
                  <hr class="divider" />
                  <p class="meaning-text">中文：{{ currentReviewWord.chineseMeaning || '暂无' }}</p>
                  <p class="meaning-text">日文：{{ currentReviewWord.japaneseMeaning }}</p>
                  <p v-if="currentReviewWord.partOfSpeech" class="pos">
                    {{ currentReviewWord.partOfSpeech }}
                  </p>
                  <div v-if="currentReviewWord.example" class="example-box">
                    <p class="example-label">例句：</p>
                    <p class="example-text">{{ currentReviewWord.example }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 学习状态信息 -->
        <div v-if="showReviewMeaning" class="study-info">
          <p>{{ autoFlipCountdown > 0 ? `${autoFlipCountdown}秒后自动翻回` : '选择您对这个词汇的掌握程度' }}</p>
        </div>

        <!-- 操作按钮 -->
        <div class="actions">
          <button
            @click="prevReviewWord"
            class="btn btn-secondary"
            :class="{ 'btn-disabled': currentReviewIndex === 0 }"
          >
            <el-icon><ArrowLeft /></el-icon> 上一个
          </button>
          <button @click="toggleReviewCard" class="btn btn-primary">
            查看释义 (Space)
          </button>
          <button
            @click="skipReviewWord"
            class="btn btn-secondary"
            :class="{ 'btn-disabled': currentReviewIndex === reviewWords.length - 1 }"
          >
            下一个 <el-icon><ArrowRight /></el-icon>
          </button>
          <button @click="nextReviewWord('unknown')" class="btn btn-unknown">
            <el-icon><CircleClose /></el-icon> 不认识
          </button>
          <button @click="nextReviewWord('fuzzy')" class="btn btn-fuzzy">
            <el-icon><QuestionFilled /></el-icon> 模糊
          </button>
          <button @click="nextReviewWord('known')" class="btn btn-known">
            <el-icon><Check /></el-icon> 认识
          </button>
        </div>

        <!-- 快捷键提示 -->
        <div class="keyboard-hints">
          <span class="hint">← → 切换卡片 | Space 查看释义 | 1: 不认识 | 2: 模糊 | 3: 认识</span>
        </div>
      </template>

      <!-- 复习完成状态 -->
      <div v-else-if="reviewSessionCompleted" class="completion-state">
        <div v-if="showReviewCelebration" class="celebration-layer" aria-hidden="true">
          <span v-for="n in 18" :key="`review-confetti-${n}`" class="confetti-piece" :style="{ '--i': n }"></span>
          <div class="celebration-glow"></div>
        </div>
        <div class="completion-content">
          <p class="completion-icon"><el-icon><Promotion /></el-icon></p>
          <p class="completion-text">{{ reviewMode === 'today' ? '恭喜！今天的复习任务已完成' : '恭喜！本轮强化练习已完成' }}</p>
          <div class="button-group">
            <button
              v-if="reviewMode === 'today'"
              @click="switchReviewMode('random')"
              class="btn btn-primary"
            >
              开始强化练习
            </button>
            <button
              v-else
              @click="resetReviewSession('random')"
              class="btn btn-primary"
            >
              再刷一轮
            </button>
            <button @click="resetReviewSession('today')" class="btn btn-secondary">
              返回今日任务
            </button>
          </div>
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
        <p class="empty-icon"><el-icon><Warning /></el-icon></p>
        <p class="empty-text">{{ reviewMode === 'today' ? '今日暂无到期复习任务' : '暂无可用强化练习单词' }}</p>
        <div class="button-group">
          <button @click="refreshReviewWords" class="btn btn-primary">重新加载</button>
          <button
            v-if="reviewMode === 'today'"
            @click="switchReviewMode('random')"
            class="btn btn-secondary"
          >
            去强化练习
          </button>
          <button
            v-else
            @click="switchReviewMode('today')"
            class="btn btn-secondary"
          >
            返回今日任务
          </button>
        </div>
      </div>
    </el-tab-pane>
  </el-tabs>
</section>
</template>

<script setup lang="ts">
import { ref, computed, reactive, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { DictionaryConfig, StudyPlan, Word } from '@/types'
import {
  activateStudyPlan,
  createStudyPlan,
  getDictionaryCatalog,
  getLearnWords,
  getReviewRandom,
  getReviewToday,
  getStudyPlans,
  requestAddMore as requestAddMoreAPI,
  saveLearningSession,
  updateStudyPlan as updateStudyPlanAPI,
  isAuthenticated
} from '@/api'
import { useWordProgress, useStudyStats, useFavorites } from '@/composables/useLocalStorage'
import { WORD_COUNT_OPTIONS } from '@/utils/constants'
import { Setting, Reading, CircleClose, QuestionFilled, Check, Promotion, Warning, Star, StarFilled, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'

/**
 * 检查登录状态，未登录则打开登录对话框
 */
function requireLogin(): boolean {
  if (!isAuthenticated()) {
    ElMessage.warning('请先登录才能学习')
    window.dispatchEvent(new CustomEvent('open-login-dialog'))
    return false
  }
  return true
}

// 标签
const activeTab = ref<'learn' | 'review'>('learn')

// 学习计划管理
const studyPlans = ref<StudyPlan[]>([])
const currentPlan = ref<StudyPlan | null>(null)
const selectedPlanId = ref('')
const dictionaries = ref<DictionaryConfig[]>([])
const wordCountOptions = WORD_COUNT_OPTIONS
const planPanelOpenNames = ref<string[]>([])
const selectedDictionaryId = ref<string>('common')
const currentDailyGoal = ref(10)
const customWordCount = ref<number | null>(null)
const newPlanName = ref('新学习计划')
const newPlanDictionaryId = ref<string>('common')
const newPlanDailyGoal = ref(10)
const newPlanReviewRatio = ref(0.5)

// 计算当前选中的辞书
const selectedDictionary = computed(() => {
  return dictionaries.value.find(d => d.id === selectedDictionaryId.value)
})

const newSelectedDictionary = computed(() => {
  return dictionaries.value.find(d => d.id === newPlanDictionaryId.value)
})

// 计算当前辞书的名称
const currentDictionaryName = computed(() => {
  const plan = currentPlan.value
  if (plan?.dictionaryId) {
    const dict = dictionaries.value.find(d => d.id === plan.dictionaryId)
    return dict ? dict.name : '常用词典'
  }
  return '常用词典'
})

// 背单词数据
const learnWords = ref<Word[]>([])
const learnSessionPoolWords = ref<Word[]>([])
const currentLearnIndex = ref(0)
const showLearningMeaning = ref(false)
const skipFlipAnimation = ref(false)
const learnSessionCompleted = ref(false)
const showLearnCelebration = ref(false)
const celebrationTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const learnWordStatusMap = ref<Map<string, 'unknown' | 'fuzzy' | 'known'>>(new Map())
const learnSessionStats = reactive({
  known: 0,
  fuzzy: 0,
  unknown: 0
})

// 复习数据
const reviewWords = ref<Word[]>([])
const currentReviewIndex = ref(0)
const reviewMode = ref<'today' | 'random'>('today')
const showReviewMeaning = ref(false)
const reviewSessionCompleted = ref(false)
const showReviewCelebration = ref(false)
const reviewWordStatusMap = ref<Map<string, 'unknown' | 'fuzzy' | 'known'>>(new Map())
const autoFlipCountdown = ref(0)
const autoFlipTimer = ref<ReturnType<typeof setInterval> | null>(null)
const reviewCelebrationTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const reviewSessionStats = reactive({
  known: 0,
  fuzzy: 0,
  unknown: 0
})

// 其他功能
const { updateProgress } = useWordProgress()
const { incrementRecited, syncStudyStats } = useStudyStats()
const { isFavorited, toggleFavorite: originalToggleFavorite } = useFavorites()
const isLoading = ref(false)

/**
 * 需要登录检查的 toggleFavorite 包装函数
 */
const toggleFavorite = async (wordId: string) => {
  if (!isAuthenticated()) {
    ElMessage.warning('请先登录才能收藏词汇')
    window.dispatchEvent(new CustomEvent('open-login-dialog'))
    return
  }
  try {
    await originalToggleFavorite(wordId)
    const isFav = isFavorited(wordId)
    ElMessage.success(isFav ? '已收藏' : '已取消收藏')
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  }
}

// 计算属性
const currentWord = computed(() => learnWords.value[currentLearnIndex.value] || null)
const currentReviewWord = computed(() => reviewWords.value[currentReviewIndex.value] || null)

const learnWordStatus = computed(() => {
  if (!currentWord.value) return null
  return learnWordStatusMap.value.get(currentWord.value.id) || null
})

const reviewWordStatus = computed(() => {
  if (!currentReviewWord.value) return null
  return reviewWordStatusMap.value.get(currentReviewWord.value.id) || null
})

const reviewModeLabel = computed(() => (
  reviewMode.value === 'today' ? '今日复习任务' : '强化练习'
))

const reviewTaskLimit = computed(() => {
  const plan = currentPlan.value
  if (!plan) return 20
  const count = Math.round(plan.dailyGoal * plan.reviewRatio)
  return Math.max(1, count)
})

// 检查是否所有单词都已标记
const learnWordsAllMarked = computed(() => {
  if (learnWords.value.length === 0) return false
  return learnWords.value.every(word => learnWordStatusMap.value.has(word.id))
})

const reviewWordsAllMarked = computed(() => {
  if (reviewWords.value.length === 0) return false
  return reviewWords.value.every(word => reviewWordStatusMap.value.has(word.id))
})

const learnUnmarkedWords = computed(() => {
  return learnWords.value.filter(word => !learnWordStatusMap.value.has(word.id))
})

const learnUnmarkedItems = computed(() => {
  return learnWords.value
    .map((word, index) => ({ word, position: index + 1 }))
    .filter(item => !learnWordStatusMap.value.has(item.word.id))
})

const reviewUnmarkedWords = computed(() => {
  return reviewWords.value.filter(word => !reviewWordStatusMap.value.has(word.id))
})

const learnRemainingCount = computed(() => learnUnmarkedWords.value.length)
const reviewRemainingCount = computed(() => reviewUnmarkedWords.value.length)

const learnRemainingWordsText = computed(() => {
  const words = learnUnmarkedWords.value.map(word => word.word)
  if (words.length <= 6) return words.join('、')
  return `${words.slice(0, 6).join('、')} 等${words.length}个`
})

const reviewRemainingWordsText = computed(() => {
  const words = reviewUnmarkedWords.value.map(word => word.word)
  if (words.length <= 6) return words.join('、')
  return `${words.slice(0, 6).join('、')} 等${words.length}个`
})

// 获取已标记单词的数量
const learnWordsMarkedCount = computed(() => {
  return learnWordStatusMap.value.size
})

const reviewWordsMarkedCount = computed(() => {
  return reviewWordStatusMap.value.size
})

const learnProgressPercent = computed(() => {
  if (learnWords.value.length === 0) return 0
  return (learnWordsMarkedCount.value / learnWords.value.length) * 100
})

const reviewProgressPercent = computed(() => {
  if (reviewWords.value.length === 0) return 0
  return (reviewWordsMarkedCount.value / reviewWords.value.length) * 100
})

// 背单词相关方法
const toggleLearningCard = () => {
  showLearningMeaning.value = !showLearningMeaning.value
}

const triggerLearnCelebration = () => {
  showLearnCelebration.value = true
  if (celebrationTimer.value) {
    clearTimeout(celebrationTimer.value)
  }
  celebrationTimer.value = setTimeout(() => {
    showLearnCelebration.value = false
    celebrationTimer.value = null
  }, 2600)
}

const triggerReviewCelebration = () => {
  showReviewCelebration.value = true
  if (reviewCelebrationTimer.value) {
    clearTimeout(reviewCelebrationTimer.value)
  }
  reviewCelebrationTimer.value = setTimeout(() => {
    showReviewCelebration.value = false
    reviewCelebrationTimer.value = null
  }, 2600)
}

const applyWordStatusChange = (
  statusMap: Map<string, 'unknown' | 'fuzzy' | 'known'>,
  sessionStats: { known: number; fuzzy: number; unknown: number },
  wordId: string,
  nextStatus: 'unknown' | 'fuzzy' | 'known'
) => {
  const previousStatus = statusMap.get(wordId)
  const isFirstMarked = previousStatus === undefined

  if (previousStatus && previousStatus !== nextStatus) {
    sessionStats[previousStatus] = Math.max(0, sessionStats[previousStatus] - 1)
  }

  if (!previousStatus || previousStatus !== nextStatus) {
    sessionStats[nextStatus]++
  }

  statusMap.set(wordId, nextStatus)
  return { previousStatus, isFirstMarked }
}

const nextLearnWord = async (status: 'unknown' | 'fuzzy' | 'known') => {
  if (!requireLogin()) return
  
  if (currentWord.value) {
    const wordId = currentWord.value.id
    const { isFirstMarked } = applyWordStatusChange(
      learnWordStatusMap.value,
      learnSessionStats,
      wordId,
      status
    )

    updateProgress(currentWord.value.id, status)
    if (isFirstMarked) {
      incrementRecited()
    }

    // 选择后直接跳到下一词，不执行翻转动画
    skipFlipAnimation.value = true
    showLearningMeaning.value = false
    
    // 检查是否所有单词都已标记
    const allMarked = learnWords.value.every(word => learnWordStatusMap.value.has(word.id))
    
    if (allMarked) {
      // 所有单词都标记了，显示完成状态
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
        await syncStudyStats()
      }
    } else {
      // 还有未标记的单词，继续到下一张
      currentLearnIndex.value++
      if (currentLearnIndex.value >= learnWords.value.length) {
        // 到达最后一张，循环回开头找未标记的单词
        currentLearnIndex.value = 0
      }
    }

    requestAnimationFrame(() => {
      skipFlipAnimation.value = false
    })
  }
}

const jumpToLearnWord = (wordId: string) => {
  const targetIndex = learnWords.value.findIndex(word => word.id === wordId)
  if (targetIndex === -1) return
  activeTab.value = 'learn'
  showLearningMeaning.value = false
  currentLearnIndex.value = targetIndex
}

// 上一张卡片
const prevLearnWord = () => {
  if (currentLearnIndex.value > 0) {
    showLearningMeaning.value = false
    currentLearnIndex.value--
  }
}

// 下一张卡片（不记录答案）
const skipLearnWord = () => {
  if (currentLearnIndex.value < learnWords.value.length - 1) {
    showLearningMeaning.value = false
    currentLearnIndex.value++
  }
}

const loadLearnWords = async () => {
  if (!isAuthenticated()) {
    learnWords.value = []
    learnSessionPoolWords.value = []
    return
  }

  isLoading.value = true
  try {
    if (!currentPlan.value) {
      await loadStudyPlans()
    }
    if (currentPlan.value) {
      const words = await getLearnWords(currentPlan.value.id)
      learnWords.value = words
      learnSessionPoolWords.value = [...words]
    }
  } catch (error) {
    console.error('Failed to load learn words:', error)
    learnWords.value = []
    learnSessionPoolWords.value = []
  } finally {
    isLoading.value = false
  }
}

const resetLearnSessionWithSource = async (reloadFromApi: boolean = false) => {
  learnSessionStats.known = 0
  learnSessionStats.fuzzy = 0
  learnSessionStats.unknown = 0
  currentLearnIndex.value = 0
  showLearningMeaning.value = false
  learnSessionCompleted.value = false
  showLearnCelebration.value = false
  learnWordStatusMap.value.clear()

  if (reloadFromApi || learnSessionPoolWords.value.length === 0) {
    await loadLearnWords()
    return
  }

  learnWords.value = [...learnSessionPoolWords.value]
}

const resetLearnSession = async () => {
  await resetLearnSessionWithSource(false)
}

// 复习相关方法
const toggleReviewCard = () => {
  // 清除之前的计时器
  if (autoFlipTimer.value) {
    clearInterval(autoFlipTimer.value)
    autoFlipTimer.value = null
    autoFlipCountdown.value = 0
  }

  showReviewMeaning.value = !showReviewMeaning.value

  // 如果翻转到显示释义，启动自动翻回计时器
  if (showReviewMeaning.value) {
    autoFlipCountdown.value = 3
    autoFlipTimer.value = setInterval(() => {
      autoFlipCountdown.value--
      if (autoFlipCountdown.value <= 0) {
        showReviewMeaning.value = false
        autoFlipCountdown.value = 0
        if (autoFlipTimer.value) {
          clearInterval(autoFlipTimer.value)
          autoFlipTimer.value = null
        }
      }
    }, 1000)
  }
}

const nextReviewWord = async (status: 'unknown' | 'fuzzy' | 'known') => {
  if (!requireLogin()) return
  
  // 清除自动翻回计时器
  if (autoFlipTimer.value) {
    clearInterval(autoFlipTimer.value)
    autoFlipTimer.value = null
    autoFlipCountdown.value = 0
  }
  
  if (currentReviewWord.value) {
    const wordId = currentReviewWord.value.id
    const { isFirstMarked } = applyWordStatusChange(
      reviewWordStatusMap.value,
      reviewSessionStats,
      wordId,
      status
    )

    updateProgress(currentReviewWord.value.id, status)
    if (isFirstMarked) {
      incrementRecited()
    }

    // 选择后直接跳到下一词，不执行翻转动画
    skipFlipAnimation.value = true
    showReviewMeaning.value = false
    
    // 检查是否所有单词都已标记
    const allMarked = reviewWords.value.every(word => reviewWordStatusMap.value.has(word.id))
    
    if (allMarked) {
      // 所有单词都标记了，显示完成状态
      reviewSessionCompleted.value = true
      if (currentPlan.value) {
        const today = new Date().toISOString().split('T')[0] || ''
        await saveLearningSession(currentPlan.value.id, {
          planId: currentPlan.value.id,
          date: today,
          learnedWords: [],
          reviewedWords: reviewWords.value.map(w => w.id),
          sessionStats: {
            knownCount: reviewSessionStats.known,
            fuzzyCount: reviewSessionStats.fuzzy,
            unknownCount: reviewSessionStats.unknown
          },
          completedAt: Date.now()
        })
        await syncStudyStats()
      }
    } else {
      // 还有未标记的单词，继续到下一张
      currentReviewIndex.value++
      if (currentReviewIndex.value >= reviewWords.value.length) {
        // 到达最后一张，循环回开头找未标记的单词
        currentReviewIndex.value = 0
      }
    }

    requestAnimationFrame(() => {
      skipFlipAnimation.value = false
    })
  }
}

// 复习上一张卡片
const prevReviewWord = () => {
  if (currentReviewIndex.value > 0) {
    showReviewMeaning.value = false
    currentReviewIndex.value--
  }
}

// 复习下一张卡片（不记录答案）
const skipReviewWord = () => {
  if (currentReviewIndex.value < reviewWords.value.length - 1) {
    showReviewMeaning.value = false
    currentReviewIndex.value++
  }
}

const loadReviewWords = async (mode: 'today' | 'random' = reviewMode.value) => {
  reviewMode.value = mode

  if (!isAuthenticated()) {
    reviewWords.value = []
    return
  }

  isLoading.value = true
  try {
    if (!currentPlan.value) {
      await loadStudyPlans()
    }
    const targetCount = reviewTaskLimit.value
    const reviewList = mode === 'today'
      ? await getReviewToday(targetCount)
      : await getReviewRandom(Math.max(10, targetCount))
    const nextWords = reviewList.items.map(item => item.word)
    reviewWords.value = nextWords
  } catch (error) {
    console.error('Failed to load review words:', error)
    reviewWords.value = []
  } finally {
    isLoading.value = false
  }
}

const resetReviewSession = async (mode: 'today' | 'random' = reviewMode.value) => {
  // 清除自动翻回计时器
  if (autoFlipTimer.value) {
    clearInterval(autoFlipTimer.value)
    autoFlipTimer.value = null
  }

  reviewSessionStats.known = 0
  reviewSessionStats.fuzzy = 0
  reviewSessionStats.unknown = 0
  currentReviewIndex.value = 0
  showReviewMeaning.value = false
  autoFlipCountdown.value = 0
  reviewSessionCompleted.value = false
  showReviewCelebration.value = false
  reviewWordStatusMap.value.clear()
  await loadReviewWords(mode)
}

const switchReviewMode = async (mode: 'today' | 'random') => {
  await resetReviewSession(mode)
}

const refreshReviewWords = async () => {
  await resetReviewSession(reviewMode.value)
}

// 加量学习
const requestAddMore = async () => {
  if (!requireLogin()) return

  try {
    if (currentPlan.value) {
      const excludeWordIds = learnSessionPoolWords.value
        .map(word => Number(word.id))
        .filter(id => Number.isInteger(id) && id > 0)

      const result = await requestAddMoreAPI(currentPlan.value.id, 5, excludeWordIds)
      if (result.success) {
        const existingIds = new Set(learnSessionPoolWords.value.map(word => word.id))
        const additionalWords = result.moreWords.filter(word => !existingIds.has(word.id))

        if (additionalWords.length === 0) {
          ElMessage.info('当前可用单词不足，暂无新的加量单词')
          return
        }

        learnSessionPoolWords.value.push(...additionalWords)
        // 加量学习阶段仅学习新增单词
        learnWords.value = additionalWords
        learnWordStatusMap.value.clear()
        currentLearnIndex.value = 0
        showLearningMeaning.value = false
        skipFlipAnimation.value = false
        learnSessionCompleted.value = false
        showLearnCelebration.value = false
        ElMessage.success(`已添加 ${additionalWords.length} 个加量单词`)
      }
    }
  } catch (error) {
    console.error('加量学习失败:', error)
    ElMessage.error('加量学习失败，请稍后重试')
  }
}

const loadDictionaries = async () => {
  try {
    dictionaries.value = await getDictionaryCatalog()
  } catch (error) {
    console.error('Failed to load dictionaries:', error)
    dictionaries.value = []
  }
}

const loadStudyPlans = async () => {
  if (!isAuthenticated()) {
    studyPlans.value = []
    currentPlan.value = null
    selectedPlanId.value = ''
    return
  }

  try {
    studyPlans.value = await getStudyPlans()
    currentPlan.value = studyPlans.value.find(plan => plan.isActive) || studyPlans.value[0] || null
    if (currentPlan.value) {
      selectedPlanId.value = currentPlan.value.id
      selectedDictionaryId.value = currentPlan.value.dictionaryId || 'common'
      currentDailyGoal.value = currentPlan.value.dailyGoal
    }
  } catch (error) {
    console.error('Failed to load study plans:', error)
    studyPlans.value = []
    currentPlan.value = null
    selectedPlanId.value = ''
  }
}

const handlePlanSwitch = async (planId: string) => {
  if (!requireLogin()) return
  if (!planId || (currentPlan.value && currentPlan.value.id === planId)) return

  try {
    await activateStudyPlan(planId)
    await loadStudyPlans()
    await resetLearnSessionWithSource(true)
    await resetReviewSession()
    ElMessage.success('已切换学习计划')
  } catch (error: any) {
    ElMessage.error(error?.message || '切换学习计划失败')
  }
}

// 学习计划管理
const savePlanConfig = async () => {
  if (!requireLogin()) return
  if (!currentPlan.value) {
    ElMessage.warning('请先创建学习计划')
    return
  }

  const finalDailyGoal = customWordCount.value || currentDailyGoal.value
  if (finalDailyGoal < 1) {
    ElMessage.warning('每日学习单词数至少为 1')
    return
  }

  try {
    await updateStudyPlanAPI(currentPlan.value.id, {
      name: currentPlan.value.name,
      dailyGoal: finalDailyGoal,
      reviewRatio: currentPlan.value.reviewRatio,
      dictionaryId: selectedDictionaryId.value
    })
    await loadStudyPlans()
  } catch (error: any) {
    ElMessage.error(error?.message || '保存学习计划失败')
    return
  }

  await resetLearnSessionWithSource(true)
  await resetReviewSession()
  ElMessage.success('学习计划已更新')
}

const createNewPlanConfig = async () => {
  if (!requireLogin()) return

  const name = newPlanName.value.trim()
  if (!name) {
    ElMessage.warning('请输入学习计划名称')
    return
  }
  if (newPlanDailyGoal.value < 1) {
    ElMessage.warning('每日学习单词数至少为 1')
    return
  }
  if (newPlanReviewRatio.value < 0 || newPlanReviewRatio.value > 1) {
    ElMessage.warning('复习比例应在 0 到 1 之间')
    return
  }

  try {
    const newPlan = await createStudyPlan({
      name,
      dailyGoal: newPlanDailyGoal.value,
      reviewRatio: newPlanReviewRatio.value,
      dictionaryId: newPlanDictionaryId.value
    })
    await activateStudyPlan(newPlan.id)
    await loadStudyPlans()

    newPlanName.value = '新学习计划'
    newPlanDictionaryId.value = 'common'
    newPlanDailyGoal.value = 10
    newPlanReviewRatio.value = 0.5
    planPanelOpenNames.value = []
  } catch (error: any) {
    ElMessage.error(error?.message || '创建学习计划失败')
    return
  }

  await resetLearnSessionWithSource(true)
  await resetReviewSession()
  ElMessage.success('新学习计划已创建并切换')
}

const resetPlanConfig = () => {
  if (currentPlan.value) {
    selectedDictionaryId.value = currentPlan.value.dictionaryId || 'common'
    currentDailyGoal.value = currentPlan.value.dailyGoal
    customWordCount.value = null
  }
}

const updateCustomWordCount = () => {
  if (customWordCount.value && customWordCount.value > 0) {
    currentDailyGoal.value = customWordCount.value
  }
}

// 键盘快捷键
const handleKeyboard = (event: KeyboardEvent) => {
  if (activeTab.value === 'learn') {
    if (event.code === 'Space') {
      event.preventDefault()
      toggleLearningCard()
    } else if (event.code === 'ArrowLeft') {
      event.preventDefault()
      prevLearnWord()
    } else if (event.code === 'ArrowRight') {
      event.preventDefault()
      skipLearnWord()
    } else if (event.code === 'Digit1') {
      nextLearnWord('unknown')
    } else if (event.code === 'Digit2') {
      nextLearnWord('fuzzy')
    } else if (event.code === 'Digit3') {
      nextLearnWord('known')
    }
  } else if (activeTab.value === 'review') {
    if (event.code === 'Space') {
      event.preventDefault()
      toggleReviewCard()
    } else if (event.code === 'ArrowLeft') {
      event.preventDefault()
      prevReviewWord()
    } else if (event.code === 'ArrowRight') {
      event.preventDefault()
      skipReviewWord()
    } else if (event.code === 'Digit1') {
      nextReviewWord('unknown')
    } else if (event.code === 'Digit2') {
      nextReviewWord('fuzzy')
    } else if (event.code === 'Digit3') {
      nextReviewWord('known')
    }
  }
}

watch(learnSessionCompleted, (completed) => {
  if (completed) {
    triggerLearnCelebration()
  }
})

watch(reviewSessionCompleted, (completed) => {
  if (completed) {
    triggerReviewCelebration()
  }
})

onMounted(() => {
  if (isAuthenticated()) {
    loadDictionaries().then(() => loadStudyPlans()).then(() => {
      loadLearnWords()
      loadReviewWords()
    })
  }

  window.addEventListener('keydown', handleKeyboard)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyboard)
  if (celebrationTimer.value) {
    clearTimeout(celebrationTimer.value)
    celebrationTimer.value = null
  }
  if (reviewCelebrationTimer.value) {
    clearTimeout(reviewCelebrationTimer.value)
    reviewCelebrationTimer.value = null
  }
  // 清除自动翻回计时器
  if (autoFlipTimer.value) {
    clearInterval(autoFlipTimer.value)
    autoFlipTimer.value = null
  }
})
</script>

<style scoped>
.recite-view {
  max-width: 95%;
  margin: 0 auto;
}

/* 学习计划管理区 */
.plan-card {
  margin-bottom: 3rem;
}

.card-header {
  font-size: 1.8rem;
}

.plan-item-new {
  padding: 1.5rem;
  background: linear-gradient(135deg, #f0f2f5 0%, #f5f7fa 100%);
  border-radius: 0.8rem;
  border-left: 0.4rem solid #667eea;
}

.plan-label {
  font-size: 1.4rem;
  color: #999;
  margin-bottom: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05rem;
}

.plan-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: #000000;
}

.plan-switch-row {
  margin-top: 2rem;
  display: flex;
  flex-wrap: wrap;
  gap: 1.2rem;
  align-items: center;
  justify-content: space-between;
}

.plan-switch-label {
  font-size: 1.6rem;
  font-weight: 600;
  color: #000000;
}

.plan-switch-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.plan-switch-select {
  width: 32rem;
  max-width: 100%;
}

.plan-collapse {
  margin-top: 1.6rem;
}

.config-title-row {
  display: inline-flex;
  align-items: center;
  gap: 0.8rem;
  color: #000000;
  font-weight: 600;
  font-size: 1.4rem;
}

/* 配置区 */
.config-section {
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 0.2rem solid #ebeef5;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(30rem, 1fr));
  gap: 2.4rem;
  margin-bottom: 2rem;
}

.config-item {
  display: flex;
  flex-direction: column;
}

.config-label {
  font-size: 1.4rem;
  font-weight: 600;
  color: #000000;
  margin-bottom: 1.2rem;
}

.config-select {
  padding: 1.2rem;
  border: 0.2rem solid #dcdfe6;
  border-radius: 0.6rem;
  font-size: 1.4rem;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
}

.config-select:hover {
  border-color: #667eea;
}

.config-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.1);
}

.dict-description {
  font-size: 1.2rem;
  color: #999;
  margin-top: 0.8rem;
  line-height: 1.5;
}

.dict-tags {
  font-size: 1.2rem;
  color: #667085;
  margin-top: 0.6rem;
  line-height: 1.5;
}

.word-count-options {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1.2rem;
}

.word-count-btn {
  padding: 1rem 1.6rem;
  border: 0.2rem solid #dcdfe6;
  background: white;
  border-radius: 0.6rem;
  font-size: 1.4rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  color: #222222;
}

.word-count-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.word-count-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: #667eea;
  box-shadow: 0 0.4rem 1.2rem rgba(102, 126, 234, 0.3);
}

.custom-input {
  padding: 1rem;
  border: 0.2rem solid #dcdfe6;
  border-radius: 0.6rem;
  font-size: 1.4rem;
  transition: all 0.3s;
}

.custom-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.1);
}

.config-actions {
  display: flex;
  gap: 1.2rem;
  justify-content: flex-start;
}

.config-actions .btn {
  padding: 1.2rem 3.2rem;
  font-size: 1.5rem;
}

/* 旧的选项卡和其他样式 */


/* 选项卡 */
.tabs-container {
  display: flex;
  gap: 1rem;
  margin-bottom: 3rem;
  border-bottom: 0.2rem solid #ebeef5;
}

.tab {
  padding: 1.2rem 2rem;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 1.6rem;
  color: #333333;
  border-bottom: 0.3rem solid transparent;
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

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
}

h1 {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #000000;
}

.counter {
  font-size: 1.8rem;
  color: #333333;
  font-weight: normal;
}

.progress-bar {
  height: 0.8rem;
  background: #ebeef5;
  border-radius: 0.4rem;
  overflow: hidden;
  margin-bottom: 4rem;
  box-shadow: inset 0 0.2rem 0.4rem rgba(0, 0, 0, 0.05);
}

.progress {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0.2rem 0.8rem rgba(102, 126, 234, 0.3);
}

.mark-progress {
  display: flex;
  align-items: flex-start;
  flex-direction: column;
  gap: 0.6rem;
  padding: 1.2rem 0 2rem;
  font-size: 1.4rem;
  color: #333;
  font-weight: 500;
}

.progress-primary {
  color: #667eea;
}

.warn-text {
  color: #e6a23c;
  line-height: 1.5;
}

.done-text {
  color: #67c23a;
}

.remaining-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
  max-height: 8.8rem;
  overflow-y: auto;
  padding-right: 0.4rem;
}

.remaining-chip {
  border: 0.1rem solid rgba(102, 126, 234, 0.35);
  background: rgba(102, 126, 234, 0.08);
  color: #4255c6;
  border-radius: 99.9rem;
  font-size: 1.2rem;
  font-weight: 600;
  padding: 0.6rem 1.2rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.remaining-chip:hover {
  background: rgba(102, 126, 234, 0.16);
  transform: translateY(-0.1rem);
}

.remaining-chip.active {
  background: rgba(102, 126, 234, 0.26);
  border-color: rgba(102, 126, 234, 0.75);
  box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.15) inset;
}

.flashcard {
  position: relative;
  margin: 4rem 0;
  perspective: 100rem;
  height: 50rem;
}

/* 3D 翻转容器 */
.flip-container {
  position: relative;
  width: 100%;
  height: 100%;
  transition: transform 0.6s cubic-bezier(0.6, 0.2, 0.4, 1);
  transform-style: preserve-3d;
}

.flip-container.no-flip {
  transition: none;
}

/* 翻转状态 */
.flip-container.flipped {
  transform: rotateY(180deg);
}

/* 内层翻转元素 */
.flip-inner {
  position: relative;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
}

/* 卡片正面 */
.card-face {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 1.2rem;
  padding: 8rem 6rem;
  min-height: 40rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1rem 3rem rgba(102, 126, 234, 0.2);
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

.card-face:hover {
  box-shadow: 0 1.6rem 4.8rem rgba(102, 126, 234, 0.3);
}

/* 卡片背面 */
.card-back {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 1.2rem;
  padding: 6rem 6rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  transform: rotateY(180deg);
  box-shadow: 0 1rem 3rem rgba(102, 126, 234, 0.2);
}

.back-content {
  text-align: center;
  width: 100%;
}

.favorite-btn-container {
  position: absolute;
  top: 2rem;
  right: 2rem;
  z-index: 10;
}

.favorite-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 4.4rem;
  height: 4.4rem;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.4rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(1rem);
}

.favorite-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.favorite-btn.active {
  background: rgba(245, 108, 108, 0.8);
  filter: drop-shadow(0 0.2rem 0.8rem rgba(245, 108, 108, 0.4));
}

.card-content {
  text-align: center;
}

.word-text {
  font-size: 4.8rem;
  margin: 0 0 1.2rem;
  font-weight: 700;
}

.kana-text {
  font-size: 2.4rem;
  margin: 0;
  opacity: 0.9;
}

.flip-hint {
  margin-top: 3rem;
  text-align: center;
  opacity: 0.8;
  animation: bounce 2s infinite;
}

.flip-hint p {
  margin: 0.5rem 0;
  font-size: 1.4rem;
}

.hint-text {
  font-size: 1.2rem;
  opacity: 0.7;
}

.status-badge {
  position: absolute;
  top: 1.5rem;
  left: 1.5rem;
  padding: 0.6rem 1.2rem;
  border-radius: 2rem;
  font-size: 1.2rem;
  font-weight: 600;
  color: white;
  box-shadow: 0 0.2rem 0.8rem rgba(0, 0, 0, 0.15);
}

.status-unknown {
  background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
}

.status-fuzzy {
  background: linear-gradient(135deg, #e6a23c 0%, #ebb563 100%);
}

.status-known {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.divider {
  border: none;
  border-top: 0.1rem solid rgba(255, 255, 255, 0.3);
  margin: 2rem 0;
}

.meaning-text {
  font-size: 3.2rem;
  margin: 0 0 1.2rem;
  font-weight: 600;
}

.pos {
  font-size: 1.6rem;
  opacity: 0.8;
  margin: 0 0 2.4rem;
  font-style: italic;
}

.example-box {
  background: rgba(255, 255, 255, 0.1);
  padding: 1.5rem;
  border-radius: 0.8rem;
  margin-top: 2rem;
}

.example-label {
  font-size: 1.2rem;
  margin: 0 0 0.8rem;
  opacity: 0.8;
}

.example-text {
  margin: 0;
  font-size: 1.4rem;
  line-height: 1.6;
}

.study-info {
  text-align: center;
  margin: 2.4rem 0;
  color: #222222;
  font-size: 1.6rem;
  font-weight: 500;
}

.review-mode-switch {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.6rem;
}

.mode-btn {
  border: 0.1rem solid #dcdfe6;
  background: #ffffff;
  color: #333333;
  border-radius: 99.9rem;
  padding: 0.8rem 1.4rem;
  font-size: 1.3rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.mode-btn.active {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.12);
  color: #4b60d0;
}

.mode-refresh-btn {
  margin-left: auto;
  border: 0.1rem solid #dcdfe6;
  background: #f5f7fa;
  color: #333333;
  border-radius: 0.8rem;
  padding: 0.8rem 1.2rem;
  font-size: 1.3rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-refresh-btn:hover {
  border-color: #667eea;
  color: #4b60d0;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  margin-top: 3rem;
  flex-wrap: wrap;
}

.btn {
  padding: 1.4rem 3.2rem;
  border: none;
  border-radius: 0.6rem;
  font-size: 1.8rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 600;
  box-shadow: 0 0.2rem 0.4rem rgba(0, 0, 0, 0.1);
}

.btn .el-icon {
  margin-right: 0.4rem;
}

.btn:active {
  transform: translateY(0.1rem);
  box-shadow: 0 0.1rem 0.2rem rgba(0, 0, 0, 0.1);
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 0.4rem 1.2rem rgba(102, 126, 234, 0.3);
}

.btn-primary:hover {
  background: linear-gradient(135deg, #7b92f4 0%, #8b5ac8 100%);
  box-shadow: 0 0.6rem 1.6rem rgba(102, 126, 234, 0.4);
  transform: translateY(-0.2rem);
}

.btn-secondary {
  background: #f0f2f5;
  color: #333;
  box-shadow: 0 0.2rem 0.4rem rgba(0, 0, 0, 0.05);
}

.btn-secondary:hover {
  background: #e4e7eb;
}

.btn-small {
  padding: 0.8rem 1.6rem;
  font-size: 1.4rem;
}

.btn-unknown {
  background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
  color: white;
  flex: 1;
  box-shadow: 0 0.4rem 1.2rem rgba(245, 108, 108, 0.3);
}

.btn-unknown:hover {
  background: linear-gradient(135deg, #f78989 0%, #fb9d9d 100%);
  box-shadow: 0 0.6rem 1.6rem rgba(245, 108, 108, 0.4);
  transform: translateY(-0.2rem);
}

.btn-fuzzy {
  background: linear-gradient(135deg, #e6a23c 0%, #ebb563 100%);
  color: white;
  flex: 1;
  box-shadow: 0 0.4rem 1.2rem rgba(230, 162, 60, 0.3);
}

.btn-fuzzy:hover {
  background: linear-gradient(135deg, #ebb563 0%, #f0c282 100%);
  box-shadow: 0 0.6rem 1.6rem rgba(230, 162, 60, 0.4);
  transform: translateY(-0.2rem);
}

.btn-known {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  color: white;
  flex: 1;
  box-shadow: 0 0.4rem 1.2rem rgba(103, 194, 58, 0.3);
}

.btn-known:hover {
  background: linear-gradient(135deg, #85ce61 0%, #a4d885 100%);
  box-shadow: 0 0.6rem 1.6rem rgba(103, 194, 58, 0.4);
  transform: translateY(-0.2rem);
}

.btn-disabled {
  opacity: 0.5;
  cursor: not-allowed !important;
  pointer-events: none;
}

.btn-disabled:hover {
  transform: none !important;
  box-shadow: 0 0.2rem 0.4rem rgba(0, 0, 0, 0.05) !important;
}

.keyboard-hints {
  text-align: center;
  margin-top: 2rem;
  color: #333333;
  font-size: 1.2rem;
}

.hint {
  display: inline-block;
  padding: 0.8rem 1.2rem;
  background: #f5f7fa;
  border-radius: 0.4rem;
  margin: 0 0.5rem;
}

.completion-state {
  position: relative;
  overflow: hidden;
  text-align: center;
  padding: 6rem 2rem;
}

.completion-content {
  position: relative;
  z-index: 2;
  margin-bottom: 4rem;
}

.celebration-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
}

.confetti-piece {
  --size: 1rem;
  position: absolute;
  top: -10%;
  left: calc((var(--i) * 5.4%) - 4%);
  width: var(--size);
  height: calc(var(--size) * 1.8);
  border-radius: 0.2rem;
  opacity: 0;
  background: hsl(calc(var(--i) * 20), 85%, 60%);
  transform: rotate(calc(var(--i) * 16deg));
  animation: confetti-fall 1.8s ease-in forwards;
  animation-delay: calc((var(--i) - 1) * 0.08s);
}

.celebration-glow {
  position: absolute;
  left: 50%;
  top: 35%;
  width: 22rem;
  height: 22rem;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(103, 194, 58, 0.28) 0%, rgba(64, 158, 255, 0.08) 50%, transparent 70%);
  animation: celebration-pulse 1.8s ease-out forwards;
}

.completion-icon {
  font-size: 6rem;
  margin: 0;
}

.completion-text {
  font-size: 2.4rem;
  color: #000000;
  margin: 2rem 0 0;
  font-weight: 500;
}

.button-group {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
  margin-top: 2rem;
  flex-wrap: wrap;
}

.stats-summary {
  background: linear-gradient(135deg, #f5f7fa 0%, #eef2f8 100%);
  border-radius: 0.8rem;
  padding: 2.4rem;
  margin-top: 2rem;
  border: 0.1rem solid #ebeef5;
}

.stats-summary h3 {
  margin-top: 0;
  color: #000000;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  margin-top: 2rem;
}

.stat {
  background: white;
  padding: 2rem;
  border-radius: 0.8rem;
  text-align: center;
  border: 0.1rem solid #ebeef5;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0.1rem 0.4rem rgba(0, 0, 0, 0.04);
}

.stat:hover {
  border-color: #667eea;
  box-shadow: 0 0.4rem 1.2rem rgba(102, 126, 234, 0.15);
  transform: translateY(-0.4rem);
}

.stat-label {
  display: block;
  color: #333333;
  font-size: 1.4rem;
  margin-bottom: 1rem;
}

.stat-number {
  display: block;
  font-size: 3.2rem;
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
  padding: 6rem 2rem;
}

.empty-icon {
  font-size: 6rem;
  margin: 0;
}

.empty-text {
  font-size: 1.8rem;
  color: #333333;
  margin: 1.5rem 0;
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
    transform: translateY(-1rem);
  }
}

@keyframes confetti-fall {
  0% {
    opacity: 0;
    transform: translateY(0) rotate(0deg);
  }
  10% {
    opacity: 1;
  }
  100% {
    opacity: 0;
    transform: translateY(32rem) rotate(540deg);
  }
}

@keyframes celebration-pulse {
  0% {
    opacity: 0.1;
    transform: translate(-50%, -50%) scale(0.75);
  }
  40% {
    opacity: 0.9;
    transform: translate(-50%, -50%) scale(1);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(1.2);
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .plan-info {
    grid-template-columns: 1fr;
  }
  
  .flashcard {
    height: 38rem;
  }
  
  .card-face,
  .card-back {
    padding: 4rem 2rem;
    min-height: 28rem;
  }
  
  .word-text {
    font-size: 2.8rem;
  }
  
  .meaning-text {
    font-size: 1.8rem;
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
