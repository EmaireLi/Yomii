import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  // 优化构建配置，改善首次加载和代码分割
  build: {
    target: 'ES2020',
    rollupOptions: {
      output: {
        // 代码分割策略：将依赖和路由分别打包成独立的 chunk
        manualChunks: {
          // 将 Element Plus 及相关依赖分离
          'element-plus': ['element-plus'],
          // 将 Vue 相关依赖分离
          'vue': ['vue', 'vue-router'],
          // Canvas-nest 单独分离
          'canvas-nest': ['canvas-nest.js'],
        }
      }
    }
  },
  // 开发服务器优化
  server: {
    // 预热常用模块，加快开发服务器启动
    preTransformRequests: ['/src/main.ts', '/src/App.vue'],
    // 启用缓存，加快重新启动
    middlewareMode: false,
  }
})
