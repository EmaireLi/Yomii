<template>
  <section class="view-section essay-view">
    <div class="essay-view-title"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <span>作文评价</span> 
      <span class="badge">AI Ready</span>
    </div>

    <!-- 编辑和提交作文 -->
    <div v-if="!showEvaluationOnly" class="essay-editor"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <el-card class="section-card">
        <template #header>
          <div class="card-header"><el-icon class="inline-icon"><EditPen /></el-icon> 写作练习</div>
        </template>
        <p class="hint">请用日语写一篇短文，最少 200 字。支持未来 AI 自动评分。</p>

        <div class="form-group">
          <label for="topic">选择话题：</label>
          <select v-model="selectedTopic" class="topic-select">
            <option value="">-- 选择一个话题 --</option>
            <option value="daily-life">日常生活</option>
            <option value="travel">旅行经历</option>
            <option value="hobbies">爱好兴趣</option>
            <option value="family">家庭成员</option>
            <option value="future-plan">未来计划</option>
            <option value="custom">自定义话题</option>
          </select>
        </div>

        <div v-if="selectedTopic === 'custom'" class="form-group">
          <label for="custom-topic">自定义话题：</label>
          <input
            v-model="customTopic"
            type="text"
            class="topic-input"
            placeholder="输入你的话题..."
          />
        </div>

        <div class="form-group">
          <label for="essay-content">作文内容：</label>
          <textarea
            v-model="essayContent"
            class="essay-textarea"
            placeholder="请用日语写作...（最少 200 字）"
            rows="12"
            @input="updateWordCount"
          ></textarea>
          <div class="word-count">
            <span :class="{ warning: wordCount < 200 }">
              字数：{{ wordCount }} / 最少 200
            </span>
          </div>
        </div>

        <div class="button-group">
          <button
            @click="submitEssay"
            :disabled="!canSubmit"
            class="btn btn-submit"
          >
            <span v-if="!isSubmitting"><el-icon class="inline-icon"><Promotion /></el-icon> 提交作文</span>
            <span v-else>提交中...</span>
          </button>
          <button @click="clearForm" class="btn btn-secondary">
            清空
          </button>
        </div>
      </el-card>
    </div>

    <!-- 评分结果展示 -->
    <div v-if="essays.length > 0" class="essays-history"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <el-card class="section-card">
        <template #header>
          <div class="card-header"><el-icon class="inline-icon"><Collection /></el-icon> 作文历史</div>
        </template>

      <div class="empty-state" v-if="essays.length === 0">
        <p>还没有提交任何作文</p>
      </div>

      <div v-for="essay in essays" :key="essay.id" class="essay-item">
        <div class="essay-header">
          <div>
            <div class="essay-title">{{ essay.topic === 'custom' ? essay.title : getTopicLabel(essay.topic) }}</div>
            <p class="meta"><el-icon class="inline-icon"><Calendar /></el-icon> {{ formatDate(essay.submitTime) }} | <el-icon class="inline-icon"><Memo /></el-icon> {{ essay.wordCount }} 字</p>
          </div>
          <button
            @click="selectEssay(essay)"
            :class="['btn btn-view', { active: selectedEssay?.id === essay.id }]"
          >
            <span v-if="essay.score">查看评分</span>
            <span v-else><el-icon class="inline-icon"><Loading /></el-icon> 等待评分</span>
          </button>
        </div>


        <!-- 评分结果 -->
        <transition name="expand">
          <div v-if="selectedEssay?.id === essay.id && essay.score" class="score-detail">
            <div class="score-summary">
              <div class="main-score">
                <div class="score-number">{{ essay.score.overallScore }}</div>
                <div class="score-label">总分</div>
              </div>

              <div class="score-breakdown">
                <div class="score-item">
                  <span class="score-label">语法</span>
                  <div class="score-bar">
                    <div class="score-fill" :style="{ width: essay.score.gramarScore + '%' }"></div>
                  </div>
                  <span class="score-value">{{ essay.score.gramarScore }}</span>
                </div>

                <div class="score-item">
                  <span class="score-label">词汇</span>
                  <div class="score-bar">
                    <div class="score-fill" :style="{ width: essay.score.vocabularyScore + '%' }"></div>
                  </div>
                  <span class="score-value">{{ essay.score.vocabularyScore }}</span>
                </div>

                <div class="score-item">
                  <span class="score-label">流畅度</span>
                  <div class="score-bar">
                    <div class="score-fill" :style="{ width: essay.score.fluencyScore + '%' }"></div>
                  </div>
                  <span class="score-value">{{ essay.score.fluencyScore }}</span>
                </div>

                <div class="score-item">
                  <span class="score-label">连贯性</span>
                  <div class="score-bar">
                    <div class="score-fill" :style="{ width: essay.score.coherenceScore + '%' }"></div>
                  </div>
                  <span class="score-value">{{ essay.score.coherenceScore }}</span>
                </div>
              </div>
            </div>

            <!-- 评论 -->
            <div class="comments-section">
              <h4><el-icon class="inline-icon"><ChatDotRound /></el-icon> 评论反馈</h4>
              <p class="comment-text">{{ essay.score.comments }}</p>
              <p class="ai-note" v-if="essay.score.aiEvaluated">
                <el-icon class="inline-icon"><Opportunity /></el-icon> 本评分由 AI 系统生成（{{ formatDate(essay.score.evaluationTime) }}）
              </p>
            </div>

            <!-- 原文 -->
            <div class="essay-content-view">
              <h4><el-icon class="inline-icon"><Document /></el-icon> 原文</h4>
              <div class="content-box">
                {{ essay.content }}
              </div>
            </div>
          </div>
        </transition>
      </div>
    </el-card>
    </div>

    <!-- 提示 -->
    <el-card class="section-card"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <template #header>
        <div class="card-header"><el-icon class="inline-icon"><Opportunity /></el-icon> 写作建议</div>
      </template>
      <ul>
        <li>确保内容与选定话题相关</li>
        <li>使用正确的日语语法和表达</li>
        <li>字数不少于 200，更详细的内容会获得更高分</li>
        <li>使用多样的词汇和句式</li>
        <li>AI 评分系统正在优化中，目前支持人工评分和样本评分</li>
      </ul>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { EditPen, Promotion, Collection, Calendar, Memo, Loading, ChatDotRound, Opportunity, Document } from '@element-plus/icons-vue'
