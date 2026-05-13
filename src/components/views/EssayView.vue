<template>
  <section class="view-section essay-view">
    <div class="essay-view-title" @mousemove.stop @pointermove.stop @touchmove.stop>
      <span>作文评价</span>
      <span class="badge">Dual Model</span>
    </div>

    <div class="essay-editor" @mousemove.stop @pointermove.stop @touchmove.stop>
      <el-card class="section-card">
        <template #header>
          <div class="card-header"><el-icon class="inline-icon"><EditPen /></el-icon> 写作练习</div>
        </template>

        <p class="hint">提交后将按 JLPT 风格异步生成评分报告和修改建议。</p>

        <div class="form-grid">
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

          <div class="form-group">
            <label for="target-level">目标等级：</label>
            <select v-model="targetLevel" class="topic-select">
              <option v-for="level in jlptLevels" :key="level" :value="level">
                {{ level }}
              </option>
            </select>
          </div>
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
            placeholder="请用日语写作..."
            rows="12"
            @input="updateWordCount"
          />
          <div class="word-count">
            <span>字数：{{ wordCount }}</span>
            <span class="target">目标：{{ targetLevel }}</span>
          </div>
        </div>

        <div class="button-group">
          <button @click="submitEssay" :disabled="!canSubmit" class="btn btn-submit">
            <span v-if="!isSubmitting"><el-icon class="inline-icon"><Promotion /></el-icon> 提交作文</span>
            <span v-else>提交中...</span>
          </button>
          <button @click="clearForm" class="btn btn-secondary">清空</button>
        </div>
      </el-card>
    </div>

    <div class="essays-history" @mousemove.stop @pointermove.stop @touchmove.stop>
      <el-card class="section-card">
        <template #header>
          <div class="card-header header-between">
            <span><el-icon class="inline-icon"><Collection /></el-icon> 作文历史记录</span>
            <el-button link type="primary" @click="loadEssayHistory()">
              <el-icon><RefreshRight /></el-icon>
              刷新
            </el-button>
          </div>
        </template>

        <div v-if="essays.length === 0" class="empty-wrap">
          <el-empty description="还没有提交任何作文，快去练习吧" />
        </div>

        <el-table v-else :data="essays" style="width: 100%" stripe>
          <el-table-column label="提交时间" min-width="160">
            <template #default="scope">
              {{ formatDate(scope.row.submitTime) }}
            </template>
          </el-table-column>
          <el-table-column label="话题" min-width="120">
            <template #default="scope">
              {{ scope.row.topic === 'custom' ? scope.row.title : getTopicLabel(scope.row.topic) }}
            </template>
          </el-table-column>
          <el-table-column label="目标等级" width="90">
            <template #default="scope">
              {{ scope.row.targetLevel }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="110">
            <template #default="scope">
              <el-tag :type="statusTagType(scope.row.status)" effect="light">
                {{ statusLabel(scope.row.status) }}
              </el-tag>
              <el-progress
                v-if="activeStatuses.has(scope.row.status)"
                class="table-progress"
                :percentage="essayProgressPercent(scope.row)"
                :show-text="false"
                :stroke-width="4"
              />
            </template>
          </el-table-column>
          <el-table-column label="总分" width="80">
            <template #default="scope">
              <template v-if="scope.row.scoreReport">
                <span class="score-value">{{ scope.row.scoreReport.overallScore }}</span>
              </template>
              <span v-else class="pending-text">--</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="scope">
              <el-button type="primary" link size="small" @click="viewHistoryDetail(scope.row)">详情报告</el-button>
              <el-button type="danger" link size="small" @click="confirmDeleteEssay(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-wrap" v-if="essayTotal > essayLimit">
          <el-pagination
            v-model:current-page="essayPage"
            :page-size="essayLimit"
            :total="essayTotal"
            layout="prev, pager, next"
            @current-change="onEssayPageChange"
          />
        </div>
      </el-card>
    </div>

    <el-card class="section-card" @mousemove.stop @pointermove.stop @touchmove.stop>
      <template #header>
        <div class="card-header"><el-icon class="inline-icon"><Opportunity /></el-icon> 写作建议</div>
      </template>
      <ul class="tips-list">
        <li>围绕题目展开，优先保证任务完成度。</li>
        <li>段落之间使用连接词，提升连贯性。</li>
        <li>先追求句子正确，再追求表达复杂度。</li>
        <li>报告会给出评分维度、错误摘要、逐句修改建议和修正版。</li>
      </ul>
    </el-card>

    <el-dialog v-model="historyDetailVisible" title="作文详细报告" width="880px">
      <div v-if="selectedHistoryItem" class="history-detail-body">
        <div class="detail-header">
          <div>
            <h3>{{ selectedHistoryItem.topic === 'custom' ? selectedHistoryItem.title : getTopicLabel(selectedHistoryItem.topic) }}</h3>
            <p>
              提交时间：{{ formatDate(selectedHistoryItem.submitTime) }}
              <span class="meta-divider">|</span>
              字数：{{ selectedHistoryItem.wordCount }}
              <span class="meta-divider">|</span>
              目标等级：{{ selectedHistoryItem.targetLevel }}
            </p>
          </div>
          <div class="detail-actions">
            <el-tag :type="statusTagType(selectedHistoryItem.status)" effect="light">
              {{ statusLabel(selectedHistoryItem.status) }}
            </el-tag>
            <el-button
              v-if="selectedHistoryItem.status === 'failed'"
              size="small"
              type="primary"
              @click="retryEvaluation(selectedHistoryItem.id)"
            >
              重新评测
            </el-button>
            <el-button
              v-else-if="selectedHistoryItem.status !== 'completed'"
              size="small"
              @click="refreshEssayReport(selectedHistoryItem.id)"
            >
              刷新状态
            </el-button>
          </div>
        </div>

        <template v-if="selectedHistoryItem.status === 'completed' && selectedHistoryItem.scoreReport">
          <div class="report-grid">
            <div class="score-card overall">
              <div class="score-card-label">总分</div>
              <div class="score-card-value">{{ selectedHistoryItem.scoreReport.overallScore }}</div>
              <div class="score-card-sub">{{ selectedHistoryItem.scoreReport.levelEstimate }}</div>
            </div>
            <div class="score-card">
              <div class="score-card-label">任务完成度</div>
              <div class="score-card-value small">{{ selectedHistoryItem.scoreReport.taskCompletionScore }}</div>
            </div>
            <div class="score-card">
              <div class="score-card-label">语法</div>
              <div class="score-card-value small">{{ selectedHistoryItem.scoreReport.grammarScore }}</div>
            </div>
            <div class="score-card">
              <div class="score-card-label">词汇</div>
              <div class="score-card-value small">{{ selectedHistoryItem.scoreReport.vocabularyScore }}</div>
            </div>
            <div class="score-card">
              <div class="score-card-label">连贯性</div>
              <div class="score-card-value small">{{ selectedHistoryItem.scoreReport.coherenceScore }}</div>
            </div>
            <div class="score-card">
              <div class="score-card-label">自然度</div>
              <div class="score-card-value small">{{ selectedHistoryItem.scoreReport.naturalnessScore }}</div>
            </div>
            <div class="score-card">
              <div class="score-card-label">等级匹配度</div>
              <div class="score-card-value small">{{ selectedHistoryItem.scoreReport.jlptFitScore }}</div>
            </div>
          </div>

          <div class="panel">
            <h4><el-icon><Finished /></el-icon> 评分总结</h4>
            <p>{{ selectedHistoryItem.scoreReport.summary }}</p>
            <p class="panel-muted">{{ selectedHistoryItem.scoreReport.comments }}</p>
          </div>

          <div v-if="selectedHistoryItem.revisionReport?.revisedScore" class="panel score-compare-panel">
            <h4><el-icon><TrendCharts /></el-icon> 修改前后分数对比</h4>
            <div class="score-compare-grid">
              <div class="compare-col">
                <div class="compare-label">修改前</div>
                <div class="compare-value">{{ selectedHistoryItem.scoreReport.overallScore }}</div>
                <div class="compare-sub">{{ selectedHistoryItem.scoreReport.levelEstimate }}</div>
              </div>
              <div class="compare-arrow">
                <el-icon :size="28" :color="scoreDeltaColor">
                  <ArrowRightBold />
                </el-icon>
              </div>
              <div class="compare-col">
                <div class="compare-label">修改后</div>
                <div class="compare-value" :class="scoreDeltaClass">{{ selectedHistoryItem.revisionReport.revisedScore.overallScore }}</div>
                <div class="compare-sub">{{ selectedHistoryItem.revisionReport.revisedScore.levelEstimate }}</div>
              </div>
              <div class="compare-delta">
                <el-tag :type="scoreDeltaType" effect="dark">
                  {{ scoreDeltaText }}
                </el-tag>
              </div>
            </div>
            <el-alert
              v-if="scoreDeltaNegative"
              title="修改后评分下降"
              type="warning"
              :description="`修正版评分(${selectedHistoryItem.revisionReport.revisedScore.overallScore}分) 低于原文评分(${selectedHistoryItem.scoreReport.overallScore}分)。建议手动检查修正内容，酌情采纳。`"
              show-icon
              :closable="false"
            />
          </div>

          <div v-if="selectedHistoryItem.revisionReport" class="panel">
            <h4><el-icon><MagicStick /></el-icon> 重点问题</h4>
            <div v-if="selectedHistoryItem.revisionReport.issues.length > 0" class="issue-list">
              <div v-for="(issue, index) in selectedHistoryItem.revisionReport.issues" :key="`${selectedHistoryItem.id}-issue-${index}`" class="issue-card">
                <div class="issue-source">{{ issue.source }}</div>
                <div class="issue-suggestion">建议：{{ issue.suggestion }}</div>
                <div class="issue-explanation">{{ issue.explanation }}</div>
              </div>
            </div>
            <el-empty v-else description="当前未生成重点问题列表" />
          </div>

          <div v-if="selectedHistoryItem.revisionReport" class="panel">
            <h4><el-icon><Edit /></el-icon> 逐句修改建议</h4>
            <div v-if="selectedHistoryItem.revisionReport.sentenceSuggestions.length > 0" class="sentence-list">
              <div
                v-for="(suggestion, index) in selectedHistoryItem.revisionReport.sentenceSuggestions"
                :key="`${selectedHistoryItem.id}-sentence-${index}`"
                class="sentence-card"
              >
                <div class="sentence-original">原句：{{ suggestion.original }}</div>
                <div class="sentence-suggested">建议：{{ suggestion.suggested }}</div>
                <div class="sentence-reason">{{ suggestion.reason }}</div>
              </div>
            </div>
            <el-empty v-else description="当前未生成逐句建议" />
          </div>

          <div v-if="selectedHistoryItem.revisionReport" class="panel">
            <h4><el-icon><DocumentChecked /></el-icon> 修正版</h4>
            <div class="content-box">{{ selectedHistoryItem.revisionReport.fullRevision }}</div>
            <p class="panel-muted">{{ selectedHistoryItem.revisionReport.revisionNotes }}</p>
          </div>

          <div
            v-if="selectedHistoryItem.revisionReport?.expandedRevision"
            class="panel"
          >
            <h4><el-icon><DocumentChecked /></el-icon> 扩写版</h4>
            <div class="content-box">{{ selectedHistoryItem.revisionReport.expandedRevision }}</div>
            <p class="panel-muted">该版本用于在不跑题的前提下补充细节和展开表达。</p>
          </div>

          <div
            v-if="selectedHistoryItem.revisionReport?.polishedRevision"
            class="panel"
          >
            <h4><el-icon><DocumentChecked /></el-icon> 润色版</h4>
            <div class="content-box">{{ selectedHistoryItem.revisionReport.polishedRevision }}</div>
            <p class="panel-muted">该版本用于在保持原意的前提下提升自然度和表达质量。</p>
          </div>

          <div class="panel">
            <h4><el-icon><Document /></el-icon> 原文内容</h4>
            <div class="content-box">{{ selectedHistoryItem.content }}</div>
          </div>
        </template>

        <template v-else-if="selectedHistoryItem.status === 'failed'">
          <el-result
            icon="error"
            title="评测失败"
            :sub-title="selectedHistoryItem.errorMessage || '模型服务未返回有效结果'"
          >
            <template #extra>
              <el-button type="primary" @click="retryEvaluation(selectedHistoryItem.id)">重新评测</el-button>
            </template>
          </el-result>
        </template>

        <template v-else>
          <div class="pending-panel">
            <el-icon class="loading-icon"><Loading /></el-icon>
            <div class="pending-title">{{ statusLabel(selectedHistoryItem.status) }}</div>
            <el-progress
              class="evaluation-progress"
              :percentage="essayProgressPercent(selectedHistoryItem)"
              :status="essayProgressStatus(selectedHistoryItem)"
              :stroke-width="10"
            />
            <p class="panel-muted">
              {{ selectedHistoryItem.errorMessage || essayProgressMessage(selectedHistoryItem) || '评分模型和修改模型正在异步处理中，完成后可直接查看完整报告。' }}
            </p>
            <el-button
              v-if="isModelWaiting(selectedHistoryItem)"
              size="small"
              type="primary"
              @click="autoRetryEvaluation(selectedHistoryItem.id)"
              :disabled="isRetrying"
            >
              {{ isRetrying ? '重试中...' : '立即重试' }}
            </el-button>
          </div>
        </template>
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
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ArrowRightBold,
  ChatDotRound,
  Collection,
  Document,
  DocumentChecked,
  Edit,
  EditPen,
  Finished,
  Loading,
  MagicStick,
  Opportunity,
  Promotion,
  RefreshRight,
  TrendCharts
} from '@element-plus/icons-vue'
import type { Essay } from '@/types'
import {
  deleteEssayAPI,
  getEssayHistoryAPI,
  getEssayReportAPI,
  isAuthenticated,
  requestEssayEvaluationAPI,
  submitEssayAPI
} from '@/api'

