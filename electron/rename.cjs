/*
  rename.cjs
  用途：TypeScript 编译 Electron 源代码后，部分环境下会产出 ESM 风格的 `.js` 文件，
  在 package.json 包含 "type": "module" 时，Node 会把 .js 当作 ESM 去加载，导致 require/预加载不兼容。
  该脚本将 tsc 输出的 main.js / preload.js 重命名为 .cjs，明确表示 CommonJS 模块，
  以便 Electron 在运行时按 CommonJS 加载它们。
*/
const fs = require('fs')
const path = require('path')

const out = path.join(__dirname, '..', 'dist-electron')

try {
  if (fs.existsSync(path.join(out, 'main.js'))){
    fs.renameSync(path.join(out, 'main.js'), path.join(out, 'main.cjs'))
  }
  if (fs.existsSync(path.join(out, 'preload.js'))){
    fs.renameSync(path.join(out, 'preload.js'), path.join(out, 'preload.cjs'))
  }
  console.log('Renamed electron build outputs to .cjs')
} catch (err) {
  console.error('Failed to rename electron build outputs:', err)
  process.exit(1)
}
