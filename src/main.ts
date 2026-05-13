import './assets/main.css'

import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(ElementPlus, {
  locale: zhCn
})
app.use(router)
app.mount('#app')

// 初始化 Canvas 动画（推迟到应用完全加载后）
// 使用 requestIdleCallback 在浏览器空闲时初始化，避免阻塞主线程
const initCanvasNest = async () => {
  try {
    const CanvasNestModule = await import('canvas-nest.js')
    const CanvasNest = (CanvasNestModule && (CanvasNestModule as any).default) || CanvasNestModule
    if (typeof CanvasNest === 'function') {
      new (CanvasNest as any)(document.getElementById("app"), {
        color: '16,24,32',
        pointColor: '16,24,32',
        opacity: 0.95,
        zIndex: -1,
        count: 300,
        pointerEvent: 'none'
      })
    }
  } catch (error) {
    console.error('CanvasNest 初始化失败：', error)
  }
}

// 首先等待应用挂载完成，然后等待 DOMContentLoaded，最后在浏览器空闲时初始化动画
if (typeof window !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      if (typeof requestIdleCallback !== 'undefined') {
        requestIdleCallback(initCanvasNest, { timeout: 2000 })
      } else {
        setTimeout(initCanvasNest, 500)
      }
    })
  } else {
    if (typeof requestIdleCallback !== 'undefined') {
      requestIdleCallback(initCanvasNest, { timeout: 2000 })
    } else {
      setTimeout(initCanvasNest, 500)
    }
  }
}