const topics = {
  'daily-life': '日常生活',
  travel: '旅行经历',
  hobbies: '爱好兴趣',
  family: '家庭成员',
  'future-plan': '未来计划',
  custom: '自定义话题'
}

const jlptLevels = ['N5', 'N4', 'N3', 'N2', 'N1']
const activeStatuses = new Set(['pending', 'scoring', 'revising'])

const selectedTopic = ref<string>('')
const customTopic = ref<string>('')
const targetLevel = ref<string>('N3')
const essayContent = ref<string>('')
const wordCount = ref<number>(0)
const isSubmitting = ref<boolean>(false)
const essays = ref<Essay[]>([])
const essayTotal = ref<number>(0)
const essayPage = ref<number>(1)
const essayLimit = 15
const historyDetailVisible = ref<boolean>(false)
const selectedHistoryItem = ref<Essay | null>(null)

let pollTimer: number | null = null

const canSubmit = computed(() => {
  const topic = selectedTopic.value === 'custom' ? customTopic.value.trim() : selectedTopic.value
  return topic.length > 0 && essayContent.value.trim().length > 0 && !isSubmitting.value
})

const hasActiveEssay = computed(() => essays.value.some(item => activeStatuses.has(item.status)))
const isRetrying = ref<boolean>(false)
let retryTimer: number | null = null

