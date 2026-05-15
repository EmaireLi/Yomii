/**
 * main.ts
 * Electron 主进程入口（开发与生产共用）
 * - 在开发模式下，通过环境变量 `VITE_DEV_SERVER_URL` 加载 Vite 提供的页面
 * - 在生产模式下，加载构建输出 `dist/index.html`
 * - 在运行时会优先选择存在的 `dist-electron/preload.cjs`（如果有），否则回退到 `preload.js`
 * - 隐藏菜单栏但保留窗口控制按键（关闭/缩小），支持 Windows 和 macOS
 */
import { app, BrowserWindow, Menu, dialog } from 'electron'
import * as path from 'path'
import * as fs from 'fs'
import { spawn, spawnSync, ChildProcessWithoutNullStreams } from 'child_process'

let mainWindow: BrowserWindow | null = null
let backendProcess: ChildProcessWithoutNullStreams | null = null
let isQuitting = false

const BACKEND_PORT = 8000
const BACKEND_HOST = '127.0.0.1'

function resolveProjectRoot(): string {
  return app.isPackaged ? process.resourcesPath : path.join(__dirname, '..')
}

function resolveBackendDir(): string {
  return app.isPackaged
    ? path.join(process.resourcesPath, 'backend')
    : path.join(resolveProjectRoot(), 'backend')
}

function resolveBackendExecutable(): string | null {
  if (!app.isPackaged) return null
  const executableName = process.platform === 'win32' ? 'yomii-backend.exe' : 'yomii-backend'
  const target = path.join(resolveBackendDir(), executableName)
  return fs.existsSync(target) ? target : null
}

function resolveIconPath(): string {
  return app.isPackaged
    ? path.join(process.resourcesPath, 'public', 'yomii.ico')
    : path.join(resolveProjectRoot(), 'public', 'yomii.ico')
}

async function waitForBackendReady(timeoutMs = 20000): Promise<boolean> {
  const start = Date.now()
  const healthUrl = `http://${BACKEND_HOST}:${BACKEND_PORT}/health`

  while (Date.now() - start < timeoutMs) {
    try {
      const response = await fetch(healthUrl)
      if (response.ok) return true
    } catch {
      // ignore and retry
    }
    await new Promise(resolve => setTimeout(resolve, 500))
  }

  return false
}

function stopBackendProcess(): void {
  if (!backendProcess) {
    return
  }

  const processToStop = backendProcess
  backendProcess = null

  try {
    processToStop.stdout.removeAllListeners()
    processToStop.stderr.removeAllListeners()
    processToStop.removeAllListeners()
  } catch {
    // ignore listener cleanup failures during shutdown
  }

  try {
    processToStop.stdout.destroy()
    processToStop.stderr.destroy()
  } catch {
    // ignore stdio cleanup failures during shutdown
  }

  try {
    if (process.platform === 'win32') {
      spawnSync('taskkill', ['/PID', String(processToStop.pid), '/T', '/F'], {
        stdio: 'ignore',
        windowsHide: true,
      })
    } else {
      processToStop.kill('SIGTERM')
    }
  } catch {
    try {
      processToStop.kill('SIGKILL')
    } catch {
      // process already exited
    }
  }
}

async function startBackendIfNeeded(): Promise<void> {
  if (backendProcess || process.env.VITE_DEV_SERVER_URL) {
    return
  }

  const backendDir = resolveBackendDir()
  const backendExecutable = resolveBackendExecutable()
  const pythonExecutable = process.env.YOMII_PYTHON_EXECUTABLE || (process.platform === 'win32' ? 'python' : 'python3')
  const env = {
    ...process.env,
    USER_DATABASE_BACKEND: 'sqlite',
    USER_SQLITE_DATABASE_PATH: path.join(backendDir, 'data', 'user_data.db'),
    SQLITE_DATABASE_PATH: path.join(backendDir, 'data', 'dictionary.db'),
    ENABLE_ESSAY_EVALUATION: 'false',
    ENABLE_DEFAULT_AUTO_LOGIN: 'true',
    DEFAULT_RELEASE_USERNAME: '丰川祥子',
    DEFAULT_RELEASE_PHONE: '18800000000',
    DEEPSEEK_API_KEY: '',
    DEEPSEEK_BASE_URL: '',
    DEEPSEEK_MODEL: '',
    ESSAY_SCORE_MODEL_URL: '',
    ESSAY_REVISION_MODEL_URL: '',
    YOMII_BACKEND_PORT: String(BACKEND_PORT),
  }

  if (backendExecutable) {
    backendProcess = spawn(
      backendExecutable,
      [],
      {
        cwd: backendDir,
        env,
        stdio: 'pipe',
      }
    )
  } else {
    backendProcess = spawn(
      pythonExecutable,
      ['-m', 'uvicorn', 'app.main:app', '--host', BACKEND_HOST, '--port', String(BACKEND_PORT)],
      {
        cwd: backendDir,
        env: { ...env, PYTHONPATH: backendDir },
        stdio: 'pipe',
      }
    )
  }

  backendProcess.stdout.on('data', data => {
    process.stdout.write(`[backend] ${data}`)
  })
  backendProcess.stderr.on('data', data => {
    process.stderr.write(`[backend] ${data}`)
  })
  backendProcess.on('exit', code => {
    backendProcess = null
    console.log(`[backend] exited with code ${code ?? 0}`)
  })
  backendProcess.on('error', async error => {
    console.error('[backend] failed to start:', error)
    await dialog.showErrorBox(
      'Yomii 后端启动失败',
      `无法启动本地后端服务。\n\n开发模式请确认已安装 Python 3.11+，并已在当前环境安装 backend/requirements.txt 依赖。\n\n错误信息：${String(error)}`
    )
  })

  const ready = await waitForBackendReady()
  if (!ready) {
    await dialog.showErrorBox(
      'Yomii 后端未就绪',
      '发布版尝试启动本地后端超时。请确认当前机器已安装 Python 3.11+，并且 backend/requirements.txt 依赖可用。'
    )
  }
}

async function createWindow() {
  // 根据平台设置不同的窗口配置
  const isMac = process.platform === 'darwin'

  await startBackendIfNeeded()
  
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    minWidth: 800,
    minHeight: 600,
    icon: fs.existsSync(resolveIconPath()) ? resolveIconPath() : undefined,
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

  mainWindow.on('close', () => {
    if (!isQuitting && process.platform !== 'darwin') {
      isQuitting = true
      app.quit()
    }
  })
}

app.on('ready', () => {
  void createWindow()
})

app.on('window-all-closed', () => {
  stopBackendProcess()
  if (process.platform !== 'darwin') {
    isQuitting = true
    app.quit()
  }
})

app.on('before-quit', () => {
  isQuitting = true
  stopBackendProcess()
})

app.on('will-quit', () => {
  stopBackendProcess()
})

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow()
  }
})
