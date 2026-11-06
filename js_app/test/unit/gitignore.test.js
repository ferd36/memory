/**
 * Build output must not be committed. The repository .gitignore predates
 * js_app/, so dist/ and dist-electron/ showed up as untracked files.
 */
import { test, describe } from 'node:test'
import assert from 'node:assert/strict'
import { spawnSync } from 'child_process'
import path from 'path'

import { PROJECT_ROOT } from '../helpers/index.js'

const ignored = relative =>
  spawnSync('git', ['check-ignore', '-q', '--no-index', path.join(PROJECT_ROOT, relative)],
    { cwd: PROJECT_ROOT }).status === 0

const gitMissing = spawnSync('git', ['--version']).status !== 0

describe('.gitignore covers js_app build output', { skip: gitMissing && 'git is not installed' }, () => {
  for (const relative of ['dist/index.html', 'dist-electron/index.js', 'dist-electron/preload.mjs', 'node_modules/react/index.js']) {
    test(`ignores ${relative}`, () => {
      assert.equal(ignored(relative), true)
    })
  }

  test('does not ignore the sources', () => {
    assert.equal(ignored('src/main/index.js'), false)
    assert.equal(ignored('src/renderer/App.jsx'), false)
  })
})