const isModelWaiting = (essay: Essay | null): boolean => {
  return !!essay && essay.status === 'pending' && (essay.errorMessage || '').includes('模型服务未就绪')
}

const scoreDelta = computed(() => {
  const report = selectedHistoryItem.value?.revisionReport
  const original = selectedHistoryItem.value?.scoreReport
  if (!report?.revisedScore || !original) return 0
  return report.revisedScore.overallScore - original.overallScore
})

const scoreDeltaType = computed<'success' | 'danger' | 'info'>(() => {
  if (scoreDelta.value > 0) return 'success'
  if (scoreDelta.value < 0) return 'danger'
  return 'info'
})

const scoreDeltaColor = computed(() => {
  if (scoreDelta.value > 0) return '#67c23a'
  if (scoreDelta.value < 0) return '#f56c6c'
  return '#909399'
})

const scoreDeltaText = computed(() => {
  const d = scoreDelta.value
  if (d > 0) return `+${d} 分`
  if (d < 0) return `${d} 分`
  return '持平'
})

const scoreDeltaNegative = computed(() => scoreDelta.value < 0)

const scoreDeltaClass = computed(() => {
  if (scoreDelta.value > 0) return 'improved'
  if (scoreDelta.value < 0) return 'declined'
  return ''
})

const updateWordCount = () => {
  wordCount.value = essayContent.value.length
}

