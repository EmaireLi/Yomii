import { createRouter, createWebHistory } from 'vue-router'
import type { RouteLocationNormalized, NavigationGuardNext } from 'vue-router'
import { isAuthenticated, getCurrentUser } from '@/api'
import HomeView from '@/components/views/HomeView.vue'
import SearchView from '@/components/views/SearchView.vue'
import ReciteView from '@/components/views/ReciteView.vue'
import FavoritesView from '@/components/views/FavoritesView.vue'
import TestView from '@/components/views/TestView.vue'
import EssayView from '@/components/views/EssayView.vue'

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
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

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
  const title = to.meta.title as string
  document.title = title ? `${title} - Yomii` : 'Yomii - 日语学习助手'
})

export default router
