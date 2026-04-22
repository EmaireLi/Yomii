<template>
  <section class="favorites-view">
    <el-card class="header-card"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <h1>我的收藏</h1>
    </el-card>

    <!-- 加载中 -->
    <el-card v-if="isLoading" class="state-card"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <div class="loading-container">
        <div class="spinner"></div>
        <p class="loading-text">正在加载收藏</p>
      </div>
    </el-card>

    <!-- 错误信息 -->
    <el-card v-else-if="errorMessage" class="state-card"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <el-alert :title="errorMessage" type="error" />
    </el-card>

    <!-- 收藏列表 -->
    <div v-else-if="favorites.length > 0" class="results"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <el-card class="result-info">
        <template #header>
          <div class="card-header">
            <div class="stats-container">
              <div class="stat-item">
                <span class="stat-label">共</span>
                <span class="stat-value">{{ totalFavorites }}</span>
                <span class="stat-label">个收藏</span>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-item">
                <span class="stat-label">第</span>
                <span class="stat-value">{{ currentPage }}</span>
                <span class="stat-label">/</span>
                <span class="stat-value">{{ totalPages }}</span>
                <span class="stat-label">页</span>
              </div>
            </div>
          </div>
        </template>
      </el-card>
      
      <el-row :gutter="20" class="result-list">
        <el-col v-for="word in favorites" :key="word.id" :xs="24" :md="12" :lg="12">
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
                @click="removeFavorite(word.id)"
                class="favorite-btn active"
                type="danger"
              >
                <el-icon>
                  <StarFilled />
                </el-icon>
              </el-button>
            </div>
            
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

      <div class="pagination-wrapper" v-if="totalFavorites > pageSize">
        <el-pagination
          background
          layout="prev, pager, next, jumper"
          :current-page="currentPage"
          :page-size="pageSize"
          :total="totalFavorites"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 未找到 -->
    <el-card v-else class="state-card"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <el-empty description="还没有收藏词汇" />
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { ElNotification, ElMessage } from 'element-plus'
import { VideoPlay, DocumentCopy, StarFilled } from '@element-plus/icons-vue'
import type { Word } from '@/types'
import { getFavorites, removeFromFavorites, isAuthenticated } from '@/api'

const favorites = ref<Word[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const totalFavorites = ref(0)
const isLoading = ref(false)
const errorMessage = ref('')
const hoveredWordId = ref<string | null>(null)

const totalPages = computed(() => {
  if (totalFavorites.value === 0) return 1
  return Math.ceil(totalFavorites.value / pageSize.value)
})

/**
 * 加载收藏列表
 */
const loadFavorites = async (page: number = currentPage.value) => {
  if (!isAuthenticated()) {
    ElMessage.warning('请先登录才能查看收藏')
    window.dispatchEvent(new CustomEvent('open-login-dialog'))
    return
  }

  isLoading.value = true
  errorMessage.value = ''
  try {
    const result = await getFavorites(page, pageSize.value)
    favorites.value = result.words
    totalFavorites.value = result.total
    currentPage.value = result.page
  } catch (error: any) {
    errorMessage.value = error.message || '加载收藏失败，请稍后重试'
    favorites.value = []
    totalFavorites.value = 0
  } finally {
    isLoading.value = false
  }
}

/**
 * 移除收藏
 */
const removeFavorite = async (wordId: string) => {
  try {
    await removeFromFavorites(wordId)
    ElNotification({
      title: '成功',
      message: '已取消收藏',
      type: 'success',
      duration: 2000
    })
    await loadFavorites()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  }
}

const handlePageChange = async (page: number) => {
  currentPage.value = page
  await loadFavorites()
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
  loadFavorites()
})
</script>

<style scoped>
.favorites-view {
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
  gap: 24px;
  width: 100%;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
}

.stat-label {
  color: #606266;
  font-weight: 400;
}

.stat-value {
  color: #409eff;
  font-weight: 600;
  font-size: 18px;
  padding: 2px 8px;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 4px;
  min-width: 45px;
  text-align: center;
}

.stat-divider {
  width: 1px;
  height: 24px;
  background: #dcdfe6;
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
  display: flex;
  flex-direction: column;
  min-height: 420px;
  max-height: 420px;
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
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
  flex-shrink: 0;
}

.word-info {
  flex: 1;
  min-width: 0;
}

.word-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #000000;
  font-weight: 600;
  word-break: break-all;
}

.kana {
  margin: 0 0 8px 0;
  color: #333333;
  font-size: 15px;
  word-break: break-all;
}

.favorite-btn {
  font-size: 20px !important;
  padding: 0 !important;
  flex-shrink: 0;
}

.result-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 16px;
  flex: 1;
  overflow-y: auto;
  min-height: 0;
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
  margin-top: 4px;
}

.result-actions {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #ebeef5;
  flex-shrink: 0;
  background: #f9f9f9;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  gap: 20px;
}

.spinner {
  width: 60px;
  height: 60px;
  border: 4px solid #f0f0f0;
  border-top: 4px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-text {
  margin: 0;
  font-size: 18px;
  color: #333333;
  font-weight: 500;
  letter-spacing: 2px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes slideUp {
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
