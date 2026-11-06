import { test, describe, beforeEach, afterEach } from 'node:test'
import assert from 'node:assert/strict'

import {
  PreconditionError,
  InvariantViolation,
  VIOLATION,
  requires,
  checks,
  setStrict,
  isStrict,
  onViolation,
  getViolations,
  clearViolations,
  isNonBlankString,
  isPositiveInteger,
} from '../../src/main/invariants.js'

beforeEach(() => {
  clearViolations()
  setStrict(false)
})

afterEach(() => {
  clearViolations()
  setStrict(false)
})

describe('requires (hard preconditions)', () => {
  test('is a no-op when the condition holds', () => {
    assert.doesNotThrow(() => requires(true, 'never seen'))
  })

  test('throws PreconditionError with the message when the condition fails', () => {
    assert.throws(
      () => requires(false, 'round must be positive'),
      err => err instanceof PreconditionError && err.message === 'round must be positive',
    )
  })

  test('carries structured details onto the error', () => {
    try {
      requires(false, 'bad round', { round: -1 })
      assert.fail('should have thrown')
    } catch (err) {
      assert.deepEqual(err.details, { round: -1 })
    }
  })

  test('throws regardless of strict mode — it is not a soft check', () => {
    setStrict(false)
    assert.throws(() => requires(false, 'still throws'), PreconditionError)
  })

  test('does not record a soft violation', () => {
    assert.throws(() => requires(false, 'x'))
    assert.deepEqual(getViolations(), [])
  })
})

describe('checks (soft invariants)', () => {
  test('returns true and records nothing when the condition holds', () => {
    assert.equal(checks(true, VIOLATION.PAYLOAD_SHAPE, 'fine'), true)
    assert.deepEqual(getViolations(), [])
  })

  test('returns false and records when the condition fails', () => {
    assert.equal(checks(false, VIOLATION.PAYLOAD_SHAPE, 'bad shape', { field: 'solution' }), false)

    const violations = getViolations()
    assert.equal(violations.length, 1)
    assert.equal(violations[0].code, VIOLATION.PAYLOAD_SHAPE)
    assert.equal(violations[0].message, 'bad shape')
    assert.deepEqual(violations[0].details, { field: 'solution' })
  })

  test('does NOT throw in the default mode — instrumentation must not change behaviour', () => {
    assert.doesNotThrow(() => checks(false, VIOLATION.UNANSWERABLE_SOLUTION, 'unsafe'))
  })

  test('throws InvariantViolation in strict mode', () => {
    setStrict(true)
    assert.throws(
      () => checks(false, VIOLATION.UNANSWERABLE_SOLUTION, 'unsafe'),
      err => err instanceof InvariantViolation && err.code === VIOLATION.UNANSWERABLE_SOLUTION,
    )
  })

  test('strict-mode violations are still recorded before throwing', () => {
    setStrict(true)
    assert.throws(() => checks(false, VIOLATION.PAYLOAD_SHAPE, 'boom'))
    assert.equal(getViolations().length, 1)
  })

  test('accumulates violations in order', () => {
    checks(false, VIOLATION.PAYLOAD_SHAPE, 'first')
    checks(false, VIOLATION.UNANSWERABLE_SOLUTION, 'second')
    assert.deepEqual(
      getViolations().map(v => v.message),
      ['first', 'second'],
    )
  })

  test('timestamps each violation', () => {
    checks(false, VIOLATION.PAYLOAD_SHAPE, 'stamped')
    assert.match(getViolations()[0].at, /^\d{4}-\d{2}-\d{2}T/)
  })
})

describe('violation log', () => {
  test('getViolations returns a copy, not the live array', () => {
    checks(false, VIOLATION.PAYLOAD_SHAPE, 'one')
    const snapshot = getViolations()
    checks(false, VIOLATION.PAYLOAD_SHAPE, 'two')
    assert.equal(snapshot.length, 1)
    assert.equal(getViolations().length, 2)
  })

  test('clearViolations empties it', () => {
    checks(false, VIOLATION.PAYLOAD_SHAPE, 'one')
    clearViolations()
    assert.deepEqual(getViolations(), [])
  })
})

describe('onViolation listeners', () => {
  test('notifies subscribers', () => {
    const seen = []
    const unsubscribe = onViolation(v => seen.push(v.code))
    checks(false, VIOLATION.UNANSWERABLE_SOLUTION, 'multi-line')
    unsubscribe()

    assert.deepEqual(seen, [VIOLATION.UNANSWERABLE_SOLUTION])
  })

  test('unsubscribe stops notifications', () => {
    const seen = []
    const unsubscribe = onViolation(v => seen.push(v.code))
    unsubscribe()
    checks(false, VIOLATION.PAYLOAD_SHAPE, 'after unsubscribe')
    assert.deepEqual(seen, [])
  })

  test('notifies before throwing in strict mode', () => {
    const seen = []
    const unsubscribe = onViolation(v => seen.push(v.code))
    setStrict(true)
    assert.throws(() => checks(false, VIOLATION.PAYLOAD_SHAPE, 'boom'))
    unsubscribe()
    assert.deepEqual(seen, [VIOLATION.PAYLOAD_SHAPE])
  })
})

describe('setStrict / isStrict', () => {
  test('round-trips', () => {
    setStrict(true)
    assert.equal(isStrict(), true)
    setStrict(false)
    assert.equal(isStrict(), false)
  })

  test('coerces truthy values to booleans', () => {
    setStrict('yes')
    assert.equal(isStrict(), true)
  })
})

describe('isNonBlankString', () => {
  const accepted = ['a', ' padded ', '0', '▶']
  const rejected = ['', '   ', '\n\t', null, undefined, 0, 1, [], {}, Symbol('s')]

  for (const value of accepted) {
    test(`accepts ${JSON.stringify(String(value))}`, () => {
      assert.equal(isNonBlankString(value), true)
    })
  }
  for (const value of rejected) {
    test(`rejects ${String(typeof value === 'symbol' ? 'Symbol' : JSON.stringify(value))}`, () => {
      assert.equal(isNonBlankString(value), false)
    })
  }
})

describe('isPositiveInteger', () => {
  const accepted = [1, 2, 10, 1000]
  const rejected = [0, -1, 1.5, NaN, Infinity, -Infinity, '1', null, undefined, true]

  for (const value of accepted) {
    test(`accepts ${value}`, () => assert.equal(isPositiveInteger(value), true))
  }
  for (const value of rejected) {
    test(`rejects ${String(value)}`, () => assert.equal(isPositiveInteger(value), false))
  }
})

describe('VIOLATION codes', () => {
  test('every key maps to itself, so codes cannot drift from their names', () => {
    for (const [key, value] of Object.entries(VIOLATION)) {
      assert.equal(key, value)
    }
  })
})
