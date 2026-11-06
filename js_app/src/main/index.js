import { app, BrowserWindow, ipcMain } from 'electron'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { create_problem, get_problem_types, evaluate_problem } from './problems.js'
import { requires, checks, VIOLATION, isNonBlankString, isPositiveInteger } from './invariants.js'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

/**
 * This module runs from two different directories: src/main/ when Electron
 * loads the source tree, and dist-electron/ when it loads the vite build. The
 * preload has a different extension in each (vite emits .mjs) and the renderer
 * entry sits at a different depth, so try the candidates for both layouts
 * rather than assuming one.
 */
export function resolveWindowPaths(baseDir) {
  const firstExisting = candidates =>
    candidates.find(p => fs.existsSync(p)) ?? candidates[0]

  return {
    preload: firstExisting([
      path.join(baseDir, 'preload.mjs'), // vite build output
      path.join(baseDir, 'preload.js'),  // source tree
    ]),
    indexHtml: firstExisting([
      path.join(baseDir, '../dist/index.html'),    // from dist-electron/
      path.join(baseDir, '../../dist/index.html'), // from src/main/
    ]),
  }
}

function createWindow() {
  const paths = resolveWindowPaths(__dirname)

  checks(fs.existsSync(paths.preload), VIOLATION.UNRESOLVED_PATH,
    'preload script does not exist at the resolved path; window.api will be undefined',
    { preload: paths.preload, baseDir: __dirname })

  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: paths.preload,
    },
  })

  // Vite development server URL
  if (process.env.VITE_DEV_SERVER_URL) {
    win.loadURL(process.env.VITE_DEV_SERVER_URL)
  } else {
    checks(fs.existsSync(paths.indexHtml), VIOLATION.UNRESOLVED_PATH,
      'renderer entry does not exist at the resolved path',
      { indexHtml: paths.indexHtml, baseDir: __dirname })
    win.loadFile(paths.indexHtml)
  }
}

app.whenReady().then(() => {
  // Arguments crossing the IPC boundary come from the renderer and are
  // untrusted; validate them here rather than letting them reach the shell.
  ipcMain.handle('get-problem-types', () => get_problem_types())

  ipcMain.handle('create-problem', (event, type, round) => {
    requires(isNonBlankString(type), 'create-problem: type must be a non-blank string', { type })
    requires(isPositiveInteger(round), 'create-problem: round must be a positive integer', { round })
    return create_problem(type, round)
  })

  ipcMain.handle('evaluate-problem', (event, type, solution, user_input, state) => {
    requires(isNonBlankString(type), 'evaluate-problem: type must be a non-blank string', { type })
    requires(typeof solution === 'string', 'evaluate-problem: solution must be a string', { solution })
    requires(typeof user_input === 'string', 'evaluate-problem: user_input must be a string', { user_input })
    return evaluate_problem(type, solution, user_input, state ?? {})
  })

  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
