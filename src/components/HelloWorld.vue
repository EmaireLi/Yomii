<script setup lang="ts">
defineProps<{
  msg: string
}>()
</script>

<template>
  <el-card class="greetings-card">
    <template #header>
      <div class="card-header">
        <el-text tag="h1" class="greeting-title">{{ msg }}</el-text>
      </div>
    </template>
    
    <el-text size="large" class="greeting-subtitle">
      您已成功创建了一个项目，该项目基于
      <el-link href="https://vite.dev/" target="_blank" type="primary">Vite</el-link>
      和
      <el-link href="https://vuejs.org/" target="_blank" type="primary">Vue 3</el-link>
      技术栈构建。
    </el-text>
    
    <el-divider />
    
    <div class="tech-stack">
      <el-tag type="success" size="large" effect="light">Vue 3</el-tag>
      <el-tag type="info" size="large" effect="light">TypeScript</el-tag>
      <el-tag type="warning" size="large" effect="light">Vite</el-tag>
      <el-tag type="primary" size="large" effect="light">Element Plus</el-tag>
    </div>
  </el-card>
</template>

<style scoped>
.greetings-card {
  max-width: 600px;
  margin: 0 auto;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.greetings-card:hover {
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.2);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.greeting-title {
  font-size: 2.2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.greeting-subtitle {
  display: block;
  line-height: 1.8;
  color: var(--el-text-color-regular);
}

.tech-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
  justify-content: center;
}

@media (max-width: 768px) {
  .greeting-title {
    font-size: 1.8rem;
  }
  
  .greetings-card {
    max-width: 100%;
  }
}
</style>
