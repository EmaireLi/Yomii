<template>
  <section class="view-section search-view">
    <h1>日语查词</h1>
    
    <!-- 搜索框 -->
    <div class="search-box">
      <div class="search-input-wrapper">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="输入日语假名、汉字或中文..."
          @keyup.enter="handleSearch"
          class="search-input"
        />
        <button @click="handleSearch" class="search-btn">搜索</button>
      </div>
      <div v-if="searchHistory.length > 0" class="search-history">
        <span class="history-label">最近搜索：</span>
        <button
          v-for="(history, idx) in searchHistory.slice(0, 5)"
          :key="idx"
          @click="searchQuery = history; handleSearch()"
          class="history-tag"
        >
          {{ history }}
        </button>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-if="isLoading" class="loading-state">
      <p class="loading-icon">⏳</p>
      <p class="loading-text">搜索中...</p>
    </div>

    <div v-else-if="errorMessage" class="error-state">
      <p class="error-icon">⚠️</p>
      <p class="error-text">{{ errorMessage }}</p>
    </div>

    <div v-else-if="searchResult.length > 0" class="results">
      <h3 class="result-count">找到 {{ searchResult.length }} 个结果</h3>
      <div class="result-list">
        <div
          v-for="word in searchResult"
          :key="word.id"
          class="result-card"
        >
          <div class="result-header">
            <div class="word-info">
              <h2>{{ word.word }}</h2>
              <p class="kana">[{{ word.kana }}]</p>
              <p v-if="word.partOfSpeech" class="pos">{{ word.partOfSpeech }}</p>
            </div>
            <button
              @click="toggleFavorite(word.id)"
              :class="['favorite-btn', { active: isFavorited(word.id) }]"
              title="加入收藏"
            >
              ❤️
            </button>
          </div>
          
          <div class="result-body">
            <p class="meaning"><strong>释义：</strong> {{ word.meaning }}</p>
            <p v-if="word.example" class="example"><strong>例句：</strong> {{ word.example }}</p>
            <div v-if="word.tags && word.tags.length > 0" class="tags">
              <span v-for="tag in word.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </div>

          <div class="result-actions">
            <button 
              v-if="word.audioUrl"
              @click="playAudio(word.audioUrl)"
              class="action-btn"
              title="播放发音"
            >
              🔊 听发音
            </button>
            <button class="action-btn" @click="copyToClipboard(word.word)">
              📋 复制
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="hasSearched" class="empty-state">
      <p class="empty-icon">🔍</p>
      <p class="empty-text">未找到相关词汇</p>
      <p class="empty-hint">请尝试其他关键词或使用不同的搜索方式</p>
    </div>

    <!-- 初始状态 -->
    <div v-else class="initial-state">
      <p class="init-icon">📚</p>
      <p class="init-text">输入词汇开始查询</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Word } from '@/types'
import { searchWords as searchWordsAPI } from '@/api'
import { useSearchHistory, useFavorites } from '@/composables/useLocalStorage'

const searchQuery = ref('')
const searchResult = ref<Word[]>([])
const hasSearched = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')

const { searchHistory, addSearch } = useSearchHistory()
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
  // TODO: 实现音频播放功能
}

const copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text).then(() => {
    alert('已复制: ' + text)
  })
}
</script>

<style scoped>
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
  color: #909399;
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
  color: #909399;
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
  color: #303133;
}

.kana {
  margin: 0 0 5px;
  color: #606266;
  font-size: 16px;
}

.pos {
  margin: 0;
  color: #909399;
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
  color: #606266;
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
  color: #606266;
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
  color: #909399;
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
