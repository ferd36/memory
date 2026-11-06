import { spawnSync } from 'child_process'
import fs from 'fs'
import os from 'os'
import path from 'path'
import { fileURLToPath } from 'url'
import { clearViolations, getViolations, setStrict, isStrict } from '../../src/main/invariants.js'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export const PROJECT_ROOT = path.resolve(__dirname, '../..')
export const MAIN_DIR = path.join(PROJECT_ROOT, 'src/main')
export const BRIDGE_PATH = path.join(MAIN_DIR, 'bridge.py')
export const PYTHON_PATH = '/Users/frank/Files/sandbox/src/.venv/bin/python'

/**
 * Integration tests shell out to a specific virtualenv interpreter. On a
 * machine without it they skip rather than fail, so the fast suite stays green
 * everywhere. Pass the result as node:test's `skip` option.
 */
export function pythonUnavailable() {
  if (!fs.existsSync(PYTHON_PATH)) return `python interpreter not found at ${PYTHON_PATH}`
  if (!fs.existsSync(BRIDGE_PATH)) return `bridge not found at ${BRIDGE_PATH}`
  return false
}

/** Hits the network (gnews, 15s timeout); excluded from the exhaustive sweep. */
export const NETWORK_DEPENDENT_TYPES = new Set(['SentenceCompletion'])

/** Mirrors TwoBackRecall.create's `tempfile.gettempdir()/memory_twoback.json`. */
export const TWO_BACK_HISTORY_FILE = path.join(os.tmpdir(), 'memory_twoback.json')

export function resetTwoBackHistory() {
  try {
    fs.unlinkSync(TWO_BACK_HISTORY_FILE)
  } catch {
    // Absent is the state we want.
  }
}

/**
 * Run bridge.py directly and return stdout, stderr and exit status.
 *
 * Deliberately uses spawnSync without a shell so the harness is not itself
 * subject to the quoting defect it exists to test for.
 */
export function runBridge(args, { strict = false, timeout = 60000 } = {}) {
  const env = { ...process.env }
  if (strict) env.MEMORY_TRAINER_STRICT = '1'
  else delete env.MEMORY_TRAINER_STRICT

  const result = spawnSync(PYTHON_PATH, [BRIDGE_PATH, ...args], {
    env,
    encoding: 'utf8',
    timeout,
  })

  return {
    status: result.status,
    stdout: result.stdout ?? '',
    stderr: result.stderr ?? '',
    invariants: parseInvariantLines(result.stderr ?? ''),
  }
}

/**
 * Run a python snippet with bridge.py importable, for exercising its invariant
 * helpers directly. No problem type currently violates a soft invariant — that
 * is the point of the fixes — so the mechanism needs a synthetic trigger.
 */
export function runPythonSnippet(snippet, { strict = false } = {}) {
  const env = { ...process.env }
  if (strict) env.MEMORY_TRAINER_STRICT = '1'
  else delete env.MEMORY_TRAINER_STRICT

  const preamble = [
    'import importlib.util, sys',
    `spec = importlib.util.spec_from_file_location('bridge', ${JSON.stringify(BRIDGE_PATH)})`,
    'bridge = importlib.util.module_from_spec(spec)',
    'spec.loader.exec_module(bridge)',
  ].join('\n')

  const result = spawnSync(PYTHON_PATH, ['-c', `${preamble}\n${snippet}`], {
    env,
    encoding: 'utf8',
    timeout: 60000,
  })

  return {
    status: result.status,
    stdout: result.stdout ?? '',
    stderr: result.stderr ?? '',
    invariants: parseInvariantLines(result.stderr ?? ''),
  }
}

/** Parse the `INVARIANT[CODE] message {json}` lines bridge.py writes to stderr. */
export function parseInvariantLines(stderr) {
  return String(stderr)
    .split('\n')
    .map(line => /^INVARIANT\[([A-Z_]+)\]\s+(.*)$/.exec(line.trim()))
    .filter(Boolean)
    .map(m => ({ code: m[1], message: m[2] }))
}

/**
 * Run `fn` with a clean violation log and return everything it recorded.
 * Errors are captured rather than thrown so a test can assert on both the
 * violations and the failure.
 */
export function collectViolations(fn, { strict = false } = {}) {
  const previousStrict = isStrict()
  clearViolations()
  setStrict(strict)
  try {
    const value = fn()
    return { value, violations: getViolations(), error: null }
  } catch (error) {
    return { value: undefined, violations: getViolations(), error }
  } finally {
    setStrict(previousStrict)
    clearViolations()
  }
}

/** Unique violation codes, sorted — handy for set-style assertions. */
export function uniqueCodes(violations) {
  return [...new Set(violations.map(v => v.code))].sort()
}
