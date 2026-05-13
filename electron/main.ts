/**
 * main.ts
 * Electron 主进程入口（开发与生产共用）
 * - 在开发模式下，通过环境变量 `VITE_DEV_SERVER_URL` 加载 Vite 提供的页面
 * - 在生产模式下，加载构建输出 `dist/index.html`
 * - 在运行时会优先选择存在的 `dist-electron/preload.cjs`（如果有），否则回退到 `preload.js`
 */
import { app, BrowserWindow } from 'electron'
import * as path from 'path'
import * as fs from 'fs'

let mainWindow: BrowserWindow | null = null

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      // 运行时选择 preload 文件，优先使用 CommonJS 编译产物 preload.cjs
      preload: ((): string => {
        const base = path.join(__dirname, '..', 'dist-electron')
        const cjs = path.join(base, 'preload.cjs')
        const js = path.join(base, 'preload.js')
        if (fs.existsSync(cjs)) return cjs
        return js
      })(),
      nodeIntegration: false,
      contextIsolation: true
    }
  })

  // 开发时由 launcher 注入 VITE_DEV_SERVER_URL，生产时读取 dist/index.html
  const devUrl = process.env.VITE_DEV_SERVER_URL
  const prodFile = path.join(__dirname, '..', 'dist', 'index.html')

  if (devUrl) {
    mainWindow.loadURL(devUrl)
  } else {
    mainWindow.loadFile(prodFile)
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

app.on('ready', createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow()
  }
})
