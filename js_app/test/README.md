# js_app test suite

Runs on the Node built-in test runner (`node:test`, Node ≥ 18). No new
dependencies.

```
npm test              # unit — fast, no subprocesses (~1s)
npm run test:integration   # spawns python via bridge.py (~75s)
npm run test:all
npm run test:strict   # soft invariants become hard failures
npm run test:watch
```

## Layout

| Path | What it covers |
| --- | --- |
| `unit/invariants.test.js` | The invariant layer itself: `requires`, `checks`, strict mode, predicates. |
| `unit/no-shell.test.js` | Source-level guards that no shell is used to reach the bridge, and that no path is hardcoded. |
| `unit/csp.test.js` | The renderer fetches nothing from a remote origin, in source and in the build output. |
| `unit/preconditions.test.js` | Argument validation on `create_problem` / `evaluate_problem`, asserted to short-circuit before any spawn. |
| `unit/paths.test.js` | Build-layout invariants: where the preload and renderer entry resolve in the source tree vs `dist-electron/`. |
| `unit/renderer-contract.test.js` | What `App.jsx` reads off a payload vs what the bridge sends. Reads the JSX as source — there is no DOM library in the project. |
| `unit/evaluate-fallback.test.js` | `evaluate_problem` marks an exact-match fallback as such when the bridge cannot run. Points the interpreter at a missing path, so no python runs. |
| `unit/gitignore.test.js` | Build output and `node_modules/` are ignored by git; sources are not. |
| `integration/bridge-cli.test.js` | The `bridge.py` command-line protocol: exit codes, JSON on stdout, diagnostics on stderr. |
| `integration/problem-generation.test.js` | All 42 problem types generate a renderable payload; pins the renderer's parsing assumptions for the three special-cased types. |
| `integration/evaluation.test.js` | Scoring end to end, including what happens when the answer contains shell metacharacters. |
| `integration/rounds.test.js` | Round plumbing and `TwoBackRecall`'s cross-round state. |

## The `BUG:` convention

Tests whose name starts with `BUG:` assert the current, **defective** behaviour
on purpose. Each carries a comment naming the safe expectation that should
replace it. They exist so that fixing the underlying defect produces a loud,
specific failure pointing at the assertion to invert — rather than silence.

Do not "repair" a `BUG:` test by loosening it. Either the defect is still there
(leave it) or it has been fixed (invert it, and drop the marker).

## Fixed defects and the tests that hold them fixed

| Defect | Regression test |
| --- | --- |
| Answer text was interpolated into a `/bin/sh` command and executed | `unit/no-shell.test.js`, `integration/evaluation.test.js` → "the answer text never reaches a shell" |
| Answers containing `\`, `$` or `` ` `` were mangled or silently rescored by the fallback | `integration/evaluation.test.js` → "survives the round trip intact", "the bridge result is used, not the fallback" |
| Interpreter and bridge paths hardcoded to one machine | `unit/no-shell.test.js` → "path resolution is not machine-specific" |
| Built app looked for `preload.js` while vite emits `preload.mjs`; renderer entry resolved outside the project | `unit/paths.test.js` → "build-output layout" |
| `is_scored` dropped by the bridge, so `TwoBackRecall` warm-ups were graded against "none" | `integration/rounds.test.js`, `integration/bridge-cli.test.js` |
| Multi-line solutions could not be typed into the single-line recall input | `unit/renderer-contract.test.js` → "the recall input", `integration/problem-generation.test.js` |
| Evaluation re-instantiated the problem without its creation state, breaking `Anagram` | `integration/evaluation.test.js` → "problem state travels with the evaluation" |
| Stylesheet `@import`ed a webfont the CSP blocks | `unit/csp.test.js` |
| An empty answer or any emoji matched an emoji solution; suit glyphs and METAR numbers (`05`, `M03`) could not be typed as shown | `integration/evaluation.test.js` → "symbol solutions"; `py_app/test/test_scoring.py` |
| Quit during a pending evaluation crashed `FeedbackScreen`; a pending `createProblem` could reopen a game after Quit | `unit/renderer-contract.test.js` → "results that arrive after the player quits" |
| An exact-match fallback was shown as a real grade | `unit/evaluate-fallback.test.js`, `unit/renderer-contract.test.js` → "a fallback verdict is shown with a warning" |
| `dist/`, `dist-electron/` and `node_modules/` were not ignored by git | `unit/gitignore.test.js` |
| A double click on Next skipped rounds, and `TwoBackRecall` could ask for an item that was never shown | `unit/renderer-contract.test.js` → "a second press of Next while a round loads" |
| The feedback screen showed newlines as spaces, so "Expected" and "You typed" could look identical | `unit/renderer-contract.test.js` → "the feedback screen"; `py_app/test/test_scoring.py` → `TestListAnswers` |
| Games with a one-line answer got a textarea, where Enter added a newline | `integration/bridge-cli.test.js` → "a game with a one-line answer asks for a one-line input" |
| Each `SentenceCompletion` round made a GNews request and could repeat a headline, because the cache was in memory and each round is a new process | `py_app/test/test_utils.py` → `TestFetchHeadlinesCache`; `py_app/test/test_problem_generation.py` → `TestHeadlinesAcrossProcesses` |
| `JapaneseWord` accepted only one reading of a word with two | `integration/evaluation.test.js` → "alternative readings travel with the evaluation"; `py_app/test/test_scoring.py` → `TestJapaneseReadings` |

## Invariants

`src/main/invariants.js` and the mirrored helpers at the top of `bridge.py`
provide two severities:

- **`requires(...)`** — hard precondition, always throws. Reserved for
  programmer errors (wrong type, wrong arity, out of range). A correct caller
  never trips one, so adding them cannot change a working code path.
- **`checks(...)`** — soft invariant. Records the violation and notifies
  listeners but does **not** throw. `bridge.py` writes these to stderr as
  `INVARIANT[CODE] message {json}`, keeping stdout pure JSON.

No problem type violates a soft invariant any more, which is why
`integration/bridge-cli.test.js` exercises the mechanism through
`runPythonSnippet` rather than through a real game.

Set `MEMORY_TRAINER_STRICT=1` (both sides honour it) to turn soft violations
into throws. That is what `npm run test:strict` does.

Assert on soft violations with the `collectViolations` helper:

```js
const { value, violations } = collectViolations(() => create_problem('NameList', 1))
assert.ok(violations.some(v => v.code === 'UNANSWERABLE_SOLUTION'))
```

## Notes

- Integration scripts pass `--test-concurrency=1`. `TwoBackRecall` keeps its
  history in a single shared temp file, so parallel test processes corrupt each
  other.
- Integration tests skip (they do not fail) when the hardcoded virtualenv
  interpreter is absent — see `pythonUnavailable()` in `helpers/`.
- `SentenceCompletion` fetches remote headlines and is excluded from the sweep.
  Run it with `RUN_NETWORK_TESTS=1`.
- `test_all_games.js` at the project root predates this suite and only checks
  field presence. `integration/problem-generation.test.js` supersedes it.