const getTopicLabel = (topic: string): string => topics[topic as keyof typeof topics] || '自定义话题'

const statusLabel = (status: string): string => {
  switch (status) {
    case 'pending':
      return '待评测'
    case 'scoring':
      return '评分中'
    case 'revising':
      return '修改中'
    case 'completed':
      return '已完成'
    case 'failed':
      return '失败'
    default:
      return status
  }
}

const statusTagType = (status: string): '' | 'info' | 'warning' | 'success' | 'danger' => {
  switch (status) {
    case 'completed':
      return 'success'
    case 'failed':
      return 'danger'
    case 'scoring':
    case 'revising':
      return 'warning'
    default:
      return 'info'
  }
}

const essayProgressPercent = (essay: Essay | null): number => {
  if (!essay) return 0
  if (essay.status === 'completed' || essay.status === 'failed') return 100
  const reported = Number(essay.progressPercent ?? 0)
  if (reported > 0) return Math.min(100, Math.max(0, Math.round(reported)))
  switch (essay.status) {
    case 'scoring':
      return 25
    case 'revising':
      return 65
    default:
      return 0
  }
}

const essayProgressMessage = (essay: Essay | null): string => {
  if (!essay) return ''
  if (essay.progressMessage) return essay.progressMessage
  switch (essay.status) {
    case 'pending':
      return '已提交，等待评测开始'
    case 'scoring':
      return '正在生成评分报告'
    case 'revising':
      return '正在生成修改建议'
    case 'completed':
      return '评测完成'
    case 'failed':
      return '评测失败'
    default:
      return ''
  }
}