import type { Essay, EssayScore } from '@/types'
import { submitEssayAPI, getEssayHistoryAPI, generateMockEssayScore } from '@/api'

/**
 * 话题选项
 */
const topics = {
  'daily-life': '日常生活',
  'travel': '旅行经历',
  'hobbies': '爱好兴趣',
  'family': '家庭成员',
  'future-plan': '未来计划',
  'custom': '自定义话题'
}

/**
 * 编辑器状态
 */
const selectedTopic = ref<string>('')
const customTopic = ref<string>('')
const essayContent = ref<string>('')
const wordCount = ref<number>(0)
const isSubmitting = ref<boolean>(false)

/**
 * 历史记录和评分
 */
const essays = ref<Essay[]>([])
const selectedEssay = ref<Essay | null>(null)
const showEvaluationOnly = ref<boolean>(false)

/**
 * 获取话题统计标签
 */
const getTopicLabel = (topic: string): string => {
  return topics[topic as keyof typeof topics] || '自定义话题'
}

/**
 * 是否可以提交
 */
const canSubmit = computed(() => {
  const topic = selectedTopic.value === 'custom' ? customTopic.value : selectedTopic.value
  return topic && wordCount.value >= 200 && !isSubmitting.value
})

/**
 * 更新字数统计
 */
const updateWordCount = () => {
  wordCount.value = essayContent.value.length
}

/**
 * 提交作文
 */
const submitEssay = async () => {
  if (!canSubmit.value) return

  isSubmitting.value = true

  try {
    const topic = selectedTopic.value === 'custom' ? customTopic.value : selectedTopic.value
    
    // 调用 API 提交作文
    const essay = await submitEssayAPI({
      title: topic,
      topic: selectedTopic.value,
      content: essayContent.value,
      wordCount: wordCount.value
    })

    essays.value.unshift(essay)

    // 模拟 AI 评分（真实环境中由后端处理）
    setTimeout(async () => {
      const score = generateMockEssayScore(essay.id)
      const updatedEssay = essays.value.find(e => e.id === essay.id)
      if (updatedEssay) {
        updatedEssay.score = score
        selectedEssay.value = updatedEssay
      }
    }, 1500)

    // 清空表单
    clearForm()
  } catch (error: any) {
    alert(`提交失败: ${error.message}`)
  } finally {
    isSubmitting.value = false
  }
}

