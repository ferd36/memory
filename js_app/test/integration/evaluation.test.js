/**
 * evaluate_problem end to end.
 *
 * The "answer text reaches the shell" section is the regression net for the
 * command-injection fix: evaluate_problem used to interpolate the user's answer
 * into a /bin/sh command string, escaping only `"`. It now passes an argv array
 * to execFileSync, so no shell is involved and every byte the user typed is
 * delivered to python unchanged.
 */
import { test, describe, after } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'fs'
import os from 'os'
import path from 'path'

import { evaluate_problem } from '../../src/main/problems.js'
import { pythonUnavailable, collectViolations } from '../helpers/index.js'

const skip = pythonUnavailable()
const markers = []

function markerPath(label) {
  const p = path.join(os.tmpdir(), `memory-trainer-test-${label}-${process.pid}-${Math.random().toString(36).slice(2)}`)
  markers.push(p)
  return p
}

after(() => {
  for (const p of markers) {
    try { fs.unlinkSync(p) } catch { /* already gone */ }
  }
})

describe('normal evaluation', { skip }, () => {
  test('returns score and correct for an exact match', () => {
    const r = evaluate_problem('WordList', 'apple', 'apple')
    assert.deepEqual(r, { score: 1, correct: true, fallback: false })
  })

  test('returns a fractional score for a near miss', () => {
    const r = evaluate_problem('WordList', 'apple', 'appel')
    assert.ok(r.score > 0 && r.score < 1)
    assert.equal(r.correct, false)
  })

  test('records no violations for ordinary text', () => {
    const { violations } = collectViolations(() => evaluate_problem('WordList', 'apple', 'apple'))
    assert.deepEqual(violations, [])
  })

  test('handles unicode answers, which several games produce', () => {
    const r = evaluate_problem('PlayingCardSequence', '♥10', '♥10')
    assert.equal(r.correct, true)
  })
})

describe('symbol solutions', { skip }, () => {
  // unidecode maps every emoji to '', so an empty answer or any other emoji
  // was an exact match for an emoji solution.
  test('an empty answer does not match an emoji', () => {
    assert.equal(evaluate_problem('SpatialGrid', '🍎', '').correct, false)
  })

  test('a different emoji does not match', () => {
    assert.equal(evaluate_problem('SpatialGrid', '🍎', '🚗').correct, false)
  })

  test('the emoji or its name matches', () => {
    assert.equal(evaluate_problem('SpatialGrid', '🍎', '🍎').correct, true)
    assert.equal(evaluate_problem('SpatialGrid', '🍎', 'apple').correct, true)
  })

  test('a card can be typed with a suit letter', () => {
    assert.equal(evaluate_problem('PlayingCardSequence', '♥10', '10H').correct, true)
    assert.equal(evaluate_problem('PlayingCardSequence', '♥10', '10S').correct, false)
  })

  test('a METAR number is accepted as the report shows it', () => {
    assert.equal(evaluate_problem('Metar', '5', '05').correct, true)
    assert.equal(evaluate_problem('Metar', '-3', 'M03').correct, true)
  })
})

describe('the answer text never reaches a shell', { skip }, () => {
  test('command substitution is scored as literal text, not executed', () => {
    const marker = markerPath('cmdsub')
    const answer = `$(touch ${marker})`

    const r = evaluate_problem('WordList', answer, answer)

    assert.equal(fs.existsSync(marker), false, 'the shell executed the answer text')
    assert.equal(r.correct, true, 'the literal text should compare equal to itself')
  })

  test('backtick substitution is scored as literal text, not executed', () => {
    const marker = markerPath('backtick')
    const answer = `\`touch ${marker}\``

    const r = evaluate_problem('WordList', answer, answer)

    assert.equal(fs.existsSync(marker), false)
    assert.equal(r.correct, true)
  })

  test('a command separator does not start a second command', () => {
    const marker = markerPath('separator')
    evaluate_problem('WordList', 'apple', `x; touch ${marker}`)
    assert.equal(fs.existsSync(marker), false)
  })

  test('a variable reference is compared literally, not expanded', () => {
    // Previously '$HOME' and the expansion of $HOME compared equal.
    const r = evaluate_problem('WordList', '$HOME', process.env.HOME)
    assert.equal(r.correct, false, '$HOME must not be expanded before comparison')

    const literal = evaluate_problem('WordList', '$HOME', '$HOME')
    assert.equal(literal.correct, true)
  })

  for (const [label, value] of [
    ['a dollar sign', 'costs $5'],
    ['a backtick', 'use `this`'],
    ['a backslash', 'C:\\path'],
    ['a doubled backslash', 'a\\\\b'],
    ['a backslash before a quote', 'a\\"b'],
    ['a trailing backslash', 'a\\'],
    ['a double quote', 'say "hi"'],
    ['a newline', 'a\nb'],
    ['a semicolon', 'semi;colon'],
    ['a pipe', 'pipe|bar'],
    ['an ampersand', 'amp&and'],
    ['a glob', 'glob*star'],
    ['a redirect', 'a > b'],
    ['a null-ish sequence', '$IFS$()'],
  ]) {
    test(`${label} survives the round trip intact`, () => {
      // If the argument were mangled in transit the two sides would differ and
      // the score would drop below 1.
      const { value: r, violations } = collectViolations(() =>
        evaluate_problem('WordList', value, value))
      assert.equal(r.correct, true, `${JSON.stringify(value)} was altered in transit`)
      assert.equal(r.score, 1)
      assert.deepEqual(violations, [])
    })
  }

  test('a distinct answer is still scored as distinct', () => {
    // Guards against the round trip "succeeding" by collapsing everything.
    const r = evaluate_problem('WordList', '$(echo a)', '$(echo b)')
    assert.equal(r.correct, false)
  })
})

