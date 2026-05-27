/**
 * main.ts
 * Electron 主进程入口（开发与生产共用）
 * - 在开发模式下，通过环境变量 `VITE_DEV_SERVER_URL` 加载 Vite 提供的页面
 * - 在生产模式下，加载构建输出 `dist/index.html`
 * - 在运行时会优先选择存在的 `dist-electron/preload.cjs`（如果有），否则回退到 `preload.js`
 * - 隐藏菜单栏但保留窗口控制按键（关闭/缩小），支持 Windows 和 macOS
 */
import { app, BrowserWindow, Menu } from 'electron'
import * as path from 'path'
import * as fs from 'fs'

let mainWindow: BrowserWindow | null = null

function createWindow() {
  // 根据平台设置不同的窗口配置
  const isMac = process.platform === 'darwin'
  const windowIcon = path.join(__dirname, '..', 'public', 'icon', 'yomii-logo.ico')
  
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    minWidth: 800,
    minHeight: 600,
    title: 'Yomii 辞书 - 日语词典学习应用',
    icon: windowIcon,
    // Mac: 保留系统按键，隐藏菜单栏; Windows: 使用标准窗口框架，隐藏菜单栏
    frame: true,
    // Mac 特定配置：保留红绿黄按钮并设置其位置
    ...(isMac && {
      trafficLightPosition: { x: 15, y: 10 },
    }),
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
      contextIsolation: true,
    },
  })

  // 完全隐藏菜单栏
  Menu.setApplicationMenu(null)

  // 开发时由 launcher 注入 VITE_DEV_SERVER_URL，生产时读取 dist/index.html
  const devUrl = process.env.VITE_DEV_SERVER_URL

  if (devUrl) {
    mainWindow.loadURL(devUrl)
  } else {
    // 生产环境：加载打包后的应用
    const appPath = app.getAppPath()
    const htmlPath = path.join(appPath, 'dist', 'index.html')
    mainWindow.loadFile(htmlPath).catch((err) => {
      console.error('[Electron] Failed to load HTML:', err)
    })
  }

  // Electron 在高 DPI 环境下会比浏览器更容易显得“放大”
  // 这里统一给一个轻微的缩放修正，避免字体和布局整体偏大
  mainWindow.webContents.on('did-finish-load', () => {
    if (!mainWindow) return
    mainWindow.webContents.setZoomFactor(0.8)
  })

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
