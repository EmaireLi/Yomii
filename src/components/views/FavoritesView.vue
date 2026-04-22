<template>
  <section class="favorites-view">
    <el-card class="header-card">
      <h1>我的收藏</h1>
      <p class="subtitle">按收藏时间倒序展示（最新收藏在前）</p>
    </el-card>

    <el-card class="search-card">
      <el-row :gutter="10">
        <el-col :xs="24" :sm="24" :md="16" :lg="16">
          <el-input
            v-model="searchQuery"
            clearable
            placeholder="搜索已收藏词汇（词语/假名/中文/日文释义）"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="4" :lg="4">
          <el-select v-model="pageSize" class="limit-select" @change="handleLimitChange">
            <el-option v-for="option in pageSizeOptions" :key="option" :label="`${option} 条/页`" :value="option" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="4" :lg="4">
          <el-button type="primary" class="search-btn" :loading="isLoading" @click="handleSearch">
            搜索
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card v-if="isLoading" class="state-card">
      <el-empty description="加载收藏中..." />
    </el-card>

    <el-card v-else-if="errorMessage" class="state-card">
      <el-alert :title="errorMessage" type="error" />
    </el-card>

    <el-card v-else-if="favorites.length === 0" class="state-card">
      <el-empty :description="searchQuery.trim() ? '未找到匹配的收藏词汇' : '暂无收藏词汇'" />
    </el-card>

    <div v-else class="favorites-content">
      <el-card class="count-card">
        共 <el-tag type="danger">{{ total }}</el-tag> 个收藏词汇
      </el-card>

      <el-row :gutter="20">
        <el-col v-for="word in favorites" :key="word.id" :xs="24" :md="12" :lg="12">
          <el-card class="word-card" shadow="hover">
            <div class="word-header">
              <div>
                <h2 class="word-title">{{ word.word }}</h2>
                <p class="kana">[{{ word.kana }}]</p>
              </div>
              <el-button type="danger" text @click="removeFavorite(word.id)">
                取消收藏
              </el-button>
            </div>

            <p class="meaning"><strong>中文释义：</strong>{{ word.chineseMeaning || '暂无' }}</p>
            <p class="meaning"><strong>日文释义：</strong>{{ word.japaneseMeaning || '暂无' }}</p>
            <p v-if="word.example" class="example"><strong>例句：</strong>{{ word.example }}</p>
            <div v-if="word.tags && word.tags.length > 0" class="tags">
              <el-tag v-for="tag in word.tags" :key="tag" size="small">{{ tag }}</el-tag>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <div class="pagination-wrapper" v-if="total > pageSize">
        <el-pagination
          background
          layout="prev, pager, next, jumper"
          :current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { Word } from '@/types'
import { isAuthenticated, removeFromFavorites, searchFavorites } from '@/api'
import { useFavorites } from '@/composables/useLocalStorage'

const favorites = ref<Word[]>([])
const isLoading = ref(false)
const errorMessage = ref('')
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const pageSizeOptions = [10, 20, 50]
const { syncFavorites } = useFavorites()

const loadFavorites = async (resetPage: boolean = false) => {
  if (!isAuthenticated()) {
    ElMessage.warning('请先登录查看收藏')
    window.dispatchEvent(new CustomEvent('open-login-dialog'))
    favorites.value = []
    total.value = 0
    return
  }

  if (resetPage) {
    currentPage.value = 1
  }

  isLoading.value = true
  errorMessage.value = ''
  try {
    const payload = await searchFavorites(searchQuery.value, currentPage.value, pageSize.value)
    favorites.value = payload.words
    total.value = payload.total
    currentPage.value = payload.page
    await syncFavorites()
  } catch (error: any) {
    errorMessage.value = error?.message || '加载收藏失败'
    favorites.value = []
    total.value = 0
  } finally {
    isLoading.value = false
  }
}

const handleSearch = async () => {
  await loadFavorites(true)
}

const handlePageChange = async (page: number) => {
  currentPage.value = page
  await loadFavorites(false)
}

const handleLimitChange = async () => {
  currentPage.value = 1
  await loadFavorites(false)
}

const removeFavorite = async (wordId: string) => {
  try {
    await removeFromFavorites(wordId)
    if (favorites.value.length === 1 && currentPage.value > 1) {
      currentPage.value -= 1
    }
    await loadFavorites(false)
    ElMessage.success('已取消收藏')
  } catch (error: any) {
    ElMessage.error(error?.message || '取消收藏失败')
  }
}

onMounted(() => {
  void loadFavorites()
})
</script>

<style scoped>
.favorites-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.header-card h1 {
  margin: 0;
  font-size: 28px;
  color: #000000;
}

.subtitle {
  margin: 8px 0 0;
  color: #555;
}

.state-card,
.search-card,
.count-card,
.word-card {
  border-radius: 8px;
}

.favorites-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.search-btn {
  width: 100%;
}

.limit-select {
  width: 100%;
}

.word-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.word-title {
  margin: 0;
  font-size: 24px;
}

.kana {
  margin: 6px 0 0;
  color: #666;
}

.meaning {
  margin: 10px 0 0;
}

.example {
  margin: 10px 0 0;
  color: #333;
}

.tags {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}
</style>
