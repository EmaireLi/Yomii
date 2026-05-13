<template>
  <el-container class="yomii-app">
    <!-- 左侧导航栏 -->
    <el-aside class="yomii-sidebar"
      :style="{ width: sidebarWidth }"
      @mousemove.stop
      @pointermove.stop
      @touchmove.stop>
      <div class="app-header">
        <h1 class="app-title">Yomii</h1>
        <p class="app-subtitle">日语学习助手</p>
      </div>
      
      <!-- 用户信息/登录区 -->
      <div class="user-section">
        <template v-if="isLoggedIn">
          <div class="user-info">
            <el-avatar size="large" :src="`https://api.dicebear.com/7.x/avataaars/svg?seed=${currentUser?.username}`" />
            <div class="user-details">
              <p class="username">{{ currentUser?.username }}</p>
              <p class="email">{{ currentUser?.phone }}</p>
            </div>
          </div>
          <el-button type="danger" size="small" @click="handleLogout" class="logout-btn">登出</el-button>
        </template>
        <template v-else>
          <div class="login-buttons">
            <el-button type="primary" @click="openLoginDialog" class="auth-btn">登录</el-button>
            <el-button @click="openRegisterDialog" class="auth-btn">注册</el-button>
          </div>
        </template>
      </div>
      
      <el-menu
        :default-active="route.name as string"
        @select="navigateTo"
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
            <span style="color: white; font-size: 1.6rem; font-weight: 700; letter-spacing: 0.1rem;">学习进度</span>
          </template>
        </el-statistic>
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-main class="yomii-content">
      <!-- RouterView 显示页面内容 -->
      <router-view />
    </el-main>

    <!-- 登录对话框 -->
    <el-dialog v-model="loginDialogVisible" title="登录账户" width="50rem" @closed="resetLoginDialogState">
      <el-form :model="loginForm" ref="loginFormRef" @submit.prevent="handleLogin">
        <el-form-item label="电话" :rules="[{ required: true, message: '电话不能为空' }]" prop="phone">
          <el-input v-model="loginForm.phone" placeholder="请输入电话号码" />
        </el-form-item>
        <el-form-item label="密码" :rules="[{ required: true, message: '密码不能为空' }]" prop="password">
          <el-input v-model="loginForm.password" placeholder="请输入密码" type="password" show-password />
        </el-form-item>
        <div class="form-actions">
          <el-button @click="openResetDialog" link>忘记密码？</el-button>
        </div>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="loginDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleLogin" :loading="loginLoading">登录</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 注册对话框 -->
    <el-dialog v-model="registerDialogVisible" title="创建新账户" width="50rem" @closed="resetRegisterDialogState">
      <el-form :model="registerForm" ref="registerFormRef">
        <el-form-item label="用户名" :rules="[{ required: true, message: '用户名不能为空' }]" prop="username">
          <el-input v-model="registerForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="电话" :rules="[{ required: true, message: '电话不能为空' }]" prop="phone">
          <el-input v-model="registerForm.phone" placeholder="请输入电话号码" />
        </el-form-item>
        <el-form-item label="密码" :rules="[{ required: true, message: '密码不能为空' }, { min: 8, message: '密码至少8位' }]" prop="password">
          <el-input v-model="registerForm.password" placeholder="请输入密码（至少8位）" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" :rules="[{ required: true, message: '请确认密码' }]" prop="confirmPassword">
          <el-input v-model="registerForm.confirmPassword" placeholder="请再次输入密码" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="registerDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleRegister" :loading="registerLoading">注册账户</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 找回密码对话框 -->
    <el-dialog v-model="resetDialogVisible" title="重置密码" width="50rem" @closed="resetResetDialogState">
      <el-steps :active="resetStep" align-center>
        <el-step title="验证电话" />
        <el-step title="设置新密码" />
        <el-step title="完成" />
      </el-steps>

      <div class="reset-content">
        <!-- 步骤1：输入电话 -->
        <template v-if="resetStep === 0">
          <el-form-item label="电话" style="margin-top: 2rem">
            <el-input v-model="resetForm.phone" placeholder="请输入注册电话号码" />
          </el-form-item>
        </template>

        <!-- 步骤2：设置新密码 -->
        <template v-if="resetStep === 1">
          <el-form-item label="重置码" style="margin-top: 2rem">
            <el-input v-model="resetForm.code" placeholder="请输入邮箱中收到的重置码" />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="resetForm.newPassword" placeholder="请输入新密码（至少8位）" type="password" show-password />
          </el-form-item>
          <el-form-item label="确认新密码">
            <el-input v-model="resetForm.confirmPassword" placeholder="请再次输入新密码" type="password" show-password />
          </el-form-item>
        </template>

        <!-- 步骤3：完成 -->
        <template v-if="resetStep === 2">
          <div class="reset-success">
            <el-icon class="success-icon"><CircleCheckFilled /></el-icon>
            <p>密码重置成功！</p>
            <p style="color: #606266; font-size: 1.4rem;">请使用新密码重新登录</p>
          </div>
        </template>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="resetDialogVisible = false">关闭</el-button>
          <template v-if="resetStep === 0">
            <el-button type="primary" @click="handleRequestReset" :loading="resetLoading">获取重置码</el-button>
          </template>
          <template v-if="resetStep === 1">
            <el-button @click="resetStep = 0">上一步</el-button>
            <el-button type="primary" @click="handleConfirmReset" :loading="resetLoading">确认重置</el-button>
          </template>
          <template v-if="resetStep === 2">
            <el-button type="primary" @click="completeReset">登录</el-button>
          </template>
        </div>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { House, Search, DocumentCopy, Notebook, Edit, Star, CircleCheckFilled } from '@element-plus/icons-vue'