/**
 * 清空表单
 */
const clearForm = () => {
  selectedTopic.value = ''
  customTopic.value = ''
  essayContent.value = ''
  wordCount.value = 0
}

/**
 * 选择作文查看详情
 */
const selectEssay = (essay: Essay) => {
  selectedEssay.value = selectedEssay.value?.id === essay.id ? null : essay
}

/**
 * 格式化日期
 */
const formatDate = (timestamp: number): string => {
  const date = new Date(timestamp)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

/**
 * 加载历史作文
 */
const loadEssayHistory = async () => {
  try {
    essays.value = await getEssayHistoryAPI()
  } catch (error) {
    console.error('加载作文历史失败:', error)
  }
}

// 页面加载时获取历史记录
loadEssayHistory()
</script>

<style scoped>
.essay-view {
  animation: slideUp 0.3s ease;
}

.essay-view-title {
  color: #8B4513;
  font-size: 24px;
  margin-bottom: 10px;
}

.badge {
  font-size: 12px;
  background: #f0f9eb;
  color: #000000;
  padding: 4px 8px;
  border-radius: 4px;
  margin-left: 8px;
}

.section-card {
  margin-bottom: 20px;
}

.card-header {
  font-size: 18px;
  font-weight: 600;
  color: #000000;
}

.inline-icon {
  vertical-align: middle;
  margin-right: 4px;
}

.hint {
  color: #333333;
  margin-bottom: 25px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #000000;
}

.topic-select,
.topic-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.3s;
}

.topic-select:focus,
.topic-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.essay-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  font-size: 14px;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  resize: vertical;
  transition: border-color 0.3s;
}

.essay-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.word-count {
  margin-top: 8px;
  text-align: right;
  font-size: 12px;
  color: #333333;
}

.word-count .warning {
  color: #f56c6c;
  font-weight: 600;
}

.essays-history {
  margin-top: 40px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #333333;
}

.essay-item {
  background: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 15px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.essay-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}

.essay-title {
  margin: 0 0 8px;
  color: #000000;
  font-size: 16px;
  font-weight: 600;
}

.essay-header .meta {
  margin: 0;
  font-size: 12px;
  color: #333333;
}

.btn-view {
  flex-shrink: 0;
}

.score-detail {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
  animation: slideDown 0.3s ease;
}

.score-summary {
  display: flex;
  gap: 30px;
  margin-bottom: 30px;
}

.main-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 120px;
  height: 120px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.score-number {
  font-size: 48px;
  font-weight: 700;
  line-height: 1;
}

.score-label {
  font-size: 12px;
  margin-top: 8px;
  opacity: 0.9;
}

.score-breakdown {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.score-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.score-item .score-label {
  font-size: 13px;
  font-weight: 600;
  color: #333333;
}

.score-bar {
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 0.5s ease;
}

.score-value {
  font-size: 13px;
  font-weight: 600;
  color: #667eea;
}

.comments-section {
  margin-bottom: 25px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.comments-section h4 {
  margin: 0 0 10px;
  color: #000000;
  font-size: 14px;
}

.comment-text {
  margin: 0 0 10px;
  color: #333333;
  line-height: 1.6;
}

.ai-note {
  margin: 0;
  font-size: 12px;
  color: #222222;
  font-style: italic;
}

.essay-content-view {
  margin-top: 25px;
  padding: 15px;
  background: #fafafa;
  border-left: 4px solid #667eea;
  border-radius: 4px;
}

.essay-content-view h4 {
  margin: 0 0 10px;
  color: #000000;
  font-size: 14px;
}

.content-box {
  color: #333333;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
}

.tips-section {
  background: #ecf5ff;
  padding: 20px;
  border-radius: 12px;
  margin-top: 40px;
  border-left: 4px solid #667eea;
}

.tips-section h3 {
  margin-top: 0;
  color: #667eea;
  font-size: 16px;
}

.tips-section ul {
  margin: 10px 0 0;
  padding-left: 20px;
  color: #333333;
  font-size: 14px;
  line-height: 1.8;
}

.tips-section li {
  margin-bottom: 8px;
}

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 1000px;
  }
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
}

.expand-enter-from {
  opacity: 0;
  max-height: 0;
}

.expand-leave-to {
  opacity: 0;
  max-height: 0;
}
</style>
