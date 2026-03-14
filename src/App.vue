<template>
  <div class="yomii-app">
    <!-- 左侧导航栏 -->
    <aside class="sidebar">
      <div class="app-header">
        <h1 class="app-title">Yomii</h1>
        <p class="app-subtitle">日语学习助手</p>
      </div>
      
      <nav class="nav-menu">
        <button
          v-for="item in navItems"
          :key="item.id"
          @click="switchView(item.id)"
          :class="['nav-item', { active: currentView === item.id }]"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </button>
      </nav>
      
      <div class="sidebar-footer">
        <p class="footer-text">学习进度: {{ studyStreak }} 天</p>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="content">
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
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
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
  { id: VIEWS.HOME, label: '首页', icon: '🏠' },
  { id: VIEWS.SEARCH, label: '查词', icon: '🔍' },
  { id: VIEWS.RECITE, label: '背单词', icon: '📚' },
  { id: VIEWS.TEST, label: '测试', icon: '📝' },
  { id: VIEWS.ESSAY, label: '作文评价', icon: '✍️' }
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
}</script>

<style scoped>
/* 全局基础样式 */
* {
  box-sizing: border-box;
}

/* 应用根样式 - 桌面应用风格 */
.yomii-app {
  display: flex;
  flex-direction: row;
  height: 100vh;
  width: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #333;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 50%, #f0f3f8 100%);
  overflow: hidden;
}

/* 左侧导航栏 - 桌面应用宽屏优化 */
.sidebar {
  width: 400px;
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  flex-direction: column;
  padding: 45px 0;
  box-shadow: 4px 0 20px rgba(102, 126, 234, 0.25);
  overflow-y: auto;
  position: relative;
}

/* 侧边栏背景动画 */
.sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 30%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(255, 255, 255, 0.05) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

.sidebar > * {
  position: relative;
  z-index: 1;
}

.app-header {
  padding: 0 35px;
  margin-bottom: 50px;
  text-align: center;
}

.app-title {
  font-size: 42px;
  font-weight: 700;
  margin: 0 0 12px;
  letter-spacing: 2px;
}

.app-subtitle {
  font-size: 15px;
  opacity: 0.85;
  margin: 0;
  letter-spacing: 0.5px;
}

.nav-menu {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0 20px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 20px 28px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: white;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  border-left: 4px solid transparent;
  margin: 0 0px;
  backdrop-filter: blur(10px);
  position: relative;
  overflow: hidden;
}

.nav-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateX(8px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.nav-item:hover::before {
  left: 100%;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.25);
  border-left-color: #ffd700;
  border-color: rgba(255, 255, 255, 0.4);
  font-weight: 600;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25), inset 0 0 10px rgba(255, 255, 255, 0.1);
  transform: translateX(8px) scale(1.02);
}

.nav-icon {
  font-size: 26px;
  min-width: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.nav-item:hover .nav-icon {
  transform: scale(1.2) rotate(5deg);
  filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.4));
}

.nav-item.active .nav-icon {
  transform: scale(1.25) rotate(-5deg);
  filter: drop-shadow(0 0 12px rgba(255, 215, 0, 0.6));
}

.nav-label {
  white-space: nowrap;
}

.sidebar-footer {
  padding: 30px 35px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  text-align: center;
  background: linear-gradient(180deg, transparent, rgba(0, 0, 0, 0.15));
  margin-top: auto;
}

.footer-text {
  margin: 0;
  font-size: 15px;
  opacity: 0.9;
  font-weight: 500;
  animation: pulse 2s ease-in-out infinite;
}

/* 主内容区 */
.content {
  flex: 1;
  overflow-y: auto;
  padding: 45px 70px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e9ecf1 50%, #f0f4f8 100%);
  scroll-behavior: smooth;
  position: relative;
}

/* 内容区背景装饰 */
.content::before {
  content: '';
  position: fixed;
  top: 0;
  right: 0;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.08) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}

.content > * {
  position: relative;
  z-index: 1;
}

.view-section {
  background: #fff;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  animation: slideUp 0.3s ease;
}

h1 {
  margin-top: 0;
  color: #303133;
  margin-bottom: 35px;
  font-size: 32px;
  font-weight: 700;
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  .sidebar {
    padding: 35px 0;
    width: 360px;
  }

  .app-header {
    margin-bottom: 40px;
  }

  .app-title {
    font-size: 38px;
  }

  .content {
    padding: 40px 60px;
  }
}
</style>