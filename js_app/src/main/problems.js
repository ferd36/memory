import { execFileSync } from 'child_process'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import {
  requires,
  checks,
  VIOLATION,
  isNonBlankString,
  isPositiveInteger,
} from './invariants.js'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

/**
 * bridge.py lives next to this file in the source tree. When Electron runs the
 * vite build instead, this module has been bundled into dist-electron/ and the
 * bridge is two levels up in src/main. Try both rather than baking in a path.
 */
function resolveBridge() {
  const candidates = [
    path.join(__dirname, 'bridge.py'),          // source tree
    path.join(__dirname, '../src/main/bridge.py'), // from dist-electron/
  ]
  const found = candidates.find(p => fs.existsSync(p))
  requires(found !== undefined,
    'bridge.py could not be located', { candidates })
  return found
}

/**
 * Interpreter resolution, most specific first:
 *   1. MEMORY_TRAINER_PYTHON, for anyone running against a different env
 *   2. the project's virtualenv, found by walking up from this file
 *   3. python3 on PATH
 * The virtualenv sits above the app directory, so search a few levels up
 * instead of assuming a fixed depth.
 */
function resolvePython() {
  if (process.env.MEMORY_TRAINER_PYTHON) return process.env.MEMORY_TRAINER_PYTHON

  let dir = __dirname
  for (let i = 0; i < 8; i++) {
    const candidate = path.join(dir, '.venv/bin/python')
    if (fs.existsSync(candidate)) return candidate
    const parent = path.dirname(dir)
    if (parent === dir) break
    dir = parent
  }
  return 'python3'
}

const bridgePath = resolveBridge()
const pythonPath = resolvePython()

export const RESOLVED_PATHS = { bridgePath, pythonPath }

/**
 * Fields the bridge promises to return from `create`, and the type each must
 * have. The renderer reads all of them, so a shape change here breaks the UI.
 */
export const CREATE_PAYLOAD_SHAPE = {
  display_name: isNonBlankString,
  memorize: isNonBlankString,
  prompt: isNonBlankString,
  solution: v => typeof v === 'string',
  exposure_ms: isPositiveInteger,
  input_type: isNonBlankString,
  is_scored: v => typeof v === 'boolean',
  state: v => v !== null && typeof v === 'object' && !Array.isArray(v),
}

/**
 * Run bridge.py with an argv array. No shell is involved, so arguments are
 * delivered to python byte for byte no matter what the user typed.
 */
function callBridge(args) {
  return execFileSync(pythonPath, [bridgePath, ...args], {
    encoding: 'utf8',
    maxBuffer: 10 * 1024 * 1024,
  })
}

export function get_problem_types() {
  try {
    const types = JSON.parse(callBridge(['get_types']))

    checks(Array.isArray(types), VIOLATION.PAYLOAD_SHAPE,
      'get_types did not return an array', { types })
    if (Array.isArray(types)) {
      for (const t of types) {
        checks(isNonBlankString(t?.id) && isNonBlankString(t?.name),
          VIOLATION.PAYLOAD_SHAPE, 'problem type entry must have id and name', { entry: t })
      }
    }

    return types
  } catch (e) {
    console.error("Error fetching types from python bridge:", e)
    return []
  }
}

export function create_problem(type, round = 1) {
  requires(isNonBlankString(type), 'type must be a non-blank string', { type })
  requires(isPositiveInteger(Number(round)), 'round must be a positive integer', { round })

  try {
    const p = JSON.parse(callBridge(['create', type, String(round)]))
    // Add the problem type so we can pass it back for evaluation
    p.type_id = type

    assertCreatePayload(p, type)
    return p
  } catch (e) {
    console.error(`Error creating problem ${type}:`, e)
    throw e
  }
}

export function evaluate_problem(type, solution, user_input, state = {}) {
  requires(isNonBlankString(type), 'type must be a non-blank string', { type })
  requires(typeof solution === 'string', 'solution must be a string', { solution })
  requires(typeof user_input === 'string', 'user_input must be a string', { user_input })
  requires(state !== null && typeof state === 'object' && !Array.isArray(state),
    'state must be a plain object', { state })

  try {
    const result = JSON.parse(
      callBridge(['evaluate', type, solution, user_input, JSON.stringify(state)]))

    checks(typeof result?.correct === 'boolean', VIOLATION.PAYLOAD_SHAPE,
      'evaluate must return a boolean `correct`', { result })
    checks(typeof result?.score === 'number' && result.score >= 0 && result.score <= 1,
      VIOLATION.PAYLOAD_SHAPE, 'evaluate must return a score in [0, 1]', { result })

    return { ...result, fallback: false }
  } catch (e) {
    console.error(`Error evaluating problem ${type}:`, e)
    // Fallback to strict match. Same shape as the success path so callers never
    // have to special-case it; `fallback` lets the renderer warn that partial
    // credit and custom scoring did not apply.
    const correct = solution.trim().toLowerCase() === user_input.trim().toLowerCase()
    return { score: correct ? 1 : 0, correct, fallback: true }
  }
}

/**
 * Postcondition on a create payload: the shape the renderer depends on.
 */
function assertCreatePayload(p, type) {
  checks(p !== null && typeof p === 'object', VIOLATION.PAYLOAD_SHAPE,
    'create must return an object', { type, payload: p })
  if (p === null || typeof p !== 'object') return

  for (const [field, predicate] of Object.entries(CREATE_PAYLOAD_SHAPE)) {
    checks(predicate(p[field]), VIOLATION.PAYLOAD_SHAPE,
      `create payload field \`${field}\` has an unexpected value`,
      { type, field, value: p[field] })
  }

  // A multi-line solution needs the multiline input; flag any payload that
  // asks for one without declaring it.
  checks(typeof p.solution !== 'string' || !p.solution.includes('\n') || p.input_type === 'multiline',
    VIOLATION.UNANSWERABLE_SOLUTION,
    'solution spans multiple lines but input_type does not ask for a multiline input',
    { type, solution: p.solution, input_type: p.input_type })
}
