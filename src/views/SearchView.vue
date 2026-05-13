<template>
  <section class="search-view">
    <el-card class="header-card"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <h1>日语查词</h1>
    </el-card>
    
    <!-- 搜索框 -->
    <el-card class="search-card"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <div class="search-box">
        <el-row :gutter="10">
          <el-col :xs="24" :sm="24" :md="16" :lg="16">
            <el-input
              v-model="searchQuery"
              placeholder="输入日语假名、汉字或中文..."
              @keyup.enter="handleSearch"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :xs="24" :sm="12" :md="4" :lg="4">
            <el-select
              v-model="searchLimit"
              class="limit-select"
              @change="handleLimitChange"
            >
              <el-option
                v-for="option in limitOptions"
                :key="option"
                :label="`${option} 条/页`"
                :value="option"
              />
            </el-select>
          </el-col>
          <el-col :xs="24" :sm="12" :md="4" :lg="4">
            <el-button
              type="primary"
              @click="handleSearch"
              :loading="isLoading"
              class="search-btn"
            >
              搜索
            </el-button>
          </el-col>
        </el-row>
        
        <div v-if="historyRecords.length > 0" class="search-history">
          <div class="history-header">
            <button class="history-toggle" @click="historyExpanded = !historyExpanded">
              <span class="history-label">最近搜索</span>
              <span class="history-toggle-text">{{ historyExpanded ? '收起' : '展开' }}</span>
            </button>
            <div class="history-actions">
              <el-button text class="history-link-btn" @click="historyDrawerVisible = true">
                查看全部
              </el-button>
              <el-button text class="history-link-btn danger" @click="handleClearHistory">
                清空历史
              </el-button>
            </div>
          </div>
          <div v-if="historyExpanded" class="history-preview-list">
            <div
              v-for="record in visibleHistoryRecords"
              :key="record.id"
              class="history-preview-item"
            >
              <button class="history-item-main preview" @click="applyHistorySearch(record.keyword)">
                <span class="history-item-keyword">{{ record.keyword }}</span>
                <span class="history-item-meta">
                  {{ formatHistoryMeta(record.resultCount, record.createdAt) }}
                </span>
              </button>
              <el-button
                text
                class="history-delete-btn"
                @click="handleRemoveHistoryKeyword(record.keyword)"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 加载中 -->
    <el-card v-if="isLoading" class="state-card"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <div class="loading-container">
        <div class="spinner"></div>
        <p class="loading-text">正在查询单词</p>
      </div>
    </el-card>

    <!-- 错误信息 -->
    <el-card v-else-if="errorMessage" class="state-card"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <el-alert :title="errorMessage" type="error" />
    </el-card>

    <!-- 搜索结果 -->
    <div v-else-if="searchResult.length > 0" class="results"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <el-card class="result-info">
        <template #header>
          <div class="card-header">
            <div class="stats-container">
              <div class="stat-item">
                <span class="stat-label">找到</span>
                <span class="stat-value">{{ searchTotal }}</span>
                <span class="stat-label">个单词</span>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-item">
                <span class="stat-label">第</span>
                <span class="stat-value">{{ searchPage }}</span>
                <span class="stat-label">/</span>
                <span class="stat-value">{{ totalPages }}</span>
                <span class="stat-label">页</span>
              </div>
            </div>
          </div>
        </template>
      </el-card>
      
      <el-row :gutter="20" class="result-list">
        <el-col v-for="word in searchResult" :key="word.id" :xs="24" :md="12" :lg="12">
          <el-card
            class="result-card"
            shadow="hover"
            @mouseenter="hoveredWordId = word.id"
            @mouseleave="hoveredWordId = null"
          >
            <div class="result-header">
              <div class="word-info">
                <h2 class="word-title">{{ word.word }}</h2>
                <p class="kana">[{{ word.kana }}]</p>
                <el-tag v-if="word.partOfSpeech" type="info" size="small">
                  {{ word.partOfSpeech }}
                </el-tag>
              </div>
              <el-button
                text
                @click="toggleFavorite(word.id)"
                class="favorite-btn"
                :type="isFavorited(word.id) ? 'danger' : 'info'"
              >
                <el-icon>
                  <component :is="isFavorited(word.id) ? StarFilled : Star" />
                </el-icon>
              </el-button>
            </div>
            
            <el-divider margin="1.6rem 0" />
            
            <div class="result-body">
              <p class="meaning"><strong>中文释义：</strong> {{ word.chineseMeaning || '暂无' }}</p>
              <p class="meaning"><strong>日文释义：</strong> {{ word.japaneseMeaning }}</p>
              <p v-if="word.example" class="example"><strong>例句：</strong> {{ word.example }}</p>
              <div v-if="word.tags && word.tags.length > 0" class="tags">
                <el-tag v-for="tag in word.tags" :key="tag" size="small">
                  {{ tag }}
                </el-tag>
              </div>
            </div>

            <el-divider margin="1.6rem 0" />

            <div class="result-actions">
              <el-button
                size="small"
                @click="copyToClipboard(word.word)"
                text
              >
                <el-icon><DocumentCopy /></el-icon>
                <span>复制</span>
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <div class="pagination-wrapper" v-if="searchTotal > searchLimit">
        <el-pagination
          background
          layout="prev, pager, next, jumper"
          :current-page="searchPage"
          :page-size="searchLimit"
          :total="searchTotal"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 未找到 -->
    <el-card v-else-if="hasSearched" class="state-card"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <el-empty description="未找到相关词汇" />
    </el-card>

    <!-- 初始状态 -->
    <el-card v-else class="state-card"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <el-empty description="输入词汇开始查询" />
    </el-card>

    <el-drawer
      v-model="historyDrawerVisible"
      title="查询历史"
      size="42rem"
      class="history-drawer"
    >
      <div class="history-drawer-body">
        <div class="drawer-toolbar">
          <span class="drawer-summary">共 {{ historyRecords.length }} 条历史</span>
          <el-button text class="history-link-btn danger" @click="handleClearHistory">
            清空历史
          </el-button>
        </div>

        <el-empty v-if="historyRecords.length === 0" description="暂无查询历史" />

        <div v-else class="history-list">
          <div
            v-for="record in historyRecords"
            :key="record.id"
            class="history-list-item"
          >
            <button class="history-item-main" @click="applyHistorySearch(record.keyword)">
              <span class="history-item-keyword">{{ record.keyword }}</span>
              <span class="history-item-meta">
                {{ formatHistoryMeta(record.resultCount, record.createdAt) }}
              </span>
            </button>
            <el-button text class="history-delete-btn" @click="handleRemoveHistoryKeyword(record.keyword)">
              删除
            </el-button>
          </div>
        </div>
      </div>
    </el-drawer>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElNotification, ElMessage } from 'element-plus'
