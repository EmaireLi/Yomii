<template>
  <section class="search-view">
    <el-card class="header-card">
      <h1>日语查词</h1>
    </el-card>
    
    <!-- 搜索框 -->
    <el-card class="search-card">
      <div class="search-box">
        <el-row :gutter="10">
          <el-col :xs="24" :sm="24" :md="20" :lg="20">
            <el-input
              v-model="searchQuery"
              placeholder="输入日语假名、汉字或中文..."
              @keyup.enter="handleSearch"
              clearable
            >
              <template #prefix>
                <span>🔍</span>
              </template>
            </el-input>
          </el-col>
          <el-col :xs="24" :sm="24" :md="4" :lg="4">
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
    <el-card v-if="isLoading" class="state-card">
      <el-empty description="搜索中..." image="search" />
    </el-card>

    <!-- 错误信息 -->
    <el-card v-else-if="errorMessage" class="state-card">
      <el-alert :title="errorMessage" type="error" />
    </el-card>

    <!-- 搜索结果 -->
    <div v-else-if="searchResult.length > 0" class="results">
      <el-card class="result-info">
        <template #header>
          <div class="card-header">
            <span>找到 <el-tag>{{ searchResult.length }}</el-tag> 个结果</span>
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
              <p class="meaning"><strong>释义：</strong> {{ word.meaning }}</p>
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
    </div>

    <!-- 未找到 -->
    <el-card v-else-if="hasSearched" class="state-card">
      <el-empty description="未找到相关词汇" />
    </el-card>

    <!-- 初始状态 -->
    <el-card v-else class="state-card">
      <el-empty description="输入词汇开始查询" />
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElNotification } from 'element-plus'
import { VideoPlay, DocumentCopy, Star, StarFilled } from '@element-plus/icons-vue'
import type { Word } from '@/types'
import { searchWords as searchWordsAPI } from '@/api'
import { useSearchHistory, useFavorites } from '@/composables/useLocalStorage'

const searchQuery = ref('')
const searchResult = ref<Word[]>([])
const hasSearched = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')
const hoveredWordId = ref<string | null>(null)

const { searchHistory, addSearch, removeSearch } = useSearchHistory()
const { isFavorited, toggleFavorite } = useFavorites()

/**
 * 执行搜索
 */
const handleSearch = async () => {
  hasSearched.value = true
  errorMessage.value = ''
  
  if (!searchQuery.value.trim()) {
    searchResult.value = []
    return
  }
  
  isLoading.value = true
  try {
    searchResult.value = await searchWordsAPI(searchQuery.value)
    addSearch(searchQuery.value)
  } catch (error: any) {
    errorMessage.value = error.message || '搜索失败，请稍后重试'
    searchResult.value = []
  } finally {
    isLoading.value = false
  }
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
