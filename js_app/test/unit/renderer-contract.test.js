/**
 * The contract between the bridge payload and what App.jsx actually reads.
 *
 * The renderer is not mounted here — there is no DOM library in the project —
 * so these tests read App.jsx as source and assert on the shape of its
 * dependency on the payload. That is enough to catch the two ways this contract
 * breaks: the renderer reading a field nobody sends, and the bridge sending a
 * field nobody reads.
 */
import { test, describe } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'fs'
import path from 'path'

import { PROJECT_ROOT } from '../helpers/index.js'
import { CREATE_PAYLOAD_SHAPE } from '../../src/main/problems.js'

const APP_JSX = path.join(PROJECT_ROOT, 'src/renderer/App.jsx')
const source = fs.readFileSync(APP_JSX, 'utf8')

const readsOf = (object, text = source) =>
  [...new Set([...text.matchAll(new RegExp(`\\b${object}\\.([a-zA-Z_][\\w]*)`, 'g'))].map(m => m[1]))].sort()

/** Fields create_problem attaches, including the one added on the JS side. */
const PAYLOAD_FIELDS = [...Object.keys(CREATE_PAYLOAD_SHAPE), 'type_id'].sort()

describe('every field the renderer reads is supplied by the payload', () => {
  test('the read set is what we expect', () => {
    assert.deepEqual(readsOf('problem'), [
      'exposure_ms',
      'input_type',
      'is_scored',
      'memorize',
      'prompt',
      'solution',
      'state',
      'type_id',
    ])
  })

  test('nothing is read that the payload does not send', () => {
    // Regression guard for the dropped is_scored field: the renderer branched
    // on it for warm-up rounds while the bridge never sent it, so warm-ups were
    // graded against the placeholder solution "none".
    const missing = readsOf('problem').filter(f => !PAYLOAD_FIELDS.includes(f))
    assert.deepEqual(missing, [])
  })

  test('is_scored specifically is part of the payload shape', () => {
    assert.ok('is_scored' in CREATE_PAYLOAD_SHAPE)
    assert.equal(CREATE_PAYLOAD_SHAPE.is_scored(true), true)
    assert.equal(CREATE_PAYLOAD_SHAPE.is_scored(undefined), false)
  })

  test('state is part of the payload shape and is forwarded to evaluation', () => {
    assert.ok('state' in CREATE_PAYLOAD_SHAPE)
    assert.match(source, /window\.api\.evaluateProblem\(\s*\n?\s*problem\.type_id, problem\.solution, ans, problem\.state\)/)
  })

  test('display_name is sent but unused — the renderer shows a static heading', () => {
    assert.ok(PAYLOAD_FIELDS.includes('display_name'))
    assert.equal(readsOf('problem').includes('display_name'), false)
  })
})

describe('warm-up rounds', () => {
  test('the renderer still treats a missing is_scored as scored', () => {
    assert.match(source, /problem\.is_scored\s*!==\s*false/)
  })

  test('the warm-up branch exists and is now reachable', () => {
    assert.match(source, /Warmup round complete!/)
  })
})

