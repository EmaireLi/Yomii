/**
 * preload.ts
 * 预加载脚本（preload）在独立的隔离上下文中运行，负责向渲染进程暴露安全的 API。
 * - 请保持导出接口最小化，仅暴露必要功能
 * - 由于此文件会被编译为 CommonJS（production/dev），请避免在暴露的代码中使用不受支持的浏览器 API
 */
import { contextBridge } from 'electron'

// 向渲染进程暴露安全的 API
contextBridge.exposeInMainWorld('electronAPI', {
  // 标记当前运行在 Electron 环境中
  isElectron: true,
  // 在这里添加你需要暴露给前端的方法，例如：
  // sendMessage: (msg) => ipcRenderer.send('channel', msg)
})
