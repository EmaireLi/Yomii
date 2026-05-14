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

// 初始化 Canvas 动画
setTimeout(async () => {
  try {
    const CanvasNestModule = await import('canvas-nest.js')
    const CanvasNest = (CanvasNestModule as any).default || CanvasNestModule
    if (typeof CanvasNest === 'function') {
      new (CanvasNest as any)(document.getElementById('app'), {
        color: '16,24,32',
        pointColor: '16,24,32',
        opacity: 0.95,
        zIndex: -1,
        count: 300,
        pointerEvent: 'none'
      })
    }
  } catch (error) {
    console.error('CanvasNest init failed:', error)
  }
}, 500)