import { Search, DocumentCopy, Star, StarFilled } from '@element-plus/icons-vue'
import type { Word } from '@/types'
import { searchWords as searchWordsAPI, isAuthenticated } from '@/api'
import { useSearchHistory, useFavorites } from '@/composables/useLocalStorage'

const searchQuery = ref('')
const searchResult = ref<Word[]>([])
const searchPage = ref(1)
const searchLimit = ref(10)
const searchTotal = ref(0)
const limitOptions = [10, 20, 50, 100]
const hasSearched = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')
const hoveredWordId = ref<string | null>(null)
const historyDrawerVisible = ref(false)
const historyExpanded = ref(false)
const totalPages = computed(() => {
  if (searchTotal.value === 0) return 1
  return Math.ceil(searchTotal.value / searchLimit.value)
})

const { historyRecords, addSearch, removeSearch, clearHistory } = useSearchHistory()
const { isFavorited, toggleFavorite: originalToggleFavorite } = useFavorites()
const visibleHistoryRecords = computed(() => historyRecords.value.slice(0, 5))

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

/**
 * 执行搜索
 */
const loadSearchPage = async (saveHistory: boolean = false) => {
  isLoading.value = true
  try {
    const payload = await searchWordsAPI(searchQuery.value, searchPage.value, searchLimit.value)
    searchResult.value = payload.words
    searchTotal.value = payload.total
    searchPage.value = payload.page
    if (saveHistory) {
      await addSearch(searchQuery.value)
    }
  } catch (error: any) {
    errorMessage.value = error.message || '搜索失败，请稍后重试'
    searchResult.value = []
    searchTotal.value = 0
  } finally {
    isLoading.value = false
  }
}

const handleSearch = async () => {
  if (!isAuthenticated()) {
    ElMessage.warning('请先登录才能搜索')
    window.dispatchEvent(new CustomEvent('open-login-dialog'))
    return
  }

  hasSearched.value = true
  errorMessage.value = ''
  
  if (!searchQuery.value.trim()) {
    searchResult.value = []
    searchTotal.value = 0
    searchPage.value = 1
    return
  }

  searchPage.value = 1
  await loadSearchPage(true)
}

const handlePageChange = async (page: number) => {
  searchPage.value = page
  await loadSearchPage(false)
}

const handleLimitChange = async () => {
  if (!hasSearched.value || !searchQuery.value.trim()) return
  searchPage.value = 1
  await loadSearchPage(false)
}

const applyHistorySearch = async (keyword: string) => {
  searchQuery.value = keyword
  historyDrawerVisible.value = false
  await handleSearch()
}

const formatHistoryMeta = (resultCount: number, createdAt: number) => {
  const formattedTime = new Date(createdAt).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
  return `${resultCount} 条结果 · ${formattedTime}`
}

const copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text).then(() => {
    ElNotification({
      title: '成功',
      message: '已复制: ' + text,
      type: 'success',
      duration: 2000
    })
  })
}

const handleRemoveHistoryKeyword = async (keyword: string) => {
  try {
    await removeSearch(keyword)
  } catch (error: any) {
    ElMessage.error(error?.message || '删除历史失败')
  }
}

const handleClearHistory = async () => {
  try {
    await clearHistory()
    historyDrawerVisible.value = false
    ElMessage.success('查询历史已清空')
  } catch (error: any) {
    ElMessage.error(error?.message || '清空历史失败')
  }
}
</script>

<style scoped>
.search-view {
  display: flex;
  flex-direction: column;
  gap: 2.4rem;
  animation: slideUp 0.3s ease;
}

.header-card h1 {
  margin: 0;
  font-size: 2.8rem;
  color: #000000;
  font-weight: 700;
}

.search-card {
  border-radius: 0.8rem;
  box-shadow: 0 0.2rem 1.2rem rgba(0, 0, 0, 0.08);
  border: none;
  background: white;
}

.search-box {
  display: flex;
  flex-direction: column;
  gap: 1.6rem;
}

.search-btn {
  width: 100%;
  height: 4rem;
  font-weight: 500;
  border-radius: 0.4rem;
}

.limit-select {
  width: 100%;
}

.search-history {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 1.2rem;
  flex-wrap: wrap;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.2rem;
  flex-wrap: wrap;
}

.history-toggle {
  display: inline-flex;
  align-items: center;
  gap: 1rem;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
}