const essayProgressStatus = (essay: Essay | null): 'success' | 'exception' | 'warning' | undefined => {
  if (essay?.status === 'completed') return 'success'
  if (essay?.status === 'failed') return 'exception'
  return 'warning'
}

const formatDate = (timestamp: number): string => {
  if (!timestamp) return '--'
  return new Date(timestamp).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const replaceEssay = (essay: Essay) => {
  const index = essays.value.findIndex(item => item.id === essay.id)
  if (index >= 0) {
    essays.value.splice(index, 1, essay)
  } else {
    essays.value.unshift(essay)
  }
  if (selectedHistoryItem.value?.id === essay.id) {
    selectedHistoryItem.value = essay
  }
}

const stopPolling = () => {
  if (pollTimer !== null) {
    window.clearInterval(pollTimer)
    pollTimer = null
  }
}

const stopRetryTimer = () => {
  if (retryTimer !== null) {
    window.clearInterval(retryTimer)
    retryTimer = null
  }
}

const autoRetryEvaluation = async (essayId: string) => {
  isRetrying.value = true
  try {
    const essay = await requestEssayEvaluationAPI(essayId)
    replaceEssay(essay)
    await refreshEssayReport(essayId)
  } catch (error: any) {
    console.error('重试评测失败:', error)
  } finally {
    isRetrying.value = false
  }
}

const startAutoRetry = (essayId: string) => {
  stopRetryTimer()
  retryTimer = window.setInterval(async () => {
    if (isRetrying.value) return
    try {
      const essay = await requestEssayEvaluationAPI(essayId)
      replaceEssay(essay)
      if (essay.status === 'completed' || essay.status === 'failed') {
        stopRetryTimer()
      }
    } catch {
      // model still unavailable, keep retrying
    }
  }, 8000)
}

const ensurePolling = () => {
  if (!hasActiveEssay.value || pollTimer !== null) return
  pollTimer = window.setInterval(async () => {
    await loadEssayHistory(false)
  }, 4000)
}

const syncPollingState = () => {
  if (hasActiveEssay.value) ensurePolling()
  else stopPolling()
}

const loadEssayHistory = async (showMessage: boolean = false) => {
  try {
    const skip = (essayPage.value - 1) * essayLimit
    const result = await getEssayHistoryAPI(skip, essayLimit)
    const selectedId = selectedHistoryItem.value?.id
    essays.value = result.items
    essayTotal.value = result.total
    if (selectedId) {
      const latestSelected = result.items.find(item => item.id === selectedId)
      if (latestSelected) {
        selectedHistoryItem.value = latestSelected
      }
    }
    syncPollingState()
    if (showMessage) ElMessage.success('已刷新作文历史')
  } catch (error: any) {
    console.error('加载作文历史失败:', error)
    if (showMessage) ElMessage.error(error.message || '加载作文历史失败')
  }
}

const onEssayPageChange = (page: number) => {
  essayPage.value = page
  loadEssayHistory()
}

const refreshEssayReport = async (essayId: string, showMessage: boolean = false) => {
  try {
    const report = await getEssayReportAPI(essayId)
    replaceEssay(report.essay)
    syncPollingState()
    if (showMessage) ElMessage.success('已更新作文报告')
  } catch (error: any) {
    console.error('获取作文报告失败:', error)
    if (showMessage) ElMessage.error(error.message || '获取作文报告失败')
  }
}

const confirmDeleteEssay = async (item: Essay) => {
  try {
    const { ElMessageBox } = await import('element-plus')
    await ElMessageBox.confirm(
      '确定要删除这篇作文及其评测报告吗？此操作不可恢复。',
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteEssayAPI(item.id)
    essays.value = essays.value.filter(e => e.id !== item.id)
    if (selectedHistoryItem.value?.id === item.id) {
      historyDetailVisible.value = false
      selectedHistoryItem.value = null
    }
    ElMessage.success('作文已删除')
    essayTotal.value = Math.max(0, essayTotal.value - 1)
    // 如果当前页空了，回到前一页
    if (essays.value.length === 0 && essayPage.value > 1) {
      essayPage.value--
      await loadEssayHistory()
    }
  } catch (error: any) {
    if (error?.toString().includes('cancel')) return
    ElMessage.error(error.message || '删除失败')
  }
}

const viewHistoryDetail = async (item: Essay) => {
  selectedHistoryItem.value = item
  historyDetailVisible.value = true
  stopRetryTimer()
  await refreshEssayReport(item.id)
  if (isModelWaiting(item)) {
    startAutoRetry(item.id)
  }
}

const submitEssay = async () => {
  if (!isAuthenticated()) {
    ElMessage.warning('请先登录才能提交作文')
    window.dispatchEvent(new CustomEvent('open-login-dialog'))
    return
  }

  if (!canSubmit.value) return

  isSubmitting.value = true
  try {
    const topic = selectedTopic.value === 'custom' ? customTopic.value.trim() : selectedTopic.value
    const essay = await submitEssayAPI({
      title: topic,
      topic: selectedTopic.value,
      content: essayContent.value.trim(),
      wordCount: wordCount.value,
      targetLevel: targetLevel.value
    })
    essays.value.unshift(essay)
    clearForm()
    syncPollingState()
    ElMessage.success('作文已提交，正在生成评分报告和修改建议')
  } catch (error: any) {
    ElMessage.error(error.message || '提交作文失败')
  } finally {
    isSubmitting.value = false
  }
}

const retryEvaluation = async (essayId: string) => {
  try {
    const essay = await requestEssayEvaluationAPI(essayId)
    replaceEssay(essay)
    syncPollingState()
    ElMessage.success('已重新触发作文评测')
  } catch (error: any) {
    ElMessage.error(error.message || '重新评测失败')
  }
}

const clearForm = () => {
  selectedTopic.value = ''
  customTopic.value = ''
  targetLevel.value = 'N3'
  essayContent.value = ''
  wordCount.value = 0
}

watch(historyDetailVisible, (visible) => {
  if (!visible) stopRetryTimer()
})

onMounted(async () => {
  await loadEssayHistory()
})

onBeforeUnmount(() => {
  stopPolling()
  stopRetryTimer()
})
</script>

<style scoped>
.essay-view {
  animation: slideUp 0.3s ease;
}

.essay-view-title {
  color: #8b4513;
  font-size: 24px;
  margin-bottom: 10px;
}

.badge {
  font-size: 12px;
  background: #f0f9eb;
  color: #000;
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
  color: #000;
}

.header-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.inline-icon {
  vertical-align: middle;
  margin-right: 4px;
}

.hint {
  color: #333;
  margin-bottom: 20px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #000;
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
.topic-input:focus,
.essay-textarea:focus {
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

.word-count {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #333;
}

.target {
  color: #606266;
}

.empty-wrap {
  padding: 40px 20px;
  text-align: center;
}

.score-value {
  color: #67c23a;
  font-weight: 700;
}

.pending-text {
  color: #909399;
}

.table-progress {
  width: 72px;
  margin-top: 6px;
}

.tips-list {
  margin: 0;
  padding-left: 20px;
  color: #333;
  font-size: 14px;
  line-height: 1.8;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;
}

.detail-header h3 {
  margin: 0 0 8px;
  color: #303133;
}

.detail-header p {
  margin: 0;
  color: #909399;
  font-size: 13px;
}

.meta-divider {
  margin: 0 8px;
}

.detail-actions {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.report-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.score-card {
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  background: #fafafa;
}

.score-card.overall {
  background: linear-gradient(135deg, #fef6e8 0%, #fff 100%);
  border-color: #f2d5a5;
}

.score-card-label {
  font-size: 12px;
  color: #909399;
}

.score-card-value {
  margin-top: 6px;
  font-size: 34px;
  line-height: 1;
  font-weight: 700;
  color: #303133;
}

.score-card-value.small {
  font-size: 26px;
}

.score-card-sub {
  margin-top: 8px;
  font-size: 13px;
  color: #e6a23c;
}

.panel {
  margin-bottom: 18px;
  padding: 18px;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  background: #fff;
}

.panel h4 {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 12px;
  color: #303133;
}

.panel p {
  margin: 0;
  line-height: 1.8;
  color: #303133;
}

.panel-muted {
  margin-top: 10px !important;
  color: #909399 !important;
  font-size: 13px;
}

.score-compare-panel {
  background: linear-gradient(135deg, #f0f9eb 0%, #fff 100%);
  border-color: #c2e7b0;
}

.score-compare-grid {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 10px 0;
}

.compare-col {
  text-align: center;
  min-width: 100px;
}

.compare-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 6px;
}

.compare-value {
  font-size: 36px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
}

.compare-value.improved {
  color: #67c23a;
}

.compare-value.declined {
  color: #f56c6c;
}

.compare-sub {
  font-size: 13px;
  color: #e6a23c;
  margin-top: 6px;
}

.compare-arrow {
  display: flex;
  align-items: center;
}

.compare-delta {
  min-width: 70px;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  padding: 16px 0 8px;
}

.issue-list,
.sentence-list {
  display: grid;
  gap: 12px;
}

.issue-card,
.sentence-card {
  padding: 14px;
  border-radius: 10px;
  background: #f7f9fc;
  border: 1px solid #e4e7ed;
}

.issue-source,
.sentence-original {
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}

.issue-suggestion,
.sentence-suggested {
  color: #409eff;
  margin-bottom: 6px;
}

.issue-explanation,
.sentence-reason {
  color: #606266;
  line-height: 1.7;
}

.content-box {
  padding: 15px;
  background: #f8f9fa;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-word;
}

.pending-panel {
  padding: 40px 20px;
  text-align: center;
}

.loading-icon {
  font-size: 28px;
  color: #e6a23c;
  animation: spin 1.2s linear infinite;
}

.pending-title {
  margin-top: 12px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.evaluation-progress {
  max-width: 420px;
  margin: 18px auto 0;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .detail-header {
    flex-direction: column;
  }

  .report-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
