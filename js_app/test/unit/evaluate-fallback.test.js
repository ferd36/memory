/**
 * When the bridge cannot run, evaluate_problem falls back to an exact match.
 * The result must say so: the renderer showed the fallback verdict as a real
 * grade, with no partial credit and no Anagram alternatives, and no warning.
 *
 * MEMORY_TRAINER_PYTHON is read when problems.js loads, so it is set before a
 * dynamic import. node --test runs each file in its own process, so this does
 * not leak into other files. The bogus interpreter fails at spawn, so no python
 * runs and the file stays in the fast suite.
 */
import { test, describe, before } from 'node:test'
import assert from 'node:assert/strict'

let evaluate_problem

before(async () => {
  process.env.MEMORY_TRAINER_PYTHON = '/nonexistent/python-for-fallback-test'
  ;({ evaluate_problem } = await import('../../src/main/problems.js'))
})

describe('evaluate_problem when the bridge cannot run', () => {
  test('marks the result as a fallback', () => {
    const r = evaluate_problem('WordList', 'apple', 'apple')
    assert.deepEqual(r, { score: 1, correct: true, fallback: true })
  })

  test('still reports a miss as a miss', () => {
    const r = evaluate_problem('WordList', 'apple', 'appel')
    assert.deepEqual(r, { score: 0, correct: false, fallback: true })
  })
})