describe('the bridge result is used, not the fallback', { skip }, () => {
  test('an escaped quote no longer breaks the call', () => {
    // This used to produce a shell syntax error, and evaluate_problem silently
    // fell back to exact matching with no score field.
    const r = evaluate_problem('WordList', 'a\\"b', 'a\\"c')
    assert.deepEqual(Object.keys(r).sort(), ['correct', 'fallback', 'score'])
    assert.equal(r.fallback, false)
    assert.ok(r.score > 0 && r.score < 1, 'fuzzy scoring should still apply')
  })

  test('both the success and fallback paths return the same shape', () => {
    const ok = evaluate_problem('WordList', 'apple', 'apple')
    // An unknown type is the remaining way to reach the fallback.
    const fallback = evaluate_problem('NoSuchProblem', 'apple', 'apple')

    assert.deepEqual(Object.keys(ok).sort(), ['correct', 'fallback', 'score'])
    assert.deepEqual(Object.keys(fallback).sort(), ['correct', 'fallback', 'score'])
    assert.equal(ok.fallback, false)
    assert.equal(fallback.fallback, true)
  })

  test('the fallback reports a score consistent with its verdict', () => {
    const match = evaluate_problem('NoSuchProblem', 'apple', 'apple')
    assert.deepEqual(match, { score: 1, correct: true, fallback: true })

    const miss = evaluate_problem('NoSuchProblem', 'apple', 'orange')
    assert.deepEqual(miss, { score: 0, correct: false, fallback: true })
  })
})

describe('problem state travels with the evaluation', { skip }, () => {
  test('Anagram accepts an alternative dictionary anagram', () => {
    const r = evaluate_problem('Anagram', 'care', 'race', { _dict_index: 1 })
    assert.equal(r.correct, true)
  })

  test('Anagram rejects a scramble that is not a real word', () => {
    const r = evaluate_problem('Anagram', 'care', 'ecar', { _dict_index: 1 })
    assert.equal(r.correct, false)
  })

  test('the exact solution is accepted with or without state', () => {
    assert.equal(evaluate_problem('Anagram', 'care', 'care', { _dict_index: 1 }).correct, true)
    assert.equal(evaluate_problem('Anagram', 'care', 'care').correct, true)
  })

  test('state defaults to empty and is optional', () => {
    assert.equal(evaluate_problem('WordList', 'apple', 'apple').correct, true)
  })

  test('rejects a state that is not a plain object', () => {
    for (const bad of [null, [], 'x', 1]) {
      assert.throws(() => evaluate_problem('WordList', 'a', 'a', bad), /state must be a plain object/)
    }
  })
})

describe('alternative readings travel with the evaluation', { skip }, () => {
  test('JapaneseWord accepts each reading in its state', () => {
    const state = { _readings: 'ie|uchi' }
    assert.equal(evaluate_problem('JapaneseWord', 'ie', 'uchi', state).correct, true)
    assert.equal(evaluate_problem('JapaneseWord', 'ie', 'ko', state).correct, false)
  })
})

describe('evaluation is consistent with what create produced', { skip }, () => {
  test('the exact solution always scores 1', () => {
    for (const type of ['WordList', 'Number', 'RandomLetters', 'NumberList', 'WordPairs']) {
      const r = evaluate_problem(type, 'sample-answer', 'sample-answer')
      assert.equal(r.correct, true, `${type} should accept its own solution`)
    }
  })

  test('a multi-line solution can be matched exactly', () => {
    // NameList declares input_type 'multiline' and the recall screen now
    // renders a textarea, so this is reachable from the UI.
    const solution = 'Alice\nBob\nCarol'
    assert.equal(evaluate_problem('NameList', solution, solution).correct, true)
  })

  test('a multi-line solution accepts any whitespace between its items', () => {
    // The terminal trainer cannot enter a newline, and the feedback screen made
    // the two forms look identical beside "Incorrect".
    const solution = 'Alice\nBob\nCarol'
    assert.equal(evaluate_problem('NameList', solution, 'Alice Bob Carol').correct, true)
    assert.equal(evaluate_problem('NameList', solution, 'Carol Bob Alice').correct, false)
  })
})