describe('the recall input', () => {
  test('renders a textarea for multiline problems', () => {
    // Regression guard: NameList's solution is newline-joined, so a single-line
    // <input> made the game unwinnable.
    assert.match(source, /const isMultiline = problem\.input_type === 'multiline'/)
    assert.match(source, /<textarea/)
    assert.match(source, /\{isMultiline \? \(/)
  })

  test('still renders a text input for single-line problems', () => {
    assert.match(source, /<input\s*\n?\s*type="text"/)
  })

  test('the textarea is tall enough for the expected answer', () => {
    assert.match(source, /rows=\{Math\.max\(3, problem\.solution\.split\('\\n'\)\.length\)\}/)
  })

  test('Enter inserts a newline and Cmd/Ctrl+Enter submits', () => {
    assert.match(source, /e\.metaKey \|\| e\.ctrlKey/)
    assert.match(source, /onKeyDown=/)
  })
})

describe('what the renderer reads off an evaluation', () => {
  test('reads correct and fallback', () => {
    assert.deepEqual(readsOf('evaluation'), ['correct', 'fallback'])
  })

  test('BUG: the partial score is computed by the bridge and discarded', () => {
    // Safe expectation once fixed: 'score' appears in the reads.
    assert.equal(readsOf('evaluation').includes('score'), false)
  })

  test('the renderer fallback returns the same shape as the bridge', () => {
    // Both paths must carry score, correct and fallback, so a consumer never
    // has to special-case the fallback.
    assert.match(source, /\{ score: isCorrect \? 1 : 0, correct: isCorrect, fallback: true \}/)
  })

  test('a fallback verdict is shown with a warning', () => {
    // Regression guard: an exact-match fallback was shown as a real grade.
    const feedback = source.slice(source.indexOf('function FeedbackScreen'))
    assert.match(feedback, /evaluation && evaluation\.fallback && \(/)
    assert.match(feedback, /exact match only/)
  })
})

describe('problem types the renderer special-cases', () => {
  const literals = [...source.matchAll(/type_id === '([A-Za-z0-9_]+)'/g)].map(m => m[1])

  test('are the three we know about', () => {
    assert.deepEqual(literals.sort(), ['ColorSequence', 'MatrixMemory', 'PlayingCardSequence'])
  })

  test('MatrixMemory rendering assumes a space-separated, newline-delimited grid', () => {
    assert.match(source, /problem\.memorize\.split\('\\n'\)\.map\(row => row\.split\(' '\)\)/)
  })

  test('MatrixMemory column headers are derived from the first row width', () => {
    assert.match(source, /const cols = rows\[0\]\.length/)
    assert.match(source, /String\.fromCharCode\(65 \+ i\)/)
  })
})

describe('round handling', () => {
  test('MAX_ROUNDS is 10', () => {
    assert.match(source, /const MAX_ROUNDS = 10/)
  })

  test('the round number is passed to createProblem', () => {
    assert.match(source, /window\.api\.createProblem\(type,\s*r\)/)
  })

  test('BUG: nothing accumulates a score across rounds', () => {
    // Safe expectation once fixed: some running total exists.
    assert.equal(/setScore|totalScore|correctCount/.test(source), false)
  })

  test('BUG: the recall timer is displayed but never submitted', () => {
    assert.match(source, /Time: \{timeSpent\}s/)
    assert.equal(/timeSpent[^}]*onSubmit|onSubmit\([^)]*timeSpent/.test(source), false)
  })
})

describe('error handling in the renderer', () => {
  test('BUG: a failing createProblem rejects with nothing to catch it', () => {
    // Safe expectation once fixed: loadRound has a try/catch or an error state.
    assert.match(source, /const loadRound = async \(type, r[^)]*\) => \{/)
    const loadRound = source.slice(source.indexOf('const loadRound'), source.indexOf('const handleNext'))
    assert.equal(/try\s*\{/.test(loadRound), false)
  })

  test('BUG: there is no error state or error boundary', () => {
    assert.equal(/componentDidCatch|ErrorBoundary/.test(source), false)
  })
})

describe('results that arrive after the player quits', () => {
  // Regression guard: Quit during a pending evaluation set problem to null,
  // then the evaluation resolved, set the phase to 'feedback', and
  // FeedbackScreen threw on problem.is_scored. A pending createProblem could
  // likewise reopen a game after Quit.
  const between = (from, to) => {
    const start = source.indexOf(from)
    assert.notEqual(start, -1, `missing: ${from}`)
    const end = source.indexOf(to, start)
    assert.notEqual(end, -1, `missing after ${from}: ${to}`)
    return source.slice(start, end)
  }
  const STALE_CHECK = /if \(game !== gameRef\.current\) return/

  test('quitting and starting a game each begin a new game token', () => {
    assert.match(between('const handleQuit', '\n  }\n'), /gameRef\.current \+= 1/)
    assert.match(between('const startProblemType', '\n  }\n'), /const game = \+\+gameRef\.current/)
  })

  test('a stale createProblem result is dropped before it changes state', () => {
    const afterCreate = between('await window.api.createProblem', 'setProblem(p)')
    assert.match(afterCreate, STALE_CHECK)
  })

  test('a stale evaluation is dropped before it changes state', () => {
    const onSubmit = between('onSubmit={async (ans) => {', "setPhase('feedback')")
    assert.match(onSubmit, /const game = gameRef\.current/)
    const afterEvaluate = onSubmit.slice(onSubmit.indexOf('await window.api.evaluateProblem'))
    assert.match(afterEvaluate, STALE_CHECK)
    assert.ok(afterEvaluate.search(STALE_CHECK) < afterEvaluate.indexOf('setEvaluation('),
      'the stale check must come before setEvaluation')
  })
})

describe('a second press of Next while a round loads', () => {
  // Regression guard: the button stays on screen during the bridge call. A double
  // click played rounds 1, 3, 5, 7 and 9, and a TwoBackRecall answer could be an
  // item that the player never saw.
  const section = (from, to) => source.slice(source.indexOf(from), source.indexOf(to))
  const handleNext = section('const handleNext', 'const handleQuit')
  const loadRound = section('const loadRound', 'const handleNext')

  test('is ignored', () => {
    assert.match(handleNext, /if \(advancingRef\.current\) return\n\s*advancingRef\.current = true/)
    assert.ok(handleNext.indexOf('advancingRef.current = true') < handleNext.indexOf('await loadRound'),
      'the guard must be set before the bridge call')
  })

  test('the guard is released when the load fails', () => {
    assert.match(handleNext, /finally \{\s*advancingRef\.current = false\s*\}/)
  })

  test('the round number changes only together with the new problem', () => {
    assert.equal(handleNext.includes('setRound'), false)
    const afterCreate = loadRound.slice(loadRound.indexOf('await window.api.createProblem'))
    assert.ok(afterCreate.search(/if \(game !== gameRef\.current\) return/) < afterCreate.indexOf('setRound(r)'),
      'a stale result must not change the round')
  })
})

describe('the feedback screen', () => {
  test('keeps the line breaks of a multi-line answer', () => {
    // Regression guard: the browser showed newlines as spaces, so "Expected" and
    // "You typed" could look identical beside "Incorrect".
    const feedback = source.slice(source.indexOf('function FeedbackScreen'))
    assert.match(feedback, /Expected: <strong style=\{\{ ?whiteSpace: 'pre-wrap' ?\}\}>/)
    assert.match(feedback, /You typed: <strong style=\{\{ ?whiteSpace: 'pre-wrap' ?\}\}>/)
  })
})

describe('the preload bridge signature matches what the renderer calls', () => {
  const preload = fs.readFileSync(path.join(PROJECT_ROOT, 'src/main/preload.js'), 'utf8')

  test('evaluateProblem forwards the state argument', () => {
    assert.match(preload, /evaluateProblem: \(type, solution, userInput, state\)/)
    assert.match(preload, /invoke\('evaluate-problem', type, solution, userInput, state\)/)
  })

  test('every api method the renderer uses is exposed', () => {
    for (const method of readsOf('window\\.api')) {
      assert.match(preload, new RegExp(`\\b${method}:`), `preload should expose ${method}`)
    }
  })
})
