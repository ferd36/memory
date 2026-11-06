/**
 * Round handling and the one problem type that is stateful across rounds.
 *
 * TwoBackRecall is where the `is_scored` flag matters: its first two rounds are
 * warm-ups carrying the placeholder solution "none". The bridge used to drop
 * the flag, so the renderer graded those rounds and reported them incorrect.
 *
 * These tests share /tmp/memory_twoback.json with the rest of the suite, so the
 * integration scripts run with --test-concurrency=1.
 */
import { test, describe, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'fs'

import { create_problem } from '../../src/main/problems.js'
import {
  pythonUnavailable,
  collectViolations,
  resetTwoBackHistory,
  TWO_BACK_HISTORY_FILE,
} from '../helpers/index.js'

const skip = pythonUnavailable()

describe('TwoBackRecall warm-up rounds', { skip }, () => {
  beforeEach(() => resetTwoBackHistory())

  test('round 1 is a warm-up with the placeholder solution', () => {
    const p = create_problem('TwoBackRecall', 1)
    assert.match(p.prompt, /Warmup round/)
    assert.equal(p.solution, 'none')
  })

  test('round 2 is still a warm-up', () => {
    create_problem('TwoBackRecall', 1)
    const p = create_problem('TwoBackRecall', 2)
    assert.match(p.prompt, /Warmup round/)
    assert.equal(p.solution, 'none')
  })

  test('round 3 asks the real question', () => {
    create_problem('TwoBackRecall', 1)
    create_problem('TwoBackRecall', 2)
    const p = create_problem('TwoBackRecall', 3)
    assert.match(p.prompt, /2 rounds ago/)
    assert.notEqual(p.solution, 'none')
  })

  test('the round 3 solution is the item shown in round 1', () => {
    const first = create_problem('TwoBackRecall', 1)
    create_problem('TwoBackRecall', 2)
    const third = create_problem('TwoBackRecall', 3)
    assert.equal(third.solution, first.memorize)
  })

  test('the round 4 solution is the item shown in round 2', () => {
    create_problem('TwoBackRecall', 1)
    const second = create_problem('TwoBackRecall', 2)
    create_problem('TwoBackRecall', 3)
    const fourth = create_problem('TwoBackRecall', 4)
    assert.equal(fourth.solution, second.memorize)
  })

  test('warm-up rounds are marked unscored and real rounds are not', () => {
    const warmUpOne = create_problem('TwoBackRecall', 1)
    const warmUpTwo = create_problem('TwoBackRecall', 2)
    const real = create_problem('TwoBackRecall', 3)

    assert.equal(warmUpOne.is_scored, false)
    assert.equal(warmUpTwo.is_scored, false)
    assert.equal(real.is_scored, true)
  })

  test('the renderer condition for the warm-up branch now holds', () => {
    // App.jsx renders "Warmup round complete!" when `is_scored !== false`
    // is false. Before the fix the field was absent, so warm-ups were graded
    // against the placeholder solution "none" and reported incorrect.
    const warmUp = create_problem('TwoBackRecall', 1)
    assert.equal(warmUp.is_scored !== false, false, 'renderer must treat it as unscored')
    assert.equal(warmUp.solution, 'none')
  })

  test('every other problem type is scored', () => {
    for (const type of ['WordList', 'Number', 'MatrixMemory']) {
      assert.equal(create_problem(type, 1).is_scored, true)
    }
  })

  test('records no violations on any round', () => {
    for (const round of [1, 2, 3]) {
      const { violations } = collectViolations(() => create_problem('TwoBackRecall', round))
      assert.deepEqual(violations, [])
    }
  })
})

describe('TwoBackRecall history file', { skip }, () => {
  beforeEach(() => resetTwoBackHistory())

  test('round 1 starts a fresh history regardless of what was there', () => {
    fs.writeFileSync(TWO_BACK_HISTORY_FILE, JSON.stringify(['stale1', 'stale2', 'stale3']))
    const p = create_problem('TwoBackRecall', 1)
    assert.equal(p.solution, 'none', 'round 1 must ignore leftover history')
  })

  test('the file is written after each round', () => {
    create_problem('TwoBackRecall', 1)
    assert.ok(fs.existsSync(TWO_BACK_HISTORY_FILE))
    assert.deepEqual(JSON.parse(fs.readFileSync(TWO_BACK_HISTORY_FILE, 'utf8')).length, 1)
  })

  test('BUG: history lives in one shared temp file, not per-session state', () => {
    // Safe expectation once fixed: state is scoped to a game session, so two
    // concurrent runs cannot interfere.
    assert.match(TWO_BACK_HISTORY_FILE, /memory_twoback\.json$/)
    create_problem('TwoBackRecall', 1)
    create_problem('TwoBackRecall', 2)
    const history = JSON.parse(fs.readFileSync(TWO_BACK_HISTORY_FILE, 'utf8'))
    assert.equal(history.length, 2, 'any other process sharing this file corrupts the game')
  })

  test('a corrupt history file degrades to an empty history rather than crashing', () => {
    fs.writeFileSync(TWO_BACK_HISTORY_FILE, 'not json at all')
    const p = create_problem('TwoBackRecall', 5)
    assert.equal(p.solution, 'none', 'falls back to warm-up behaviour')
  })
})

describe('the round argument for every other type', { skip }, () => {
  test('is accepted at any round without changing the exposure time', () => {
    // Only TwoBackRecall reads round_num; the rest swallow it in **kwargs, so
    // difficulty does not scale over the 10 rounds of a game.
    for (const type of ['WordList', 'Number', 'RandomLetters', 'MatrixMemory']) {
      const early = create_problem(type, 1)
      const late = create_problem(type, 10)
      assert.equal(early.exposure_ms, late.exposure_ms, `${type} exposure changed with round`)
    }
  })

  test('is accepted well past MAX_ROUNDS', () => {
    const p = create_problem('WordList', 999)
    assert.ok(p.memorize.length > 0)
  })
})
