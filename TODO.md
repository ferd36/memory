# Memory Trainer — TODO

Open items from the js_app review of 2026-08-03. Fixed items are at the bottom
for context; see `js_app/test/README.md` for the test conventions.

Every entry names the regression test to write, or the `BUG:`-marked test that
already exists and should be inverted once the fix lands.

---

## Open

### 1. `execSync`-style blocking freezes the whole app
**Where:** `js_app/src/main/problems.js:78` (`callBridge`), `js_app/src/main/index.js` IPC handlers

`execFileSync` is still synchronous. Each call spawns a fresh Python
interpreter that re-imports `problems.py` (67 KB) and reloads the dictionaries —
roughly 400 ms during which the Electron main process, and therefore the entire
UI, is frozen. It happens on every create and every evaluate.

**Fix:** either `execFile` returning a promise (the IPC handlers are already
`async`-compatible), or a long-lived Python subprocess speaking JSON over
stdin/stdout, which also removes the repeated dictionary loading.

**Test:** assert `callBridge` returns a promise and that the handlers await it;
measure that two concurrent `create_problem` calls overlap rather than serialise.

---

### 2. A failed round load looks like a dead button
**Where:** `js_app/src/renderer/App.jsx:23` (`loadRound`), `App.jsx:17` (`startProblemType`)

`loadRound` awaits `window.api.createProblem`, which rejects on any bridge
failure. Nothing catches it: the user gets an unhandled rejection and a game
button that appears to do nothing. `get_problem_types` has the mirror problem —
it returns `[]` on error (`problems.js`), so a broken interpreter path yields a
"Select a Game" screen with zero buttons and no explanation.

**Fix:** an error phase in the reducer plus a visible message; surface the
bridge's stderr.

**Test:** `unit/renderer-contract.test.js` → "BUG: a failing createProblem
rejects with nothing to catch it" and "BUG: there is no error state or error
boundary". Invert both.

---

### 3. The partial score is computed and thrown away
**Where:** `js_app/src/renderer/App.jsx:251` (`FeedbackScreen`)

The bridge returns `{score, correct}` and the renderer reads only `correct`, so
a 0.95 answer renders identically to a 0.0 one. `py_app` models partial credit
throughout (`Record.score`); the UI does not expose it.

**Fix:** show the score on the feedback screen; decide whether near-misses
deserve their own visual state rather than a flat ✗.

**Test:** `unit/renderer-contract.test.js` → "BUG: the partial score is computed
by the bridge and discarded". Invert.

---

### 4. No score accumulates across a game
**Where:** `js_app/src/renderer/App.jsx:11` (`MAX_ROUNDS`), `App.jsx:36` (`handleNext`)

Ten rounds are played and the last one calls `handleQuit()` straight back to the
selection screen. Nothing is totalled, nothing is shown, nothing is persisted —
unlike `py_app/sessions.py`, which records every attempt.

**Fix:** accumulate per-round results; add an end-of-game summary. Consider
writing through to the same store `sessions.py` uses so both front-ends share a
history.

**Test:** `unit/renderer-contract.test.js` → "BUG: nothing accumulates a score
across rounds". Invert.

---

### 5. The recall timer is displayed but never recorded
**Where:** `js_app/src/renderer/App.jsx:193`, `App.jsx:242`

`RecallScreen` runs a `requestAnimationFrame` timer and renders `Time: N.NNs`,
but the elapsed time is never passed to `onSubmit`. `py_app`'s `Record` has a
`response_ms` field that the JS app has no way to fill.

**Fix:** pass the elapsed milliseconds through `onSubmit` and into whatever
persistence item 4 introduces.

**Test:** `unit/renderer-contract.test.js` → "BUG: the recall timer is displayed
but never submitted". Invert.

---

### 6. `TwoBackRecall` keeps its history in one shared temp file
**Where:** `py_app/problems.py:1791-1792`

`tempfile.gettempdir()/memory_twoback.json` is global. Two games — or the
terminal trainer and the Electron app at once, or two test processes — write
over each other. It is also why `npm run test:integration` has to pass
`--test-concurrency=1`.

**Fix:** scope the history to a game session. The `state` round-trip added for
`Anagram` (`bridge.py::_extra_state`) is the natural carrier: return the history
in `state` and hand it back on the next `create`, so no file is needed.

**Test:** `integration/rounds.test.js` → "BUG: history lives in one shared temp
file, not per-session state". Invert, and drop `--test-concurrency=1` once it
holds.

---

### 8. Smaller renderer issues
**Where:** `js_app/src/renderer/App.jsx`

- `MemorizeScreen`'s effect depends on `onComplete` (`App.jsx:50`), which is a
  fresh arrow on every `App` render. Safe only because `App` happens not to
  re-render during the memorize phase; any added parent state restarts the
  exposure timer mid-round. Wrap in `useCallback` or key the screen by round.
- The inner handle of the double `requestAnimationFrame` in `MemorizeScreen` is
  never stored, so the cleanup cannot cancel it. Under `React.StrictMode` the
  progress bar can be zeroed before its transition is set up.
- `StrictMode` double-invokes the type-list effect (`App.jsx:13`), spawning two
  Python processes at startup. Item 1 makes this cheaper; it is still wasteful.
- `evaluation` is never reset in `handleNext`/`loadRound`, leaving stale state
  between rounds. Harmless today because `FeedbackScreen` only mounts after a
  fresh evaluation, but fragile.
- `SpatialGrid` is a grid game that the renderer does not special-case the way
  it does `MatrixMemory`, so it renders as plain text.

---

### 9. Difficulty does not scale
**Where:** `js_app/src/renderer/App.jsx:24`, `py_app/problems.py`

`round` is plumbed all the way from the renderer to `cls.create(round_num=...)`,
but `TwoBackRecall` is the only class that reads it — every other `create`
swallows it in `**kwargs`. Round 10 is exactly as hard as round 1.

**Test:** `integration/rounds.test.js` → "is accepted at any round without
changing the exposure time" documents the current behaviour; rewrite it to
assert the intended progression once one exists.

---

## Done (2026-11-06)

Item 7: `test_problems.py` now imports `ChemicalFormula1`, and `pytest` runs from
`py_app/`. `test_ui.py` and `test_two_back.py` are manual scripts, and they no
longer run on import.

---

## Done (2026-08-03)

Regression tests for each are listed in `js_app/test/README.md`.

1. Command injection — answer text was interpolated into a `/bin/sh` command and
   executed. Now `execFileSync` with an argv array; no shell.
2. Answers containing `\`, `$` or `` ` `` were mangled, and `a\"b` was a shell
   syntax error that silently switched scoring to exact match.
3. Interpreter and bridge paths hardcoded to one machine.
4. Built app looked for `preload.js` while vite emits `preload.mjs`; the renderer
   entry resolved outside the project. `package.json` `main` repointed at the
   build output.
5. `is_scored` dropped by the bridge, so `TwoBackRecall` warm-up rounds were
   graded against the placeholder solution "none".
6. Multi-line solutions could not be entered — recall now renders a `<textarea>`
   for `input_type === 'multiline'`.
7. Evaluation re-instantiated the problem without its creation state, breaking
   `Anagram`'s alternative-anagram acceptance. Fixed generally via the `state`
   round-trip.
8. The stylesheet `@import`ed a webfont that the CSP blocks, so it never applied.
