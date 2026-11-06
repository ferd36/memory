/**
 * Exhaustive generation sweep: every problem type must produce a payload the
 * renderer can actually display.
 *
 * This supersedes test_all_games.js, which only checked field presence. Here
 * each type gets its own subtest, the payload is validated against the declared
 * shape, and the soft invariants raised along the way are asserted rather than
 * ignored — so the known-bad types are pinned by name.
 */
import { test, describe, before } from 'node:test'
import assert from 'node:assert/strict'

import { create_problem, get_problem_types } from '../../src/main/problems.js'
import {
  pythonUnavailable,
  collectViolations,
  uniqueCodes,
  resetTwoBackHistory,
  NETWORK_DEPENDENT_TYPES,
} from '../helpers/index.js'

const skip = pythonUnavailable()
const types = skip ? [] : get_problem_types()
const sweepable = types.filter(t => !NETWORK_DEPENDENT_TYPES.has(t.id))

/**
 * No type should raise a soft violation. Any entry here is an unfixed defect;
 * the map is kept so a new one has to be declared deliberately.
 */
const KNOWN_VIOLATIONS = {}

describe('the type list', { skip }, () => {
  test('is non-empty', () => {
    assert.ok(types.length > 0)
  })

  test('covers every game the sweep will exercise', () => {
    assert.equal(sweepable.length, types.length - NETWORK_DEPENDENT_TYPES.size)
  })

  test('includes the three types the renderer special-cases', () => {
    const ids = types.map(t => t.id)
    for (const id of ['ColorSequence', 'PlayingCardSequence', 'MatrixMemory']) {
      assert.ok(ids.includes(id), `${id} is special-cased in App.jsx but not offered`)
    }
  })
})

describe('every problem type generates a usable payload', { skip, timeout: 180000 }, () => {
  before(() => resetTwoBackHistory())

  for (const t of sweepable) {
    test(`${t.id} (${t.name})`, () => {
      const { value: p, violations, error } = collectViolations(() => create_problem(t.id, 1))

      assert.equal(error, null, `create_problem threw: ${error?.message}`)
      assert.equal(typeof p, 'object')

      // Shape the renderer depends on.
      assert.equal(p.type_id, t.id, 'type_id must round-trip for evaluation')
      assert.equal(typeof p.display_name, 'string')
      assert.ok(p.memorize.trim().length > 0, 'memorize must not be blank')
      assert.ok(p.prompt.trim().length > 0, 'prompt must not be blank')
      assert.equal(typeof p.solution, 'string')
      assert.ok(Number.isInteger(p.exposure_ms) && p.exposure_ms > 0)
      assert.ok(['single line', 'multiline', 'matrix'].includes(p.input_type))

      assert.equal(typeof p.is_scored, 'boolean')
      assert.equal(typeof p.state, 'object')
      assert.ok(p.state !== null && !Array.isArray(p.state))

      // A multi-line solution must declare the multiline input that can enter it.
      if (p.solution.includes('\n')) {
        assert.equal(p.input_type, 'multiline',
          `${t.id} has a multi-line solution but asks for a ${p.input_type} input`)
      }

      const codes = uniqueCodes(violations)
      const expected = (KNOWN_VIOLATIONS[t.id] ?? []).sort()
      assert.deepEqual(codes, expected, `unexpected violations for ${t.id}`)
    })
  }
})

describe('exposure time is sane for a memory drill', { skip, timeout: 120000 }, () => {
  test('every type exposes between 0.5s and 30s', () => {
    for (const t of sweepable) {
      const p = create_problem(t.id, 1)
      assert.ok(p.exposure_ms >= 500, `${t.id} exposes for only ${p.exposure_ms}ms`)
      assert.ok(p.exposure_ms <= 30000, `${t.id} exposes for ${p.exposure_ms}ms`)
    }
  })
})

describe('renderer parsing assumptions hold against real payloads', { skip }, () => {
  test('MatrixMemory memorize is a newline-delimited, space-separated square grid', () => {
    const p = create_problem('MatrixMemory', 1)
    const rows = p.memorize.split('\n').map(row => row.split(' '))
    assert.ok(rows.length >= 2, 'needs at least two rows to be a grid')
    for (const row of rows) {
      assert.equal(row.length, rows[0].length, 'all rows must have the same width')
      for (const cell of row) assert.ok(['X', '.'].includes(cell))
    }
    assert.equal(rows.length, rows[0].length, 'renderer labels columns A.. assuming a square')
  })

  test('MatrixMemory solution is a column letter followed by a 1-based row number', () => {
    const p = create_problem('MatrixMemory', 1)
    assert.match(p.solution, /^[A-Z][0-9]+$/)

    const rows = p.memorize.split('\n').map(row => row.split(' '))
    const col = p.solution.charCodeAt(0) - 65
    const row = Number(p.solution.slice(1)) - 1
    assert.equal(rows[row][col], 'X', 'solution must point at the marked cell')
  })

  test('ColorSequence memorize is space-separated RGBY letters the renderer can colour', () => {
    const p = create_problem('ColorSequence', 1)
    const tokens = p.memorize.split(' ')
    assert.ok(tokens.length > 0)
    for (const token of tokens) assert.ok(['R', 'G', 'B', 'Y'].includes(token))
    // The renderer splits on '' and colours per character, so every non-space
    // character must be one it knows.
    for (const ch of p.memorize.replace(/ /g, '')) {
      assert.ok('RGBY'.includes(ch))
    }
  })

  test('PlayingCardSequence memorize uses the suit glyphs the renderer reddens', () => {
    const p = create_problem('PlayingCardSequence', 1)
    const suits = [...p.memorize].filter(ch => '♠♥♣♦'.includes(ch))
    assert.ok(suits.length > 0, 'expected suit glyphs in the memorize string')
    for (const ch of p.memorize.replace(/ /g, '')) {
      assert.ok(/[♠♥♣♦AJQK0-9]/.test(ch), `unexpected character ${ch}`)
    }
  })

  test('PlayingCardSequence cards are unique, as the prompt "card after X" requires', () => {
    const p = create_problem('PlayingCardSequence', 1)
    const cards = p.memorize.split(' ')
    assert.equal(cards.length, new Set(cards).size)
  })

  test('multiline memorize strings are what the renderer styles as .multiline', () => {
    const p = create_problem('NameList', 1)
    assert.ok(p.memorize.includes('\n'))
    assert.equal(p.input_type, 'multiline')
  })

  test('NameList is answerable: its solution needs the multiline input it asks for', () => {
    const p = create_problem('NameList', 1)
    assert.ok(p.solution.includes('\n'))
    assert.equal(p.input_type, 'multiline')
  })
})

describe('network-dependent types', () => {
  const netSkip = skip || (process.env.RUN_NETWORK_TESTS === '1'
    ? false
    : 'set RUN_NETWORK_TESTS=1 to exercise types that fetch remote data')

  test('SentenceCompletion generates a payload', { skip: netSkip, timeout: 60000 }, () => {
    const p = create_problem('SentenceCompletion', 1)
    assert.ok(p.memorize.trim().length > 0)
    assert.ok(p.solution.trim().length > 0)
  })
})
