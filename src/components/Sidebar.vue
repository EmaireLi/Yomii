<template>
  <aside class="sidebar">
    <div class="logo">
      <h2>Yomii辞书</h2>
      <p class="version">v1.0.0</p>
    </div>

    <nav class="nav-menu">
      <button
        v-for="item in menuItems"
        :key="item.id"
        @click="emit('select', item.id)"
        :class="['nav-button', { active: currentView === item.id }]"
        :title="item.description"
      >
        <el-icon class="nav-icon">
          <component :is="item.icon" />
        </el-icon>
        <span class="nav-label">{{ item.label }}</span>
      </button>
    </nav>

    <!-- 学习进度显示 -->
    <div class="progress-section">
      <h3>今日目标</h3>
      <div class="daily-goal">
        <div class="goal-bar">
          <div class="goal-progress" :style="{ width: dailyProgress + '%' }"></div>
        </div>
        <p class="goal-text">{{ dailyRecited }} / {{ dailyGoal }}</p>
      </div>
    </div>

    <!-- 快捷链接 -->
    <div class="shortcuts-section">
      <h3>快捷操作</h3>
      <button @click="clearHistory" class="shortcut-btn" title="清空搜索历史">
        <el-icon><DeleteIcon /></el-icon>
        <span>清空历史</span>
      </button>
      <button @click="exportData" class="shortcut-btn" title="导出学习数据">
        <el-icon><DownloadIcon /></el-icon>
        <span>导出数据</span>
      </button>
    </div>

    <!-- 侧边栏底部 -->
    <div class="sidebar-footer">
      <p class="footer-text">学习是一种生活方式</p>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { House, Search, DocumentCopy, Notebook, Delete, Download, Star } from '@element-plus/icons-vue'
import { VIEWS } from '@/utils/constants'
import { useSearchHistory, useStudyStats } from '@/composables/useLocalStorage'

// 使图标在模板中可用
const DeleteIcon = Delete
const DownloadIcon = Download

const props = defineProps<{
  currentView: string
}>()

const emit = defineEmits<{
  select: [view: string]
}>()

const menuItems = [
  { id: VIEWS.HOME, label: '首页', icon: House, description: '查看学习概览和统计' },
  { id: VIEWS.SEARCH, label: '查词', icon: Search, description: '快速查询日语词汇' },
  { id: VIEWS.RECITE, label: '背单词', icon: DocumentCopy, description: '闪卡式单词学习' },
  { id: VIEWS.FAVORITES, label: '我的收藏', icon: Star, description: '查看收藏的词汇' },
  { id: VIEWS.TEST, label: '能力测试', icon: Notebook, description: '检测学习成果' }
]

const { clearHistory } = useSearchHistory()
const { stats } = useStudyStats()

const dailyGoal = 30
const dailyRecited = computed(() => stats.value.todayRecited)
const dailyProgress = computed(() => {
  return Math.min((dailyRecited.value / dailyGoal) * 100, 100)
})

const exportData = () => {
  const data = {
    stats: stats.value,
    exportTime: new Date().toISOString()
  }
  const dataStr = JSON.stringify(data, null, 2)
  const element = document.createElement('a')
  element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(dataStr))
  element.setAttribute('download', `yomii-data-${Date.now()}.json`)
  element.style.display = 'none'
  document.body.appendChild(element)
  element.click()
  document.body.removeChild(element)
}
</script>

<style scoped>
.sidebar {
  width: 240px;
  background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 4px rgba(0, 0, 0, 0.05);
  overflow-y: auto;
}

.logo {
  padding: 20px 15px;
  text-align: center;
  border-bottom: 2px solid #e4e7ed;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  margin: 0;
}

.logo h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 1px;
}

.version {
  margin: 5px 0 0;
  font-size: 12px;
  opacity: 0.8;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  padding: 15px 0;
  flex: 1;
}

.nav-button {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px 20px;
  border: none;
  background: none;
  text-align: left;
  font-size: 15px;
  cursor: pointer;
  color: #333333;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  font-weight: 500;
}

.nav-button:hover {
  background-color: #e8f4f8;
  color: #409eff;
  padding-left: 25px;
}

.nav-button.active {
  background: linear-gradient(90deg, #ecf5ff 0%, rgba(236, 245, 255, 0) 100%);
  color: #409eff;
  border-right: 4px solid #409eff;
  padding-right: 16px;
}

.nav-button.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: #409eff;
}

.nav-icon {
  flex-shrink: 0;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: inherit;
}

.nav-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.progress-section {
  padding: 15px;
  margin: 0 10px;
  background: #f5f7fa;
  border-radius: 8px;
  border-left: 3px solid #409eff;
}

.progress-section h3 {
  margin: 0 0 12px;
  font-size: 13px;
  color: #333333;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.daily-goal {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.goal-bar {
  height: 8px;
  background: #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
}

.goal-progress {
  height: 100%;
  background: linear-gradient(90deg, #67c23a, #85ce61);
  transition: width 0.3s ease;
}

.goal-text {
  margin: 0;
  font-size: 14px;
  color: #000000;
  font-weight: 600;
}

.shortcuts-section {
  padding: 15px;
  margin: 0 10px 15px;
  border-top: 1px solid #e4e7ed;
}

.shortcuts-section h3 {
  margin: 0 0 10px;
  font-size: 13px;
  color: #333333;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.shortcut-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 13px;
  color: #333333;
  cursor: pointer;
  margin-bottom: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: left;
  font-weight: 500;
}

.shortcut-btn:hover {
  background: #ecf5ff;
  border-color: #409eff;
  color: #409eff;
}

.shortcut-btn :deep(.el-icon) {
  flex-shrink: 0;
  font-size: 16px;
}

.shortcut-btn:last-child {
  margin-bottom: 0;
}

.sidebar-footer {
  padding: 15px;
  text-align: center;
  border-top: 1px solid #e4e7ed;
  background: #f8f9fa;
}

.footer-text {
  margin: 0;
  font-size: 12px;
  color: #222222;
  font-style: italic;
}

/* 滚动条美化 */
.sidebar::-webkit-scrollbar {
  width: 6px;
}

.sidebar::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.sidebar::-webkit-scrollbar-thumb:hover {
  background: #909399;
}
</style>
