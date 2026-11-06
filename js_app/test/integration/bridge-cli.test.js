/**
 * The bridge.py command-line contract.
 *
 * This is the real boundary between the Electron main process and the python
 * problem library, and it was previously untested. Every assertion here is
 * about the protocol: exit status, stdout being parseable JSON, and diagnostics
 * staying on stderr where they cannot corrupt the payload.
 */
import { test, describe } from 'node:test'
import assert from 'node:assert/strict'

import {
  runBridge,
  runPythonSnippet,
  pythonUnavailable,
  resetTwoBackHistory,
} from '../helpers/index.js'

const skip = pythonUnavailable()

describe('get_types', { skip }, () => {
  const result = skip ? null : runBridge(['get_types'])

  test('exits zero', () => {
    assert.equal(result.status, 0)
  })

  test('writes a JSON array to stdout', () => {
    const types = JSON.parse(result.stdout)
    assert.ok(Array.isArray(types))
    assert.ok(types.length > 0)
  })

  test('every entry has a non-blank id and name', () => {
    for (const t of JSON.parse(result.stdout)) {
      assert.equal(typeof t.id, 'string')
      assert.equal(typeof t.name, 'string')
      assert.ok(t.id.trim().length > 0)
      assert.ok(t.name.trim().length > 0)
    }
  })

  test('ids are unique', () => {
    const ids = JSON.parse(result.stdout).map(t => t.id)
    assert.equal(ids.length, new Set(ids).size)
  })

  test('ids are valid python identifiers, since they are resolved with getattr', () => {
    for (const t of JSON.parse(result.stdout)) {
      assert.match(t.id, /^[A-Za-z_][A-Za-z0-9_]*$/)
    }
  })

  test('entries are sorted by display name', () => {
    const names = JSON.parse(result.stdout).map(t => t.name)
    assert.deepEqual(names, [...names].sort())
  })

  test('Atc is displayed as ATC', () => {
    const atc = JSON.parse(result.stdout).find(t => t.id === 'Atc')
    assert.ok(atc, 'Atc type should be present')
    assert.equal(atc.name, 'ATC')
  })

  test('the base Problem class is not offered as a game', () => {
    const ids = JSON.parse(result.stdout).map(t => t.id)
    assert.equal(ids.includes('Problem'), false)
  })

  test('reports no invariant violations', () => {
    assert.deepEqual(result.invariants, [])
  })
})

describe('create', { skip }, () => {
  test('returns the payload fields the renderer needs', () => {
    const p = JSON.parse(runBridge(['create', 'WordList', '1']).stdout)
    assert.deepEqual(Object.keys(p).sort(), [
      'display_name', 'exposure_ms', 'input_type', 'is_scored',
      'memorize', 'prompt', 'solution', 'state',
    ])
  })

  test('exposure_ms is a positive integer', () => {
    const p = JSON.parse(runBridge(['create', 'Number', '1']).stdout)
    assert.ok(Number.isInteger(p.exposure_ms) && p.exposure_ms > 0)
  })

  test('defaults the round to 1 when it is omitted', () => {
    const result = runBridge(['create', 'WordList'])
    assert.equal(result.status, 0)
    assert.ok(JSON.parse(result.stdout).memorize.length > 0)
  })

  test('forwards is_scored=false for a TwoBackRecall warm-up round', () => {
    resetTwoBackHistory()
    const p = JSON.parse(runBridge(['create', 'TwoBackRecall', '1']).stdout)
    assert.equal(p.is_scored, false)
    assert.equal(p.solution, 'none')
  })

  test('defaults is_scored to true for a problem that does not set it', () => {
    const p = JSON.parse(runBridge(['create', 'WordList', '1']).stdout)
    assert.equal(p.is_scored, true)
  })

  test('reports no violations for a warm-up round any more', () => {
    resetTwoBackHistory()
    const result = runBridge(['create', 'TwoBackRecall', '1'])
    assert.deepEqual(result.invariants, [])
  })

  test('a game with a one-line answer asks for a one-line input', () => {
    // Regression guard: these games have a multi-line memorize text, and they got
    // a textarea where Enter added a newline to a one-word answer.
    for (const type of ['Appointments', 'FlightPlan', 'InventoryQuantities', 'NameAttributePairs',
      'Road', 'ShoppingList', 'WordNumberPairs', 'WordPairs']) {
      const result = runBridge(['create', type, '1'])
      const p = JSON.parse(result.stdout)
      assert.ok(!p.solution.includes('\n'), `${type} should have a one-line solution`)
      assert.equal(p.input_type, 'single line', type)
    }
  })

  test('NameList declares the multiline input its solution needs', () => {
    const result = runBridge(['create', 'NameList', '1'])
    const p = JSON.parse(result.stdout)
    assert.ok(p.solution.includes('\n'))
    assert.equal(p.input_type, 'multiline')
    assert.deepEqual(result.invariants, [])
  })

  test('carries the problem state that evaluation needs', () => {
    const p = JSON.parse(runBridge(['create', 'Anagram', '1']).stdout)
    assert.equal(typeof p.state, 'object')
    assert.equal(typeof p.state._dict_index, 'number')
  })

  test('sends an empty state for problems that attach nothing', () => {
    const p = JSON.parse(runBridge(['create', 'WordList', '1']).stdout)
    assert.deepEqual(p.state, {})
  })

  test('rejects an unknown type with a non-zero exit and no stdout', () => {
    const result = runBridge(['create', 'NoSuchProblem', '1'])
    assert.notEqual(result.status, 0)
    assert.equal(result.stdout, '')
    assert.match(result.stderr, /PreconditionError/)
    assert.match(result.stderr, /must name a Problem subclass/)
  })

  test('rejects a module attribute that is not a Problem subclass', () => {
    // `random` is importable from the problems module namespace.
    const result = runBridge(['create', 'random', '1'])
    assert.notEqual(result.status, 0)
    assert.match(result.stderr, /must name a Problem subclass/)
  })

  test('rejects a round below 1', () => {
    const result = runBridge(['create', 'WordList', '0'])
    assert.notEqual(result.status, 0)
    assert.match(result.stderr, /round_num must be >= 1/)
  })

  test('rejects a missing type argument', () => {
    const result = runBridge(['create'])
    assert.notEqual(result.status, 0)
    assert.match(result.stderr, /create requires a problem type/)
  })
})

