/**
 * Regression net for the command-injection fix.
 *
 * evaluate_problem used to build a /bin/sh command string and interpolate the
 * user's answer into it, escaping only `"`. Anything the user typed containing
 * `$` or a backtick was executed. The fix was to drop the shell entirely and
 * pass an argv array to execFileSync.
 *
 * These are source-level guards: they fail if anyone reintroduces a shell.
 * The behavioural half — arguments arriving at python byte for byte — lives in
 * integration/evaluation.test.js.
 */
import { test, describe } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'fs'
import path from 'path'

import { MAIN_DIR } from '../helpers/index.js'
import { RESOLVED_PATHS } from '../../src/main/problems.js'

const source = fs.readFileSync(path.join(MAIN_DIR, 'problems.js'), 'utf8')

describe('no shell is involved in reaching the bridge', () => {
  test('execFileSync is imported, execSync is not', () => {
    assert.match(source, /import \{ execFileSync \} from 'child_process'/)
    assert.equal(/\bexecSync\b/.test(source), false)
  })

  test('nothing spawns through exec, spawn or a shell option', () => {
    assert.equal(/\bexec\s*\(/.test(source), false)
    assert.equal(/shell:\s*true/.test(source), false)
    assert.equal(/require\(['"]child_process['"]\)/.test(source), false)
  })

  test('there is no argument-escaping helper left to be wrong', () => {
    // Correct quoting is the shell's problem only if you use one. We do not.
    assert.equal(/escapeArg/.test(source), false)
    assert.equal(/replace\(\/"\/g/.test(source), false)
  })

  test('the interpreter and script are passed as separate argv entries', () => {
    assert.match(source, /execFileSync\(pythonPath, \[bridgePath, \.\.\.args\]/)
  })

  test('no template literal builds a command out of the resolved paths', () => {
    assert.equal(/`\$\{pythonPath\}/.test(source), false)
    assert.equal(/\$\{bridgePath\}/.test(source), false)
  })
})

describe('path resolution is not machine-specific', () => {
  test('no absolute /Users path is hardcoded', () => {
    assert.equal(/['"]\/Users\//.test(source), false)
  })

  test('the bridge resolves to a file that exists', () => {
    assert.ok(fs.existsSync(RESOLVED_PATHS.bridgePath))
    assert.equal(path.basename(RESOLVED_PATHS.bridgePath), 'bridge.py')
  })

  test('the bridge resolves relative to this module, not a fixed location', () => {
    assert.match(source, /path\.join\(__dirname, 'bridge\.py'\)/)
  })

  test('the interpreter resolves to something runnable', () => {
    const { pythonPath } = RESOLVED_PATHS
    assert.ok(pythonPath === 'python3' || fs.existsSync(pythonPath),
      `${pythonPath} should exist or be the PATH fallback`)
  })

  test('MEMORY_TRAINER_PYTHON is honoured as an override', () => {
    assert.match(source, /process\.env\.MEMORY_TRAINER_PYTHON/)
  })

  test('the virtualenv is found by walking up, not by a fixed depth', () => {
    assert.match(source, /\.venv\/bin\/python/)
    assert.equal(/\.\.\/\.\.\/\.\.\/\.venv/.test(source), false)
  })

  test('falls back to python3 on PATH when no virtualenv is found', () => {
    assert.match(source, /return 'python3'/)
  })
})
