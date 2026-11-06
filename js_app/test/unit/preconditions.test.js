/**
 * Preconditions on the main-process API surface.
 *
 * All of these reject before any subprocess is spawned, so the file stays in
 * the fast suite: `requires` runs at the top of each function, ahead of the
 * execSync call.
 */
import { test, describe } from 'node:test'
import assert from 'node:assert/strict'

import { create_problem, evaluate_problem } from '../../src/main/problems.js'
import { PreconditionError } from '../../src/main/invariants.js'

const rejects = (fn, match) =>
  assert.throws(fn, err => err instanceof PreconditionError && (!match || match.test(err.message)))

describe('create_problem preconditions', () => {
  for (const [label, type] of [
    ['empty string', ''],
    ['blank string', '   '],
    ['null', null],
    ['undefined', undefined],
    ['a number', 7],
    ['an object', {}],
    ['an array', []],
  ]) {
    test(`rejects a type that is ${label}`, () => {
      rejects(() => create_problem(type, 1), /type must be a non-blank string/)
    })
  }

  for (const [label, round] of [
    ['zero', 0],
    ['negative', -1],
    ['fractional', 1.5],
    ['NaN', NaN],
    ['Infinity', Infinity],
    ['null', null],
    ['an object', {}],
  ]) {
    test(`rejects a round that is ${label}`, () => {
      rejects(() => create_problem('WordList', round), /round must be a positive integer/)
    })
  }

  test('accepts a numeric string round, matching what the bridge coerces', () => {
    // Number('3') === 3, so the precondition passes; the failure that follows
    // (if any) comes from the subprocess, not from validation.
    assert.doesNotThrow(() => {
      try {
        create_problem('WordList', '3')
      } catch (e) {
        if (e instanceof PreconditionError) throw e
      }
    })
  })

  test('validates arguments before spawning anything', () => {
    const started = Date.now()
    rejects(() => create_problem('', 1))
    // A python spawn costs ~400ms; rejecting must be effectively instant.
    assert.ok(Date.now() - started < 100, 'precondition should short-circuit before execSync')
  })
})

describe('evaluate_problem preconditions', () => {
  test('rejects a blank type', () => {
    rejects(() => evaluate_problem('', 'a', 'b'), /type must be a non-blank string/)
  })

  for (const [label, solution] of [
    ['null', null],
    ['undefined', undefined],
    ['a number', 1],
    ['an object', {}],
  ]) {
    test(`rejects a solution that is ${label}`, () => {
      rejects(() => evaluate_problem('WordList', solution, 'b'), /solution must be a string/)
    })
  }

  for (const [label, input] of [
    ['null', null],
    ['undefined', undefined],
    ['a number', 1],
  ]) {
    test(`rejects a user_input that is ${label}`, () => {
      rejects(() => evaluate_problem('WordList', 'a', input), /user_input must be a string/)
    })
  }

  test('accepts empty strings — an empty answer is a legitimate submission', () => {
    // Only asserting the precondition layer lets it through; the subprocess
    // result is covered by the integration suite.
    assert.doesNotThrow(() => {
      try {
        evaluate_problem('WordList', 'answer', '')
      } catch (e) {
        if (e instanceof PreconditionError) throw e
      }
    })
  })

  test('validates arguments before spawning anything', () => {
    const started = Date.now()
    rejects(() => evaluate_problem('WordList', null, 'b'))
    assert.ok(Date.now() - started < 100, 'precondition should short-circuit before execSync')
  })
})

describe('precondition errors carry details for diagnosis', () => {
  test('create_problem reports the offending type', () => {
    try {
      create_problem('', 1)
      assert.fail('should have thrown')
    } catch (err) {
      assert.deepEqual(err.details, { type: '' })
    }
  })

  test('create_problem reports the offending round', () => {
    try {
      create_problem('WordList', 0)
      assert.fail('should have thrown')
    } catch (err) {
      assert.deepEqual(err.details, { round: 0 })
    }
  })
})