import { VIEWS } from '@/utils/constants'
import { useStudyStats } from '@/composables/useLocalStorage'
import { login, register, logout, getCurrentUser, isAuthenticated, requestPasswordReset, resetPassword } from '@/api'
import type { User, LoginRequest, RegisterRequest, ResetPasswordRequest, SetNewPasswordRequest } from '@/types'

/**
 * 导航菜单项
 */
const navItems = [
  { id: VIEWS.HOME, label: '首页', icon: House },
  { id: VIEWS.SEARCH, label: '查词', icon: Search },
  { id: VIEWS.RECITE, label: '背单词', icon: DocumentCopy },
  { id: VIEWS.FAVORITES, label: '我的收藏', icon: Star },
  { id: VIEWS.TEST, label: '测试', icon: Notebook },
  { id: VIEWS.ESSAY, label: '作文评价', icon: Edit }
]

/**
 * 路由实例
 */
const router = useRouter()
const route = useRoute()

/**
 * Sidebar 宽度 - 动态计算以适应 Electron 和浏览器
 */
const sidebarWidth = ref<string>('20vw')

/**
 * 学习统计 Hook
 */
const { stats, syncStudyStats } = useStudyStats()

/**
 * 学习连续天数
 */
const studyStreak = computed(() => stats.value?.currentStreak || 0)

/**
 * 用户认证状态
 */
const isLoggedIn = ref(false)
const currentUser = ref<User | null>(null)

/**
 * 登录对话框
 */
const loginDialogVisible = ref(false)
const loginLoading = ref(false)
const loginFormRef = ref<FormInstance>()
const loginForm = ref<LoginRequest>({
  phone: '',
  password: ''
})

/**
 * 注册对话框
 */
const registerDialogVisible = ref(false)
const registerLoading = ref(false)
const registerFormRef = ref<FormInstance>()
const registerForm = ref<RegisterRequest>({
  username: '',
  phone: '',
  password: '',
  confirmPassword: ''
})

/**
 * 密码重置对话框
 */
const resetDialogVisible = ref(false)
const resetLoading = ref(false)
const resetStep = ref(0)
const resetForm = ref<SetNewPasswordRequest & { phone: string }>({
  phone: '',
  code: '',
  newPassword: '',
  confirmPassword: ''
})

/**
 * 初始化：检查是否已登录
 */
onMounted(() => {
  checkAuthentication()
  calculateSidebarWidth()
  // 监听窗口大小变化，动态调整 sidebar 宽度
  window.addEventListener('resize', calculateSidebarWidth)
  // 监听路由守卫的登录事件
  window.addEventListener('open-login-dialog', () => {
    openLoginDialog()
  })
})

/**
 * 清理事件监听器
 */
onUnmounted(() => {
  window.removeEventListener('resize', calculateSidebarWidth)
})

/**
 * 检查认证状态
 */
