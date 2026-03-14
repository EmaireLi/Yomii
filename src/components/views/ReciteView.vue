<template>
  <section class="view-section recite-view">
    <h1>背单词 <span class="counter">{{ currentIndex + 1 }} / {{ words.length }}</span></h1>
    
    <!-- 进度条 -->
    <div class="progress-bar">
      <div class="progress" :style="{ width: progressPercent + '%' }"></div>
    </div>

    <!-- 闪卡 -->
    <div class="flashcard" v-if="currentWord">
      <!-- 正面 -->
      <div class="card-face">
        <div class="card-content">
          <h2 class="word-text">{{ currentWord.word }}</h2>
          <p class="kana-text" v-if="showMeaning">[{{ currentWord.kana }}]</p>
        </div>

        <!-- 翻转提示 -->
        <div v-if="!showMeaning" class="flip-hint" @click="toggleCard">
          <p>点击或按空格键</p>
          <p class="hint-text">查看释义</p>
        </div>

        <!-- 背面 -->
        <transition name="flip">
          <div v-if="showMeaning" class="card-back">
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
      <div v-if="showMeaning" class="study-info">
        <p>选择您对这个词汇的掌握程度</p>
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <button
          v-if="!showMeaning"
          @click="toggleCard"
          class="btn btn-primary"
        >
          查看释义 (Space)
        </button>
        <template v-else>
          <button @click="nextWord('unknown')" class="btn btn-unknown">
            ❌ 不认识
          </button>
          <button @click="nextWord('fuzzy')" class="btn btn-fuzzy">
            🤔 模糊
          </button>
          <button @click="nextWord('known')" class="btn btn-known">
            ✓ 认识
          </button>
        </template>
      </div>

      <!-- 快捷键提示 -->
      <div class="keyboard-hints">
        <span v-if="!showMeaning" class="hint">按 Space 翻转卡片</span>
        <template v-else>
          <span class="hint">1: 不认识 | 2: 模糊 | 3: 认识</span>
        </template>
      </div>
    </div>

    <!-- 完成状态 -->
    <div v-else class="completion-state">
      <div class="completion-content">
        <p class="completion-icon">🎉</p>
        <p class="completion-text">恭喜！已完成所有词汇</p>
        <button @click="resetCards" class="btn btn-primary" style="margin-top: 20px;">
          重新开始
        </button>
        <button @click="shuffleCards" class="btn btn-secondary">
          打乱顺序再来一遍
        </button>
      </div>

      <!-- 学习统计 -->
      <div class="stats-summary">
        <h3>本轮学习总结</h3>
        <div class="stats-grid">
          <div class="stat">
            <span class="stat-label">掌握</span>
            <span class="stat-number known">{{ stats.known }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">模糊</span>
            <span class="stat-number fuzzy">{{ stats.fuzzy }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">未掌握</span>
            <span class="stat-number unknown">{{ stats.unknown }}</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import type { Word } from '@/types'
import { getRandomWordsAPI } from '@/api'
import { useWordProgress, useStudyStats } from '@/composables/useLocalStorage'

const words = ref<Word[]>([])
const currentIndex = ref(0)
const showMeaning = ref(false)
const isLoading = ref(false)

const { updateProgress } = useWordProgress()
const { incrementRecited } = useStudyStats()

const stats = reactive({
  known: 0,
  fuzzy: 0,
  unknown: 0
})

const currentWord = computed(() => words.value[currentIndex.value] || null)

const progressPercent = computed(() => {
  if (words.value.length === 0) return 0
  return (currentIndex.value / words.value.length) * 100
})

const toggleCard = () => {
  showMeaning.value = !showMeaning.value
}

const nextWord = async (status: 'unknown' | 'fuzzy' | 'known') => {
  if (currentWord.value) {
    // 更新进度
    updateProgress(currentWord.value.id, status)
    incrementRecited()

    // 更新统计
    stats[status]++

    // 移到下一个词
    showMeaning.value = false
    currentIndex.value++
  }
}

const loadNewWords = async () => {
  isLoading.value = true
  try {
    words.value = await getRandomWordsAPI(10)
  } catch (error) {
    console.error('Failed to load words:', error)
    words.value = []
  } finally {
    isLoading.value = false
  }
}

const resetCards = async () => {
  stats.known = 0
  stats.fuzzy = 0
  stats.unknown = 0
  currentIndex.value = 0
  showMeaning.value = false
  await loadNewWords()
}

const shuffleCards = () => {
  words.value = [...words.value].sort(() => Math.random() - 0.5)
  currentIndex.value = 0
  showMeaning.value = false
  stats.known = 0
  stats.fuzzy = 0
  stats.unknown = 0
}

// 键盘快捷键
const handleKeyboard = (event: KeyboardEvent) => {
  if (event.code === 'Space') {
    event.preventDefault()
    toggleCard()
  } else if (showMeaning.value && event.code === 'Digit1') {
    nextWord('unknown')
  } else if (showMeaning.value && event.code === 'Digit2') {
    nextWord('fuzzy')
  } else if (showMeaning.value && event.code === 'Digit3') {
    nextWord('known')
  }
}

onMounted(() => {
  loadNewWords()
  window.addEventListener('keydown', handleKeyboard)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyboard)
})
</script>

<style scoped>
.recite-view h1 {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.counter {
  font-size: 18px;
  color: #909399;
  font-weight: normal;
}

.progress-bar {
  height: 6px;
  background: #ebeef5;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 40px;
}

.progress {
  height: 100%;
  background: linear-gradient(90deg, #409eff, #66b1ff);
  transition: width 0.3s ease;
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
  transition: all 0.3s ease;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  position: relative;
}

.card-face:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
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
  color: #909399;
  font-size: 14px;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
  margin: 20px 0;
}

.btn {
  padding: 10px 18px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 500;
}

.btn-primary {
  background: #409eff;
  color: white;
}

.btn-primary:hover {
  background: #66b1ff;
}

.btn-unknown {
  background: #f56c6c;
  color: white;
}

.btn-unknown:hover {
  background: #f78989;
}

.btn-fuzzy {
  background: #e6a23c;
  color: white;
}

.btn-fuzzy:hover {
  background: #ebb563;
}

.btn-known {
  background: #67c23a;
  color: white;
}

.btn-known:hover {
  background: #85ce61;
}

.btn-secondary {
  background: #f5f7fa;
  color: #606266;
  border: 1px solid #dcdfe6;
}

.btn-secondary:hover {
  background: #ebeef5;
}

.keyboard-hints {
  text-align: center;
  font-size: 12px;
  color: #909399;
  margin-top: 20px;
}

.hint {
  display: inline-block;
  padding: 6px 12px;
  background: #f5f7fa;
  border-radius: 16px;
}

.completion-state {
  padding: 20px 15px;
  text-align: center;
}

.completion-content {
  background: #f0f9ff;
  padding: 25px;
  border-radius: 12px;
  border: 2px solid #b3d8ff;
  margin-bottom: 25px;
}

.completion-icon {
  font-size: 48px;
  margin: 0 0 15px;
}

.completion-text {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.stats-summary {
  background: #fdfdfd;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.stats-summary h3 {
  margin-top: 0;
  color: #303133;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-top: 20px;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.stat-number {
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

@keyframes flip {
  0% {
    transform: rotateY(-90deg);
    opacity: 0;
  }
  100% {
    transform: rotateY(0);
    opacity: 1;
  }
}

.flip-enter-active {
  animation: flip 0.3s ease;
}
</style>