describe('evaluate', { skip }, () => {
  test('scores an exact match as correct', () => {
    const r = JSON.parse(runBridge(['evaluate', 'WordList', 'apple', 'apple']).stdout)
    assert.deepEqual(r, { score: 1.0, correct: true })
  })

  test('is case- and whitespace-insensitive', () => {
    const r = JSON.parse(runBridge(['evaluate', 'WordList', 'apple', '  APPLE  ']).stdout)
    assert.equal(r.correct, true)
  })

  test('returns a partial score for a near miss', () => {
    const r = JSON.parse(runBridge(['evaluate', 'WordList', 'apple', 'appel']).stdout)
    assert.ok(r.score > 0 && r.score < 1)
    assert.equal(r.correct, false)
  })

  test('scores an empty answer as zero without crashing', () => {
    const r = JSON.parse(runBridge(['evaluate', 'WordList', 'apple', '']).stdout)
    assert.equal(r.score, 0)
    assert.equal(r.correct, false)
  })

  test('score is always within [0, 1]', () => {
    for (const answer of ['', 'x', 'apple', 'a much longer answer than the solution']) {
      const r = JSON.parse(runBridge(['evaluate', 'WordList', 'apple', answer]).stdout)
      assert.ok(r.score >= 0 && r.score <= 1, `score ${r.score} out of range for ${answer}`)
    }
  })

  test('correct is exactly score === 1', () => {
    for (const answer of ['apple', 'appl', 'zzzzz']) {
      const r = JSON.parse(runBridge(['evaluate', 'WordList', 'apple', answer]).stdout)
      assert.equal(r.correct, r.score >= 1.0)
    }
  })

  test('accepts yes/y and no/n for the n-back style games', () => {
    const yes = JSON.parse(runBridge(['evaluate', 'NBack', 'yes', 'y']).stdout)
    assert.equal(yes.correct, true)
    const no = JSON.parse(runBridge(['evaluate', 'Sternberg', 'no', 'n']).stdout)
    assert.equal(no.correct, true)
  })

  test('accepts a full colour name for a single-letter ColorSequence solution', () => {
    const r = JSON.parse(runBridge(['evaluate', 'ColorSequence', 'R', 'red']).stdout)
    assert.equal(r.correct, true)
  })

  test('accepts a reversed cell reference for MatrixMemory', () => {
    const r = JSON.parse(runBridge(['evaluate', 'MatrixMemory', 'B3', 'b3']).stdout)
    assert.equal(r.correct, true)
  })

  test('Anagram accepts an alternative valid anagram when state travels', () => {
    // create() attaches _dict_index; evaluation used to re-instantiate without
    // it, so _is_valid_anagram bailed out and only the exact word scored 1.0.
    const result = runBridge(
      ['evaluate', 'Anagram', 'care', 'race', JSON.stringify({ _dict_index: 1 })])
    assert.equal(JSON.parse(result.stdout).correct, true)
    assert.deepEqual(result.invariants, [])
  })

  test('Anagram still rejects a scramble that is not a real word', () => {
    const result = runBridge(
      ['evaluate', 'Anagram', 'care', 'ecar', JSON.stringify({ _dict_index: 1 })])
    assert.equal(JSON.parse(result.stdout).correct, false)
  })

  test('without the state the alternative anagram is not accepted', () => {
    // Pins why the state round-trip is needed at all.
    const result = runBridge(['evaluate', 'Anagram', 'care', 'race'])
    assert.equal(JSON.parse(result.stdout).correct, false)
  })

  test('state is optional and defaults to empty', () => {
    const result = runBridge(['evaluate', 'WordList', 'apple', 'apple'])
    assert.equal(result.status, 0)
    assert.equal(JSON.parse(result.stdout).correct, true)
  })

  test('rejects state that is not valid JSON', () => {
    const result = runBridge(['evaluate', 'WordList', 'a', 'a', 'not json'])
    assert.notEqual(result.status, 0)
    assert.match(result.stderr, /state must be valid JSON/)
  })

  test('rejects state that is not a JSON object', () => {
    const result = runBridge(['evaluate', 'WordList', 'a', 'a', '[1,2]'])
    assert.notEqual(result.status, 0)
    assert.match(result.stderr, /state must be a JSON object/)
  })

  test('refuses state that would overwrite a dataclass field', () => {
    const result = runBridge(
      ['evaluate', 'WordList', 'a', 'a', JSON.stringify({ solution: 'cheat' })])
    assert.notEqual(result.status, 0)
    assert.match(result.stderr, /state may not overwrite a dataclass field/)
  })

  test('rejects a missing argument', () => {
    const result = runBridge(['evaluate', 'WordList', 'only-solution'])
    assert.notEqual(result.status, 0)
    assert.match(result.stderr, /evaluate requires type, solution and user_input/)
  })

  test('a blank solution fails the Problem dataclass validation', () => {
    // Documents why evaluate_problem in problems.js has a fallback at all.
    const result = runBridge(['evaluate', 'WordList', '   ', 'x'])
    assert.notEqual(result.status, 0)
    assert.match(result.stderr, /solution must be a non-empty/)
  })
})