function checkAuthentication() {
  if (isAuthenticated()) {
    const user = getCurrentUser()
    if (user) {
      currentUser.value = user
      isLoggedIn.value = true
      void syncStudyStats()
    }
  } else {
    isLoggedIn.value = false
    currentUser.value = null
  }
}

/**
 * 计算 Sidebar 宽度 - 适应 Electron 和浏览器窗口大小变化
 * 在 Electron 中，viewport 计算与浏览器不同，需要动态调整
 */
function calculateSidebarWidth() {
  const windowWidth = window.innerWidth
  // Sidebar 目标宽度：窗口的 20%，但最小值 250px，最大值 400px
  const targetWidth = Math.max(250, Math.min(400, windowWidth * 0.2))
  sidebarWidth.value = `${targetWidth}px`
}

/**
 * 打开登录对话框
 */
function openLoginDialog() {
  resetLoginDialogState()
  loginDialogVisible.value = true
}

/**
 * 打开注册对话框
 */
function openRegisterDialog() {
  resetRegisterDialogState()
  registerDialogVisible.value = true
}

/**
 * 打开重置密码对话框
 */
function openResetDialog() {
  resetResetDialogState()
  resetDialogVisible.value = true
  loginDialogVisible.value = false
}

/**
 * 重置登录对话框状态
 */
function resetLoginDialogState() {
  ElMessage.closeAll()
  loginLoading.value = false
  loginForm.value = { phone: '', password: '' }
  loginFormRef.value?.clearValidate()
}

/**
 * 重置注册对话框状态
 */
function resetRegisterDialogState() {
  ElMessage.closeAll()
  registerLoading.value = false
  registerForm.value = { username: '', phone: '', password: '', confirmPassword: '' }
  registerFormRef.value?.clearValidate()
}

/**
 * 重置找回密码对话框状态
 */
function resetResetDialogState() {
  ElMessage.closeAll()
  resetLoading.value = false
  resetStep.value = 0
  resetForm.value = { phone: '', code: '', newPassword: '', confirmPassword: '' }
}

/**
 * 处理登录
 */
async function handleLogin() {
  if (!loginForm.value.phone || !loginForm.value.password) {
    ElMessage.warning('电话和密码不能为空')
    return
  }

  loginLoading.value = true
  try {
    const res = await login(loginForm.value)
    if (res.success) {
      ElMessage.success(res.message || '登录成功')
      checkAuthentication()
      loginDialogVisible.value = false
      // 导航到首页
      router.push({ name: VIEWS.HOME })
    } else {
      ElMessage.error(res.error || res.message || '登录失败')
    }
  } catch (error) {
    ElMessage.error('登录出错，请稍后重试')
    console.error('登录错误:', error)
  } finally {
    loginLoading.value = false
  }
}

/**
 * 处理注册
 */
async function handleRegister() {
  if (!registerForm.value.username || !registerForm.value.phone || !registerForm.value.password) {
    ElMessage.warning('请填写所有必填项')
    return
  }

  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    ElMessage.warning('两次密码不一致')
    return
  }

  if (registerForm.value.password.length < 8) {
    ElMessage.warning('密码至少8位')
    return
  }

  registerLoading.value = true
  try {
    const res = await register(registerForm.value)
    if (res.success) {
      ElMessage.success(res.message || '注册成功')
      checkAuthentication()
      registerDialogVisible.value = false
      // 导航到首页
      router.push({ name: VIEWS.HOME })
    } else {
      ElMessage.error(res.error || res.message || '注册失败')
    }
  } catch (error) {
    ElMessage.error('注册出错，请稍后重试')
    console.error('注册错误:', error)
  } finally {
    registerLoading.value = false
  }
}

/**
 * 处理请求重置密码
 */
async function handleRequestReset() {
  if (!resetForm.value.phone) {
    ElMessage.warning('电话不能为空')
    return
  }

  resetLoading.value = true
  try {
    const data: ResetPasswordRequest = { phone: resetForm.value.phone }
    const res = await requestPasswordReset(data)
    if (res.success) {
      ElMessage.success(res.message || '重置码已发送到邮箱')
      resetStep.value = 1
    } else {
      ElMessage.error(res.error || res.message || '请求失败')
    }
  } catch (error) {
    ElMessage.error('请求出错，请稍后重试')
    console.error('重置密码请求错误:', error)
  } finally {
    resetLoading.value = false
  }
}

/**
 * 处理确认重置密码
 */
