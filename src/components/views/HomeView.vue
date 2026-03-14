<template>
  <section class="view-section home-view">
    <h1>欢迎使用 Yomii 辞书</h1>
    <p class="desc">{{ appDescription }}</p>

    <!-- 快速统计 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-number">{{ STATS.totalWordsRecited }}</div>
        <div class="stat-label">总背词数</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ STATS.todayRecited }}</div>
        <div class="stat-label">今日背词</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ STATS.currentStreak }}</div>
        <div class="stat-label">连续天数</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ STATS.longestStreak }}</div>
        <div class="stat-label">最长连续</div>
      </div>
    </div>

    <!-- 团队信息 -->
    <div class="team-info">
      <h3>{{ teamInfo.name }}</h3>
      <div class="team-members">
        <div v-for="member in teamInfo.members" :key="member.id" class="member-card">
          <span class="member-name">{{ member.name }}</span>
          <span class="member-role">{{ member.role }}</span>
          <span class="member-id">{{ member.id }}</span>
        </div>
      </div>
    </div>

    <!-- 功能导航 -->
    <div class="features">
      <h3>主要功能</h3>
      <div class="feature-list">
        <div class="feature-item">
          <span class="feature-icon">🔍</span>
          <div>
            <h4>查词</h4>
            <p>快速查询日语词汇，了解含义和用法</p>
          </div>
        </div>
        <div class="feature-item">
          <span class="feature-icon">📚</span>
          <div>
            <h4>背单词</h4>
            <p>闪卡式学习，高效掌握日语词汇</p>
          </div>
        </div>
        <div class="feature-item">
          <span class="feature-icon">📝</span>
          <div>
            <h4>能力测试</h4>
            <p>评估学习成果，智能题库随机出题</p>
          </div>
        </div>
        <div class="feature-item">
          <span class="feature-icon">❤️</span>
          <div>
            <h4>收藏管理</h4>
            <p>保存喜欢的词汇，建立个人学习库</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { TEAM_INFO, APP_DESCRIPTION } from '@/utils/constants'
import { useStudyStats } from '@/composables/useLocalStorage'

const appDescription = APP_DESCRIPTION
const teamInfo = TEAM_INFO

const { stats } = useStudyStats()
const STATS = computed(() => stats.value)
</script>

<style scoped>
.home-view .desc {
  font-size: 16px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 40px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 25px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-number {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 10px;
}

.stat-label {
  font-size: 11px;
  opacity: 0.9;
}

.team-info {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 25px;
  border-left: 4px solid #409eff;
}

.team-info h3 {
  margin-top: 0;
  color: #303133;
  margin-bottom: 12px;
  font-size: 16px;
}

.team-members {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.member-card {
  background: white;
  padding: 10px;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.member-name {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.member-role {
  font-size: 12px;
  color: #409eff;
}

.member-id {
  font-size: 11px;
  color: #909399;
  font-family: monospace;
}

.features h3 {
  margin-top: 25px;
  margin-bottom: 15px;
  color: #303133;
  font-size: 16px;
}

.feature-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.feature-item {
  display: flex;
  gap: 10px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: all 0.3s;
  border-left: 4px solid transparent;
}

.feature-item:hover {
  background: #ecf5ff;
  border-left-color: #409eff;
  transform: translateX(5px);
}

.feature-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.feature-item h4 {
  margin: 0 0 4px;
  color: #303133;
  font-size: 14px;
}

.feature-item p {
  margin: 0;
  font-size: 12px;
  color: #666;
}
</style>
