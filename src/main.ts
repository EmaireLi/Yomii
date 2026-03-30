import './assets/main.css'

import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import App from './App.vue'

const app = createApp(App)
app.use(ElementPlus, {
  locale: zhCn
})
app.mount('#app')

// 初始化 Canvas 动画（仅浏览器端 / 动态导入）
window.addEventListener('load', async () => {
  try {
    const CanvasNestModule = await import('canvas-nest.js')
    const CanvasNest = (CanvasNestModule && (CanvasNestModule as any).default) || CanvasNestModule
    if (typeof CanvasNest === 'function') {
      new (CanvasNest as any)(document.body, {
        color: '0,0,0',
        pointColor: '0,0,0',
        opacity: 0.8,
        zIndex: 9999,
        count: 100
      })
      
      // 修复动画层：添加 pointer-events: none 使其不妨碍交互
      const canvasEl = document.getElementById('c_n1')
      if (canvasEl) {
        canvasEl.style.pointerEvents = 'none'
        canvasEl.style.zIndex = '9999'
      }
    }
  } catch (error) {
    console.error('CanvasNest 初始化失败：', error)
  }
})