async function handleConfirmReset() {
  if (!resetForm.value.code || !resetForm.value.newPassword) {
    ElMessage.warning('请填写所有字段')
    return
  }

  if (resetForm.value.newPassword !== resetForm.value.confirmPassword) {
    ElMessage.warning('两次密码不一致')
    return
  }

  if (resetForm.value.newPassword.length < 8) {
    ElMessage.warning('密码至少8位')
    return
  }

  resetLoading.value = true
  try {
    const data: SetNewPasswordRequest = {
      code: resetForm.value.code,
      newPassword: resetForm.value.newPassword,
      confirmPassword: resetForm.value.confirmPassword
    }
    const res = await resetPassword(data)
    if (res.success) {
      ElMessage.success(res.message || '密码重置成功')
      resetStep.value = 2
    } else {
      ElMessage.error(res.error || res.message || '重置失败')
    }
  } catch (error) {
    ElMessage.error('重置出错，请稍后重试')
    console.error('重置密码错误:', error)
  } finally {
    resetLoading.value = false
  }
}

/**
 * 完成重置，返回登录
 */
function completeReset() {
  resetDialogVisible.value = false
  resetStep.value = 0
  openLoginDialog()
}

/**
 * 处理登出
 */
function handleLogout() {
  logout()
  isLoggedIn.value = false
  currentUser.value = null
  ElMessage.success('已登出')
  // 导航到首页
  router.push({ name: VIEWS.HOME })
}

/**
 * 处理菜单选择（导航到路由）
 */
function navigateTo(viewName: string) {
  router.push({ name: viewName })
}
</script>

<style scoped>
.yomii-app {
  height: 100vh;
  width: 100%;
  z-index: 1;
  display: flex;
}

.yomii-sidebar {
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  flex-direction: column;
  padding: 0;
  margin: 0;
  box-shadow: 0.4rem 0 2rem rgba(102, 126, 234, 0.25);
  overflow-y: auto;
  /* width 动态设置通过 :style 绑定 */
  width: auto;
  height: 100vh;
  flex-shrink: 0;
  min-width: 250px;
  max-width: 400px;
}

.app-header {
  padding: 1rem 2rem 2rem 2rem;
  margin-top: 2rem;
  text-align: center;
  border-bottom: 0.1rem solid rgba(255, 255, 255, 0.2);
}

.app-title {
  font-size: 3.2rem;
  font-weight: 700;
  margin: 0;
  letter-spacing: 0.2rem;
  color: white;
}

.app-subtitle {
  font-size: 1.3rem;
  opacity: 0.85;
  margin: 0.8rem 0 0 0;
}

.user-section {
  padding: 3rem 2.5rem;
  border-bottom: 0.1rem solid rgba(255, 255, 255, 0.2);
  pointer-events: auto;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  margin-bottom: 1.2rem;
}

.user-details {
  flex: 1;
}

.username {
  margin: 0;
  color: white;
  font-weight: 600;
  font-size: 1.4rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.email {
  margin: 0.4rem 0 0 0;
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.2rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logout-btn {
  width: 100%;
}

.login-buttons {
  display: flex;
  gap: 0.8rem;
}

.auth-btn {
  flex: 1;
  pointer-events: auto;
}

.nav-menu {
  flex: 1;
  border: none;
  background-color: transparent;
}

.menu-disabled :deep(.el-menu-item) {
  opacity: 0.5;
  cursor: not-allowed;
}

.nav-menu-item {
  margin: 0.8rem 1.2rem !important;
  border-radius: 0.6rem !important;
  background: rgba(255, 255, 255, 0.08) !important;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
  pointer-events: auto;
}

.nav-menu-item:hover {
  background: rgba(255, 255, 255, 0.18) !important;
  transform: translateX(0.8rem);
}

.nav-menu-item.is-disabled {
  opacity: 0.5 !important;
  cursor: not-allowed !important;
  pointer-events: none !important;
}

.nav-menu-item.is-disabled:hover {
  background: rgba(255, 255, 255, 0.08) !important;
  transform: none !important;
}

.nav-icon {
  font-size: 2rem;
  min-width: 2.4rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-right: 1.2rem;
}

.sidebar-footer {
  padding: 3rem 2rem;
  border-top: 0.1rem solid rgba(255, 255, 255, 0.2);
  background: linear-gradient(180deg, transparent, rgba(0, 0, 0, 0.15));
  text-align: center;
  color: white;
}

.sidebar-footer :where(.el-statistic) {
  --el-text-color-primary: white;
}

.streak-statistic :where(.el-statistic__item-title) {
  color: white !important;
  font-size: 1.6rem !important;
  font-weight: 700 !important;
}

.yomii-content {
  padding: 4rem;
  background: rgba(255, 255, 255, 0.65);
  overflow-y: auto;
  position: relative;
  flex: 1;
}

/* 登录覆盖层 */
.login-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(0.2rem);
}

.overlay-content {
  text-align: center;
  padding: 4rem;
  animation: slideUp 0.3s ease-out;
}

.lock-icon {
  font-size: 6rem;
  color: #e74c3c;
  margin-bottom: 2rem;
  display: block;
}

.overlay-content h2 {
  font-size: 2.4rem;
  margin: 2rem 0 1rem;
  color: #333;
}

.overlay-content p {
  font-size: 1.4rem;
  color: #666;
  margin-bottom: 3rem;
}

.overlay-content .el-button {
  margin: 0 1rem;
}

/* 滚动条美化 */
.content::-webkit-scrollbar {
  width: 0.8rem;
}

.content::-webkit-scrollbar-track {
  background: transparent;
}

.content::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 0.4rem;
}

