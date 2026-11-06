/**
 * Invariant / precondition layer.
 *
 * Two severities, deliberately different:
 *
 *   requires(...)  Hard precondition. Always throws. Reserved for programmer
 *                  errors — wrong arity, wrong type, out-of-range. Correct
 *                  callers never trip these, so adding them cannot change the
 *                  behaviour of a working code path.
 *
 *   checks(...)    Soft invariant. Records the violation and notifies any
 *                  listeners, but does NOT throw by default. Reserved for
 *                  conditions we know are currently violated by the app: they
 *                  document a bug at the exact point it happens without
 *                  altering what the app does today. Tests flip strict mode on
 *                  to turn them into failures.
 *
 * The split is what lets us instrument the code without fixing anything yet.
 */

export class PreconditionError extends Error {
  constructor(message, details) {
    super(message)
    this.name = 'PreconditionError'
    this.details = details
  }
}

export class InvariantViolation extends Error {
  constructor(code, message, details) {
    super(`[${code}] ${message}`)
    this.name = 'InvariantViolation'
    this.code = code
    this.details = details
  }
}

/**
 * Codes for the soft invariants. Each one corresponds to a known defect; the
 * comment says what is wrong so the violation log doubles as a bug inventory.
 */
export const VIOLATION = {
  // The solution needs a multiline input but the payload does not ask for one,
  // so it could never be entered correctly.
  UNANSWERABLE_SOLUTION: 'UNANSWERABLE_SOLUTION',
  // A path the app depends on did not resolve to an existing file.
  UNRESOLVED_PATH: 'UNRESOLVED_PATH',
  // A value crossed a boundary with a type or shape the consumer does not expect.
  PAYLOAD_SHAPE: 'PAYLOAD_SHAPE',
}

let strict = process.env.MEMORY_TRAINER_STRICT === '1'
let violations = []
let listeners = []

/** In strict mode soft invariants throw instead of being recorded. */
export function setStrict(value) {
  strict = Boolean(value)
}

export function isStrict() {
  return strict
}

/** Subscribe to soft violations. Returns an unsubscribe function. */
export function onViolation(listener) {
  listeners.push(listener)
  return () => {
    listeners = listeners.filter(l => l !== listener)
  }
}

/** Every soft violation recorded since the last clear. */
export function getViolations() {
  return violations.slice()
}

export function clearViolations() {
  violations = []
}

/**
 * Hard precondition. Throws PreconditionError when `condition` is falsy.
 */
export function requires(condition, message, details) {
  if (!condition) {
    throw new PreconditionError(message, details)
  }
}

/**
 * Soft invariant. Records when `condition` is falsy; throws only in strict mode.
 * Returns true when the invariant held, so callers can branch on it if needed.
 */
export function checks(condition, code, message, details) {
  if (condition) return true

  const violation = { code, message, details, at: new Date().toISOString() }
  violations.push(violation)
  for (const listener of listeners) listener(violation)

  if (strict) {
    throw new InvariantViolation(code, message, details)
  }
  return false
}

// --- Shared predicates -----------------------------------------------------

/** A non-empty, non-blank string. */
export function isNonBlankString(value) {
  return typeof value === 'string' && value.trim().length > 0
}

/** A positive integer (used for round numbers and exposure durations). */
export function isPositiveInteger(value) {
  return Number.isInteger(value) && value > 0
}
