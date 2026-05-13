<template>
  <section class="home-view">
    <el-card class="header-card"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <h1>欢迎使用 Yomii 辞书</h1>
      <p class="desc">{{ appDescription }}</p>
    </el-card>

    <!-- 快速统计 -->
    <el-row :gutter="20" class="stats-section"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <el-col :xs="12" :sm="12" :md="6" :lg="6" class="stat-col">
        <el-card class="stat-card">
          <el-statistic title="总背词数" :value="STATS.totalWordsRecited" />
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6" :lg="6" class="stat-col">
        <el-card class="stat-card">
          <el-statistic title="今日背词" :value="STATS.todayRecited" />
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6" :lg="6" class="stat-col">
        <el-card class="stat-card">
          <el-statistic title="连续天数" :value="STATS.currentStreak" suffix="天" />
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6" :lg="6" class="stat-col">
        <el-card class="stat-card">
          <el-statistic title="最长连续" :value="STATS.longestStreak" suffix="天" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 团队信息 -->
    <el-card class="team-card"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <template #header>
        <div class="card-header">
          <div class="title-text">
            <el-icon :size="20"
              style="vertical-align: middle; margin-right: 0.8rem;">
              <UserFilled/>
            </el-icon> 
            <span>{{ teamInfo.name }}</span>
          </div>
        </div>
      </template>
      
      <el-row :gutter="20">
        <el-col v-for="member in teamInfo.members" :key="member.id" :xs="24" :sm="12" :md="8" :lg="6">
          <el-card class="member-card" shadow="hover">
            <div class="member-content">
              <div class="member-name">{{ member.name }}</div>
              <el-tag class="member-role">{{ member.role }}</el-tag>
              <div class="member-id">{{ member.id }}</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 功能导航 -->
    <el-card class="features-card"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <template #header>
        <div class="card-header">
          <div class="title-text">
            <el-icon :size="20"
              style="vertical-align: middle; margin-right: 0.8rem;">
              <Operation/>
            </el-icon> 
            <span>核心功能</span>
          </div>
        </div>
      </template>
      
      <el-row :gutter="20">
        <el-col
          v-for="(feature, idx) in featureList"
          :key="idx"
          :xs="24"
          :sm="12"
          :md="12"
          :lg="6"
          class="feature-col"
        >
          <div class="feature-item">
            <div class="feature-icon">
              <el-icon><component :is="feature.icon" /></el-icon>
            </div>
            <div class="feature-info">
              <h4>{{ feature.title }}</h4>
              <p>{{ feature.description }}</p>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Search, DocumentCopy, Notebook, StarFilled, UserFilled, Operation } from '@element-plus/icons-vue'
import { TEAM_INFO, APP_DESCRIPTION } from '@/utils/constants'
import { useStudyStats } from '@/composables/useLocalStorage'

const appDescription = APP_DESCRIPTION
const teamInfo = TEAM_INFO

const { stats } = useStudyStats()
const STATS = computed(() => stats.value)

const featureList = [
  {
    icon: Search,
    title: '查词',
    description: '快速查询日语词汇，了解含义和用法'
  },
  {
    icon: DocumentCopy,
    title: '背单词',
    description: '闪卡式学习，高效掌握日语词汇'
  },
  {
    icon: Notebook,
    title: '能力测试',
    description: '评估学习成果，智能题库随机出题'
  },
  {
    icon: StarFilled,
    title: '收藏管理',
    description: '保存喜欢的词汇，建立个人学习库'
  }
]
</script>

<style scoped>
.home-view {
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

.header-card {
  border-radius: 0.8rem;
  box-shadow: 0 0.2rem 1.2rem rgba(0, 0, 0, 0.08);
  border: none;
}

.header-card h1 {
  margin: 0 0 1.5rem 0;
  color: #000000;
  font-size: 2.8rem;
  font-weight: 700;
}

.desc {
  margin: 0;
  color: #333333;
  font-size: 1.6rem;
  line-height: 1.8;
}

.stats-section {
  margin: 0;
}

.stat-col {
  width: 100%;
}

.stat-card {
  border-radius: 0.8rem;
  box-shadow: 0 0.2rem 1.2rem rgba(0, 0, 0, 0.08);
  border: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  margin: 1rem 0;
}

.stat-card :deep(.el-card__body) {
  padding: 2rem;
}

.stat-card :deep(.el-statistic__head) {
  color: rgba(255, 255, 255, 0.8);
  font-size: 2rem;
  margin-bottom: 0.8rem;
  font-weight: 700;
}

.stat-card :deep(.el-statistic__content) {
  color: white;
  font-size: 3.6rem;
  font-weight: bold;
  letter-spacing: 0.1rem;
}

.team-card, .features-card {
  border-radius: 0.8rem;
  box-shadow: 0 0.2rem 1.2rem rgba(0, 0, 0, 0.08);
  border: none;
}

.card-header {
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title-text {
  font-size: 1.8rem;
  font-weight: 600;
  color: #000000;
}

.member-card {
  margin: 0.4rem 0;
  border-radius: 0.6rem;
  border: 0.1rem solid #ebeef5;
  transition: all 0.3s;
}

.member-card:hover {
  border-color: #409eff;
  transform: translateY(-0.2rem);
}

.member-content {
  text-align: center;
  padding: 0;
}

.member-name {
  font-weight: 600;
  color: #000000;
  margin-bottom: 0.8rem;
  font-size: 1.6rem;
}

.member-role {
  margin: 0.8rem 0;
}

.member-id {
  font-size: 1.4rem;
  color: #333333;
  font-family: monospace;
  margin-top: 0.8rem;
}

.feature-item {
  display: flex;
  gap: 1.2rem;
  width: 100%;
  height: 13.2rem;
  box-sizing: border-box;
  align-items: center;
  padding: 1.8rem;
  background: linear-gradient(135deg, #f5f7fa 0%, #eef2f8 100%);
  border-radius: 0.6rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-left: 0.4rem solid #667eea;
}

.feature-col {
  display: flex;
  margin-bottom: 1.6rem;
}

.feature-item:hover {
  background: linear-gradient(135deg, #ecf5ff 0%, #e0eeff 100%);
  border-left-color: #764ba2;
  transform: translateX(0.6rem);
  box-shadow: 0 0.2rem 0.8rem rgba(102, 126, 234, 0.15);
}

.feature-icon {
  min-width: 5.2rem;
  width: 5.2rem;
  height: 5.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.8rem;
  color: #667eea;
  background: rgba(102, 126, 234, 0.08);
  border-radius: 1rem;
}

.feature-info {
  flex: 1;
}

.feature-info h4 {
  margin: 0 0 0.4rem 0;
  color: #000000;
  font-size: 1.4rem;
  font-weight: 600;
}

.feature-info p {
  margin: 0;
  color: #333333;
  font-size: 1.3rem;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
