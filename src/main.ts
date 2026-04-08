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

// 初始化 Canvas 动画（仅浏览器端 / 动态导入）
window.addEventListener('load', async () => {
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
      
    //   // 修复动画层：添加 pointer-events: none 使其不妨碍交互
    //   const canvasEl = document.getElementById('c_n1')
    //   if (canvasEl) {
    //     canvasEl.style.pointerEvents = 'none'
    //     canvasEl.style.zIndex = '2'
    //   }
    }
  } catch (error) {
    console.error('CanvasNest 初始化失败：', error)
  }
})