describe('command dispatch', { skip }, () => {
  test('rejects a missing command', () => {
    const result = runBridge([])
    assert.notEqual(result.status, 0)
    assert.match(result.stderr, /a command argument is required/)
  })

  test('rejects an unknown command', () => {
    const result = runBridge(['frobnicate'])
    assert.notEqual(result.status, 0)
    assert.match(result.stderr, /unknown command/)
  })
})

describe('stdout stays parseable', { skip }, () => {
  test('a successful call writes nothing to stderr', () => {
    const result = runBridge(['create', 'NameList', '1'])
    assert.equal(result.stderr, '')
    assert.doesNotThrow(() => JSON.parse(result.stdout))
  })

  test('stdout is a single JSON document with a trailing newline', () => {
    const { stdout } = runBridge(['create', 'Number', '1'])
    assert.equal(stdout.trimEnd().split('\n').length, 1)
  })

  test('invariant diagnostics go to stderr, never stdout', () => {
    // No problem type violates a soft invariant any more, so trigger one
    // directly to prove the diagnostics still land on the right stream.
    const result = runPythonSnippet(
      "print('{\"ok\": true}')\n"
      + "bridge.checks(False, 'PAYLOAD_SHAPE', 'synthetic', detail=1)")

    assert.equal(result.status, 0)
    assert.deepEqual(JSON.parse(result.stdout), { ok: true })
    assert.equal(result.stdout.includes('INVARIANT'), false)
    assert.deepEqual(result.invariants.map(v => v.code), ['PAYLOAD_SHAPE'])
  })

  test('the diagnostic line carries its structured details', () => {
    const result = runPythonSnippet(
      "bridge.checks(False, 'PAYLOAD_SHAPE', 'synthetic', detail='abc')")
    assert.match(result.stderr, /INVARIANT\[PAYLOAD_SHAPE\] synthetic \{"detail": "abc"\}/)
  })
})

describe('strict mode', { skip }, () => {
  test('turns a soft violation into a non-zero exit', () => {
    const result = runPythonSnippet(
      "bridge.checks(False, 'PAYLOAD_SHAPE', 'synthetic')", { strict: true })
    assert.notEqual(result.status, 0)
    assert.match(result.stderr, /InvariantViolation/)
    assert.match(result.stderr, /PAYLOAD_SHAPE/)
  })

  test('is off by default, so a violation only records', () => {
    const result = runPythonSnippet("bridge.checks(False, 'PAYLOAD_SHAPE', 'synthetic')")
    assert.equal(result.status, 0)
  })

  test('leaves a satisfied invariant alone in either mode', () => {
    for (const strict of [false, true]) {
      const result = runPythonSnippet(
        "bridge.checks(True, 'PAYLOAD_SHAPE', 'never seen')", { strict })
      assert.equal(result.status, 0)
      assert.equal(result.stderr, '')
    }
  })

  test('every real problem type stays clean under strict mode', () => {
    for (const type of ['WordList', 'NameList', 'Anagram', 'MatrixMemory', 'TwoBackRecall']) {
      resetTwoBackHistory()
      const result = runBridge(['create', type, '1'], { strict: true })
      assert.equal(result.status, 0, `${type} violated an invariant: ${result.stderr}`)
    }
  })
})
