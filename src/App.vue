<template>
  <el-container class="yomii-app">
    <!-- 左侧导航栏 -->
    <el-aside width="300px" class="yomii-sidebar">
      <div class="app-header">
        <h1 class="app-title">Yomii</h1>
        <p class="app-subtitle">日语学习助手</p>
      </div>
      
      <el-menu
        :default-active="currentView"
        @select="switchView"
        class="nav-menu"
        background-color="#667eea"
        text-color="#fff"
        active-text-color="#ffd700"
      >
        <el-menu-item
          v-for="item in navItems"
          :key="item.id"
          :index="item.id"
          class="nav-menu-item"
        >
          <template #title>
            <el-icon><component :is="item.icon" /></el-icon>
            <span class="nav-label">{{ item.label }}</span>
          </template>
        </el-menu-item>
      </el-menu>
      
      <div class="sidebar-footer">
        <el-statistic :value="studyStreak" suffix="天">
          <template #title>
            <span style="color: white; font-size: 16px; font-weight: 700; letter-spacing: 1px;">学习进度</span>
          </template>
        </el-statistic>
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-main class="yomii-content">
      <!-- 首页视图 -->
      <HomeView v-if="currentView === 'home'" />
      
      <!-- 查词视图 -->
      <SearchView v-else-if="currentView === 'search'" />
      
      <!-- 背单词视图 -->
      <ReciteView v-else-if="currentView === 'recite'" />
      
      <!-- 能力测试视图 -->
      <TestView v-else-if="currentView === 'test'" @switch-view="switchView" />
      
      <!-- 作文评价视图 -->
      <EssayView v-else-if="currentView === 'essay'" />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { House, Search, DocumentCopy, Notebook, Edit } from '@element-plus/icons-vue'
import { VIEWS } from '@/utils/constants'
import { useStudyStats } from '@/composables/useLocalStorage'
import HomeView from '@/components/views/HomeView.vue'
import SearchView from '@/components/views/SearchView.vue'
import ReciteView from '@/components/views/ReciteView.vue'
import TestView from '@/components/views/TestView.vue'
import EssayView from '@/components/views/EssayView.vue'

/**
 * 导航菜单项
 */
const navItems = [
  { id: VIEWS.HOME, label: '首页', icon: House },
  { id: VIEWS.SEARCH, label: '查词', icon: Search },
  { id: VIEWS.RECITE, label: '背单词', icon: DocumentCopy },
  { id: VIEWS.TEST, label: '测试', icon: Notebook },
  { id: VIEWS.ESSAY, label: '作文评价', icon: Edit }
]

/**
 * 当前显示的视图
 */
const currentView = ref<string>(VIEWS.HOME)

/**
 * 学习统计 Hook
 */
const { stats } = useStudyStats()

/**
 * 学习连续天数
 */
const studyStreak = computed(() => stats.value?.currentStreak || 0)

/**
 * 切换视图
 */
const switchView = (viewName: string): void => {
  currentView.value = viewName
}
</script>

<style scoped>
.yomii-app {
  height: 100vh;
  width: 100%;
}

.yomii-sidebar {
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  flex-direction: column;
  padding: 30px 0 0 0;
  box-shadow: 4px 0 20px rgba(102, 126, 234, 0.25);
  overflow-y: auto;
}

.app-header {
  padding: 30px 20px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  margin-bottom: 20px;
}

.app-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 2px;
  color: white;
}

.app-subtitle {
  font-size: 13px;
  opacity: 0.85;
  margin: 8px 0 0 0;
}

.nav-menu {
  flex: 1;
  border: none;
  background-color: transparent;
}

.nav-menu-item {
  margin: 8px 12px !important;
  border-radius: 6px !important;
  background: rgba(255, 255, 255, 0.08) !important;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
}

.nav-menu-item:hover {
  background: rgba(255, 255, 255, 0.18) !important;
  transform: translateX(8px);
}

.nav-icon {
  font-size: 20px;
  min-width: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}

.sidebar-footer {
  padding: 30px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  background: linear-gradient(180deg, transparent, rgba(0, 0, 0, 0.15));
  text-align: center;
  color: white;
}

.sidebar-footer :where(.el-statistic) {
  --el-text-color-primary: white;
}

.streak-statistic :where(.el-statistic__item-title) {
  color: white !important;
  font-size: 16px !important;
  font-weight: 700 !important;
}

.yomii-content {
  padding: 40px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e9ecf1 50%, #f0f4f8 100%);
  overflow-y: auto;
}

/* 滚动条美化 */
.content::-webkit-scrollbar {
  width: 8px;
}

.content::-webkit-scrollbar-track {
  background: transparent;
}

.content::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 4px;
}

.content::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

.sidebar::-webkit-scrollbar {
  width: 4px;
}

.sidebar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
}

.sidebar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
}

.sidebar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

/* 进入动画 */
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes expand {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 1000px;
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.9;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.05);
  }
}

@keyframes glow {
  0% {
    box-shadow: 0 0 5px rgba(102, 126, 234, 0.3);
  }
  50% {
    box-shadow: 0 0 20px rgba(102, 126, 234, 0.6);
  }
  100% {
    box-shadow: 0 0 5px rgba(102, 126, 234, 0.3);
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-5px);
  }
}

@media (max-height: 800px) {
  .yomii-sidebar {
    padding: 35px 0;
    width: 360px;
  }

  .app-header {
    margin-bottom: 40px;
  }

  .app-title {
    font-size: 38px;
  }

  .yomii-content {
    padding: 40px 60px;
  }
}
</style>
<!-- 在文件最后面，加上这段代码 -->
<style>
/* 学习进度容器 */
.streak-statistic {
  text-align: center;
}

/* 标题：学习进度 (调大) */
.streak-statistic .el-statistic__title {
  color: white !important;
  font-size: 22px !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  margin-bottom: 8px !important;
}

/* 数字部分 (调小) */
.streak-statistic .el-statistic__content {
  color: #ffd700 !important;
  font-size: 26px !important;
  font-weight: bold !important;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

/* 单位：天 */
.streak-statistic .el-statistic__suffix {
  color: #ffd700 !important;
  font-size: 18px !important;
  margin-left: 4px !important;
}
</style>