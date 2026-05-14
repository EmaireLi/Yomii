import { createRouter, createMemoryHistory, createWebHistory } from 'vue-router'
import type { RouteLocationNormalized, NavigationGuardNext } from 'vue-router'
import { isAuthenticated } from '@/api'

// 使用动态导入（lazy loading）分离路由组件到独立的 chunk
// 这样首次加载时只需加载必需的代码，其他路由按需加载
const HomeView = () => import('@/views/HomeView.vue')
const SearchView = () => import('@/views/SearchView.vue')
const ReciteView = () => import('@/views/ReciteView.vue')
const FavoritesView = () => import('@/views/FavoritesView.vue')
const TestView = () => import('@/views/TestView.vue')
const EssayView = () => import('@/views/EssayView.vue')

// 路由配置
const routes = [
  {
    path: '/',
    redirect: '/home'
  },
  {
    path: '/home',
    name: 'home',
    component: HomeView,
    meta: { requiresAuth: false, title: '首页' }
  },
  {
    path: '/search',
    name: 'search',
    component: SearchView,
    meta: { requiresAuth: false, title: '查词' }
  },
  {
    path: '/recite',
    name: 'recite',
    component: ReciteView,
    meta: { requiresAuth: false, title: '背单词' }
  },
  {
    path: '/favorites',
    name: 'favorites',
    component: FavoritesView,
    meta: { requiresAuth: false, title: '我的收藏' }
  },
  {
    path: '/test',
    name: 'test',
    component: TestView,
    meta: { requiresAuth: false, title: '智能测试' }
  },
  {
    path: '/essay',
    name: 'essay',
    component: EssayView,
    meta: { requiresAuth: false, title: '作文评测' }
  }
]

// 创建路由实例
// Electron 环境使用 Memory 模式，网页环境使用 Web 模式
const isElectron = !!(window as any).electronAPI?.isElectron
const router = createRouter({
  history: isElectron ? createMemoryHistory() : createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 仅在 Electron 环境中初始化路由到首页
if (isElectron) {
  router.isReady().then(() => {
    if (router.currentRoute.value.path === '/') {
      router.push('/home')
    }
  })
}

/**
 * 路由前置守卫 - 检查认证状态
 */
router.beforeEach((to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
  // 检查路由是否需要认证
  const requiresAuth = to.matched.some(record => (record.meta?.requiresAuth as boolean))

  if (requiresAuth) {
    // 需要认证的路由
    if (isAuthenticated()) {
      // 用户已登录，允许访问
      next()
    } else {
      // 用户未登录，重定向到首页
      // 发送事件给 App.vue 打开登录对话框
      window.dispatchEvent(new CustomEvent('open-login-dialog'))
      next(false)
    }
  } else {
    // 不需要认证的路由，直接访问
    next()
  }
})

/**
 * 路由后置钩子 - 更新页面标题
 */
router.afterEach((to: RouteLocationNormalized) => {
  if (isElectron) return

  const title = to.meta.title as string
  document.title = title ? `${title} - Yomii` : 'Yomii - 日语学习助手'
})

export default router