.history-actions {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.history-label {
  font-size: 1.6rem;
  color: #333333;
  font-weight: 600;
  line-height: 1.8rem;
}

.history-toggle-text {
  color: #409eff;
  font-size: 1.4rem;
  font-weight: 500;
}

.history-preview-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.history-preview-item,
.history-list-item {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  min-height: 5.6rem;
  padding: 1.2rem 1.4rem;
  border: 0.1rem solid #ebeef5;
  border-radius: 1rem;
  background: #ffffff;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.history-preview-item:hover,
.history-list-item:hover {
  border-color: #c6e2ff;
  box-shadow: 0 0.4rem 1.2rem rgba(64, 158, 255, 0.08);
}

.history-link-btn {
  padding: 0 !important;
  font-size: 1.4rem;
}

.history-link-btn.danger,
.history-delete-btn {
  color: #f56c6c !important;
}

.history-drawer-body {
  display: flex;
  flex-direction: column;
  gap: 1.6rem;
}

.drawer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.2rem;
}

.drawer-summary {
  color: #606266;
  font-size: 1.3rem;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.history-item-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
  padding: 0;
}

.history-item-main.preview {
  min-width: 0;
}

.history-item-keyword {
  color: #303133;
  font-size: 1.5rem;
  font-weight: 600;
  word-break: break-all;
}

.history-item-meta {
  color: #909399;
  font-size: 1.2rem;
}

.history-delete-btn {
  flex-shrink: 0;
  padding: 0 !important;
  font-size: 1.3rem;
}

.state-card {
  border-radius: 0.8rem;
  box-shadow: 0 0.2rem 1.2rem rgba(0, 0, 0, 0.08);
  border: none;
  color: #000000;
}

.result-info {
  border-radius: 0.8rem;
  box-shadow: 0 0.2rem 1.2rem rgba(0, 0, 0, 0.08);
  border: none;
  padding: 0 !important;
}

:deep(.result-info .el-card__body) {
  padding: 0 !important;
  display: none;
}

.card-header {
  padding: 0;
  display: flex;
  align-items: center;
  width: 100%;
}

.stats-container {
  display: flex;
  align-items: center;
  gap: 2.4rem;
  width: 100%;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 1.5rem;
}

.stat-label {
  color: #606266;
  font-weight: 400;
}

.stat-value {
  color: #409eff;
  font-weight: 600;
  font-size: 1.8rem;
  padding: 0.2rem 0.8rem;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 0.4rem;
  min-width: 4.5rem;
  text-align: center;
}

.stat-divider {
  width: 0.1rem;
  height: 2.4rem;
  background: #dcdfe6;
}

@media (max-width: 768px) {
  .stats-container {
    gap: 1.6rem;
  }

  .stat-value {
    font-size: 1.6rem;
  }
}

.results {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.result-list {
  margin: 0;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 1.2rem;
}

.result-card {
  border-radius: 0.8rem;
  border: 0.1rem solid #ebeef5;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  background: white;
  color: #000000;
}

.result-card:hover {
  border-color: #667eea;
  box-shadow: 0 0.4rem 1.6rem rgba(102, 126, 234, 0.2);
  transform: translateY(-0.2rem);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1.5rem;
}

.word-info {
  flex: 1;
}

.word-title {
  margin: 0 0 0.8rem 0;
  font-size: 2.4rem;
  color: #000000;
  font-weight: 600;
}

.kana {
  margin: 0 0 0.8rem 0;
  color: #333333;
  font-size: 1.5rem;
}

.favorite-btn {
  font-size: 2rem !important;
  padding: 0 !important;
}

.result-body {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.meaning, .example {
  margin: 0;
  color: #333333;
  font-size: 1.4rem;
  line-height: 1.6;
}

.tags {
  display: flex;
  gap: 0.8rem;
  flex-wrap: wrap;
}

.result-actions {
  display: flex;
  gap: 0.8rem;
}

.search-box {
  margin-bottom: 2rem;
}

.search-input-wrapper {
  display: flex;
  gap: 0.8rem;
  margin-bottom: 1rem;
}

.search-input {
  flex: 1;
  padding: 1rem 1.2rem;
  border: 0.1rem solid #dcdfe6;
  border-radius: 0.4rem;
  font-size: 1.4rem;
  outline: none;
  transition: border-color 0.3s;
}

.search-input:focus {
  border-color: #409eff;
  box-shadow: 0 0 0 0.2rem rgba(64, 158, 255, 0.2);
}

.search-btn {
  padding: 0 2rem;
  background-color: #409eff;
  color: #fff;
  border: none;
  border-radius: 0.4rem;
  font-size: 1.4rem;
  cursor: pointer;
  transition: background-color 0.3s;
  white-space: nowrap;
}

.search-btn:hover {
  background-color: #66b1ff;
}

.results {
  animation: slideIn 0.3s ease;
}

.result-count {
  color: #333333;
  margin-bottom: 2rem;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.result-card {
  background: #fdfdfd;
  border: 0.1rem solid #ebeef5;
  border-radius: 0.8rem;
  padding: 1.2rem;
  transition: all 0.3s;
}

.result-card:hover {
  box-shadow: 0 0.2rem 1.2rem rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  gap: 1.5rem;
}

.word-info {
  flex: 1;
}

.word-info h2 {
  margin: 0 1.5rem;
  font-size: 2.8rem;
  color: #000000;
}

.kana {
  margin: 0 0 0.5rem;
  color: #333333;
  font-size: 1.6rem;
}

.pos {
  margin: 0;
  color: #333333;
  font-size: 1.4rem;
}

.favorite-btn {
  background: none;
  border: none;
  font-size: 2.4rem;
  cursor: pointer;
  transition: transform 0.3s;
  opacity: 0.5;
}

.favorite-btn:hover {
  transform: scale(1.2);
}

.favorite-btn.active {
  opacity: 1;
}

.result-body {
  margin-bottom: 1.5rem;
}

.meaning,
.example {
  margin: 0 0 1rem;
  color: #333333;
  line-height: 1.6;
}

.tags {
  display: flex;
  gap: 0.8rem;
  flex-wrap: wrap;
}

.tag {
  display: inline-block;
  padding: 0.4rem 1.2rem;
  background: #f0f9ff;
  color: #409eff;
  border-radius: 1.2rem;
  font-size: 1.2rem;
}

.result-actions {
  display: flex;
  gap: 1rem;
  padding-top: 1.5rem;
  border-top: 0.1rem solid #ebeef5;
}

.action-btn {
  padding: 0.6rem 1.5rem;
  background: #f5f7fa;
  color: #333333;
  border: 0.1rem solid #dcdfe6;
  border-radius: 0.4rem;
  cursor: pointer;
  font-size: 1.4rem;
  transition: all 0.3s;
}

.action-btn:hover {
  background: #409eff;
  color: white;
  border-color: #409eff;
}

.empty-state,
.initial-state {
  text-align: center;
  padding: 6rem 2rem;
  color: #333333;
}

.empty-icon,
.init-icon {
  font-size: 4.8rem;
  display: block;
  margin-bottom: 1.5rem;
}

.empty-text,
.init-text {
  font-size: 1.8rem;
  font-weight: 500;
  margin: 0 0 1rem;
}

.empty-hint {
  font-size: 1.4rem;
  margin: 0;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8rem 2rem;
  gap: 2rem;
}

.spinner {
  width: 6rem;
  height: 6rem;
  border: 0.4rem solid #f0f0f0;
  border-top: 0.4rem solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-text {
  margin: 0;
  font-size: 1.8rem;
  color: #333333;
  font-weight: 500;
  letter-spacing: 0.2rem;
}

@media (max-width: 768px) {
  .history-preview-item,
  .history-list-item {
    align-items: flex-start;
  }

  .history-delete-btn {
    align-self: center;
  }
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
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
</style>