.content::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

.sidebar::-webkit-scrollbar {
  width: 0.4rem;
}

.sidebar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
}

.sidebar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 0.2rem;
}

.sidebar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

/* 进入动画 */
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(2rem);
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
    max-height: 100rem;
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
    box-shadow: 0 0 0.5rem rgba(102, 126, 234, 0.3);
  }
  50% {
    box-shadow: 0 0 2rem rgba(102, 126, 234, 0.6);
  }
  100% {
    box-shadow: 0 0 0.5rem rgba(102, 126, 234, 0.3);
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0rem);
  }
  50% {
    transform: translateY(-0.5rem);
  }
}

/* 对话框样式 */
.form-actions {
  text-align: right;
  margin-top: 1rem;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.reset-content {
  padding: 2rem 0;
  min-height: 20rem;
}

.reset-success {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 20rem;
  gap: 1rem;
}

.success-icon {
  font-size: 6rem;
  color: #67c23a;
}

.reset-success p {
  margin: 0;
  font-size: 1.6rem;
  color: #333;
}

:deep(.el-dialog) .el-form:first-child {
  margin-top: 2rem;
}

/* 对话框表单输入框样式 */
:deep(.el-dialog) .el-form-item {
  margin-bottom: 2rem;
}

:deep(.el-dialog) .el-form-item__label {
  width: 9rem !important;
  text-align: left !important;
  color: #333;
  font-weight: 500;
  padding-left: 1rem !important;
  justify-content: flex-start !important;
}

:deep(.el-dialog) .el-form-item__content {
  margin-left: 0 !important;
}

:deep(.el-dialog) .el-input {
  width: 100%;
}

:deep(.el-dialog) .el-input__inner {
  border: none !important;
  background-color: transparent !important;
  border-radius: 0 !important;
  padding: 0.8rem 0 !important;
  font-size: 1.4rem;
  transition: all 0.3s ease !important;
}

:deep(.el-dialog) .el-input__inner:focus {
  box-shadow: none !important;
}

:deep(.el-dialog) .el-input__inner::placeholder {
  color: #bfbfbf;
}

:deep(.el-dialog) .el-input__prefix,
:deep(.el-dialog) .el-input__suffix {
  background-color: transparent !important;
}

@media (max-height: 80rem) {
  .app-header {
    margin-bottom: 0rem;
  }

  .app-title {
    font-size: 3.8rem;
  }

  .yomii-content {
    padding: 4rem 6rem;
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
  font-size: 2.2rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.1rem !important;
  margin-bottom: 0.8rem !important;
}

/* 数字部分 (调小) */
.streak-statistic .el-statistic__content {
  color: #ffd700 !important;
  font-size: 2.6rem !important;
  font-weight: bold !important;
  text-shadow: 0 0.2rem 0.4rem rgba(0, 0, 0, 0.3) !important;
}

/* 单位：天 */
.streak-statistic .el-statistic__suffix {
  color: #ffd700 !important;
  font-size: 1.8rem !important;
  margin-left: 0.4rem !important;
}
</style>
