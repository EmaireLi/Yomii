/*
  dev.mjs
  启动器：以编程方式启动 Vite 开发服务器，获取实际分配的本地 URL，
  然后启动 Electron 并把该 URL 注入为环境变量 `VITE_DEV_SERVER_URL`。
  这样 Electron 无需固定端口，能自动跟随 Vite 使用的端口（5173/5174 等）。
*/
import { createServer } from 'vite'
import { spawn } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const electronEntry = path.join(projectRoot, 'node_modules', 'electron', 'cli.js')

function exit(code = 0) {
  process.exit(code)
}

async function main() {
  // 创建并启动 Vite 开发服务器。
  // 注意：不固定端口（port: 0）让 Vite 在端口被占用时自动选择可用端口。
  const viteServer = await createServer({
    root: projectRoot,
    configFile: path.join(projectRoot, 'vite.config.ts'),
    server: {
      host: '127.0.0.1',
      port: 0
    }
  })

  await viteServer.listen()

  // resolvedUrls.local[0] 是本地可访问的 URL，例如 http://localhost:5173
  const devUrl = viteServer.resolvedUrls?.local?.[0]
  if (!devUrl) {
    throw new Error('Unable to resolve the Vite dev server URL.')
  }

  const electronProcess = spawn(process.execPath, [electronEntry, '.'], {
    cwd: projectRoot,
    env: {
      ...process.env,
      VITE_DEV_SERVER_URL: devUrl,
      ELECTRON_DISABLE_SECURITY_WARNINGS: 'true'
    },
    stdio: 'inherit'
  })

  const shutdown = async (code = 0) => {
    electronProcess.kill()
    await viteServer.close()
    exit(code)
  }

  electronProcess.on('exit', async code => {
    await viteServer.close()
    exit(code ?? 0)
  })

  process.on('SIGINT', () => {
    void shutdown(0)
  })

  process.on('SIGTERM', () => {
    void shutdown(0)
  })

  console.log(`Vite dev server: ${devUrl}`)
}

main().catch(async error => {
  console.error(error)
  exit(1)
})
