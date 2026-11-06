/**
 * Build-layout invariants.
 *
 * src/main/index.js runs from two directories: src/main/ when Electron loads
 * the source tree, and dist-electron/ when it loads the vite build. The preload
 * has a different extension in each (vite emits .mjs) and the renderer entry
 * sits at a different depth. resolveWindowPaths must produce working paths for
 * both — it previously hardcoded the source-tree spelling, so the built app
 * loaded no preload at all and window.api was undefined.
 *
 * index.js cannot be imported outside Electron (it takes named imports from the
 * CommonJS `electron` module), so resolveWindowPaths is re-implemented here from
 * the source, guarded by a test that re-reads it to catch drift.
 */
import { test, describe } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'fs'
import path from 'path'

import { PROJECT_ROOT, MAIN_DIR } from '../helpers/index.js'

const SRC_MAIN = MAIN_DIR
const DIST_ELECTRON = path.join(PROJECT_ROOT, 'dist-electron')
const indexSource = fs.readFileSync(path.join(SRC_MAIN, 'index.js'), 'utf8')

/** Mirror of resolveWindowPaths in src/main/index.js. */
const resolveWindowPaths = baseDir => {
  const firstExisting = candidates => candidates.find(p => fs.existsSync(p)) ?? candidates[0]
  return {
    preload: firstExisting([
      path.join(baseDir, 'preload.mjs'),
      path.join(baseDir, 'preload.js'),
    ]),
    indexHtml: firstExisting([
      path.join(baseDir, '../dist/index.html'),
      path.join(baseDir, '../../dist/index.html'),
    ]),
  }
}

describe('the mirror above still matches index.js', () => {
  test('preload candidates are preload.mjs then preload.js', () => {
    assert.match(indexSource, /path\.join\(baseDir, 'preload\.mjs'\)/)
    assert.match(indexSource, /path\.join\(baseDir, 'preload\.js'\)/)
  })

  test('renderer entry candidates are ../dist then ../../dist', () => {
    assert.match(indexSource, /path\.join\(baseDir, '\.\.\/dist\/index\.html'\)/)
    assert.match(indexSource, /path\.join\(baseDir, '\.\.\/\.\.\/dist\/index\.html'\)/)
  })

  test('the resolved paths are what BrowserWindow and loadFile actually receive', () => {
    // Regression guard: the literals used to be duplicated at the call sites,
    // so the existence checks could pass while the window used a different path.
    assert.match(indexSource, /preload: paths\.preload/)
    assert.match(indexSource, /win\.loadFile\(paths\.indexHtml\)/)
    assert.equal(/preload: path\.join\(__dirname/.test(indexSource), false)
    assert.equal(/loadFile\(path\.join\(__dirname/.test(indexSource), false)
  })
})

describe('source-tree layout', () => {
  const paths = resolveWindowPaths(SRC_MAIN)

  test('the preload resolves to a file that exists', () => {
    assert.ok(fs.existsSync(paths.preload))
    assert.equal(path.basename(paths.preload), 'preload.js')
  })

  test('the renderer entry resolves inside the project', () => {
    assert.equal(path.resolve(paths.indexHtml), path.join(PROJECT_ROOT, 'dist/index.html'))
  })
})

describe('build-output layout', () => {
  const built = fs.existsSync(DIST_ELECTRON)
  const skip = built ? false : 'dist-electron/ not present — run `npm run build` first'

  test('vite emits the preload as preload.mjs', { skip }, () => {
    assert.ok(fs.existsSync(path.join(DIST_ELECTRON, 'preload.mjs')))
  })

  test('the preload resolves to the .mjs the build actually emits', { skip }, () => {
    const { preload } = resolveWindowPaths(DIST_ELECTRON)
    assert.ok(fs.existsSync(preload), `${preload} should exist`)
    assert.equal(path.basename(preload), 'preload.mjs')
  })

  test('the renderer entry resolves inside the project, not one level above', { skip }, () => {
    const { indexHtml } = resolveWindowPaths(DIST_ELECTRON)
    assert.equal(path.resolve(indexHtml), path.join(PROJECT_ROOT, 'dist/index.html'))
    assert.ok(fs.existsSync(indexHtml))
  })

  test('never resolves outside the project root', { skip }, () => {
    for (const baseDir of [SRC_MAIN, DIST_ELECTRON]) {
      for (const resolved of Object.values(resolveWindowPaths(baseDir))) {
        assert.ok(path.resolve(resolved).startsWith(PROJECT_ROOT),
          `${resolved} escaped the project root`)
      }
    }
  })
})

describe('package.json entry point', () => {
  const pkg = JSON.parse(fs.readFileSync(path.join(PROJECT_ROOT, 'package.json'), 'utf8'))

  test('main points at the vite build output', () => {
    assert.equal(pkg.main, 'dist-electron/index.js')
  })

  test('the file main names is produced by the build', { skip: fs.existsSync(DIST_ELECTRON) ? false : 'no build output' }, () => {
    assert.ok(fs.existsSync(path.join(PROJECT_ROOT, pkg.main)))
  })
})
