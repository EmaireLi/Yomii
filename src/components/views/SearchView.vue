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
        
        <div v-if="searchHistory.length > 0" class="search-history">
          <span class="history-label">最近搜索：</span>
          <el-tag
            v-for="(history, idx) in searchHistory.slice(0, 5)"
            :key="idx"
            @click="searchQuery = history; handleSearch()"
            closable
            @close="removeSearch(idx)"
            class="history-tag"
            style="cursor: pointer; margin-top: 8px;"
          >
            {{ history }}
          </el-tag>
        </div>
      </div>
    </el-card>

    <!-- 加载中 -->
    <el-card v-if="isLoading" class="state-card"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <el-empty description="搜索中..." image="search" />
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
            <span>
              共 <el-tag>{{ searchTotal }}</el-tag> 个结果，
              第 <el-tag>{{ searchPage }}</el-tag> / <el-tag>{{ totalPages }}</el-tag> 页
            </span>
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
            
            <el-divider margin="16px 0" />
            
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

            <el-divider margin="16px 0" />

            <div class="result-actions">
              <el-button
                v-if="word.audioUrl"
                type="primary"
                size="small"
                @click="playAudio(word.audioUrl)"
                text
              >
                <el-icon><VideoPlay /></el-icon>
                <span>听发音</span>
              </el-button>
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
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElNotification, ElMessage } from 'element-plus'
import { Search, VideoPlay, DocumentCopy, Star, StarFilled } from '@element-plus/icons-vue'
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
const totalPages = computed(() => {
  if (searchTotal.value === 0) return 1
  return Math.ceil(searchTotal.value / searchLimit.value)
})

const { searchHistory, addSearch, removeSearch } = useSearchHistory()
const { isFavorited, toggleFavorite: originalToggleFavorite, syncFavorites } = useFavorites()

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
  } catch (error: any) {
    ElMessage.error(error?.message || '收藏操作失败')
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
      addSearch(searchQuery.value)
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

const playAudio = (url: string) => {
  console.log('Playing audio:', url)
  ElNotification({
    title: '提示',
    message: '音频播放功能开发中',
    type: 'info'
  })
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

onMounted(() => {
  if (isAuthenticated()) {
    void syncFavorites()
  }
})
</script>

<style scoped>
.search-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
  animation: slideUp 0.3s ease;
}

.header-card h1 {
  margin: 0;
  font-size: 28px;
  color: #000000;
  font-weight: 700;
}

.search-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: none;
  background: white;
}

.search-box {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.search-btn {
  width: 100%;
  height: 40px;
  font-weight: 500;
  border-radius: 4px;
}

.limit-select {
  width: 100%;
}

.search-history {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.history-label {
  font-size: 13px;
  color: #333333;
}

.history-tag {
  cursor: pointer;
  user-select: none;
}

.state-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: none;
  color: #000000;
}

.result-info {
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: none;
}

.card-header {
  padding: 0;
  display: flex;
  align-items: center;
}

.results {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.result-list {
  margin: 0;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 12px;
}

.result-card {
  border-radius: 8px;
  border: 1px solid #ebeef5;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  background: white;
  color: #000000;
}

.result-card:hover {
  border-color: #667eea;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2);
  transform: translateY(-2px);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 15px;
}

.word-info {
  flex: 1;
}

.word-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #000000;
  font-weight: 600;
}

.kana {
  margin: 0 0 8px 0;
  color: #333333;
  font-size: 15px;
}

.favorite-btn {
  font-size: 20px !important;
  padding: 0 !important;
}

.result-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meaning, .example {
  margin: 0;
  color: #333333;
  font-size: 14px;
  line-height: 1.6;
}

.tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.search-box {
  margin-bottom: 20px;
}

.search-input-wrapper {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.search-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s;
}

.search-input:focus {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.search-btn {
  padding: 0 20px;
  background-color: #409eff;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s;
  white-space: nowrap;
}

.search-btn:hover {
  background-color: #66b1ff;
}

.search-history {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.history-label {
  font-size: 14px;
  color: #333333;
}

.history-tag {
  padding: 4px 12px;
  background: #f0f9ff;
  color: #409eff;
  border: 1px solid #b3d8ff;
  border-radius: 16px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.history-tag:hover {
  background: #409eff;
  color: white;
}

.results {
  animation: slideIn 0.3s ease;
}

.result-count {
  color: #333333;
  margin-bottom: 20px;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.result-card {
  background: #fdfdfd;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  transition: all 0.3s;
}

.result-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
  gap: 15px;
}

.word-info {
  flex: 1;
}

.word-info h2 {
  margin: 0 015px;
  font-size: 28px;
  color: #000000;
}

.kana {
  margin: 0 0 5px;
  color: #333333;
  font-size: 16px;
}

.pos {
  margin: 0;
  color: #333333;
  font-size: 14px;
}

.favorite-btn {
  background: none;
  border: none;
  font-size: 24px;
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
  margin-bottom: 15px;
}

.meaning,
.example {
  margin: 0 0 10px;
  color: #333333;
  line-height: 1.6;
}

.tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag {
  display: inline-block;
  padding: 4px 12px;
  background: #f0f9ff;
  color: #409eff;
  border-radius: 12px;
  font-size: 12px;
}

.result-actions {
  display: flex;
  gap: 10px;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.action-btn {
  padding: 6px 15px;
  background: #f5f7fa;
  color: #333333;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
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
  padding: 60px 20px;
  color: #333333;
}

.empty-icon,
.init-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 15px;
}

.empty-text,
.init-text {
  font-size: 18px;
  font-weight: 500;
  margin: 0 0 10px;
}

.empty-hint {
  font-size: 14px;
  margin: 0;
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
</style>
