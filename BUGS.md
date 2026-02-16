# Bug Report: `src/apps/memory`

## 1. **utils.py – `load_dicts()` mutates global and duplicates data**

- **Location:** `utils.py` lines 44–52, 55.
- **Issue:** `load_dicts()` **appends** to the global `words` list instead of replacing it. Each call adds another set of word lists. So:
  - A second call (e.g. from `Anagram.create()` when `not words`, or from `Anagram._is_valid_anagram()` when `not words`) doubles the number of lists.
  - Over time, `words` can contain many duplicate language lists and grow unnecessarily.
- **Impact:** Wrong/duplicate word lists, extra memory use, and `_pick_word_list` effectively favoring languages that get appended more often.

---

## 2. **sessions.py – Corrupt gzip raises uncaught exception**

- **Location:** `sessions.py`: `_read_file_content()` (lines 11–17), used by `load_session_statistics()` and `save_session_data()`.
- **Issue:** If the sessions file exists and its first two bytes are gzip magic (`\x1f\x8b`) but the rest is corrupt, `gzip.decompress(raw)` can raise (e.g. `OSError` or `zlib.error`). `load_session_statistics()` only catches `json.JSONDecodeError` and `FileNotFoundError`, so this exception propagates. `save_session_data()` does not catch it when reading existing content.
- **Impact:** Corrupt gzip sessions file can crash the app when loading stats or saving a new session, instead of falling back to empty stats or a safe write.

---

## 3. **sessions.py – `save_session_data()` can lose new session on read error**

- **Location:** `sessions.py` lines 113–116.
- **Issue:** When appending a session, existing content is read with `_read_file_content(_SESSIONS_FILE)`. Any failure in that read (e.g. corrupt gzip, I/O error) raises before the new session is written.
- **Impact:** The new session is never saved if reading the existing file fails.

---

## 4. **File I/O without explicit UTF-8 encoding**

- **Location:**
  - `utils.py`: line 48 (`load_dicts`), line 83 (`load_frequencies`);
  - `problems.py`: lines 207, 219 (FlightInfo), 283 (TokyoMetro), 813 (Atc), 952 (FlightPlan), 1033 (Road).
- **Issue:** All use `open(path)` (or `open(path) as f`) without `encoding='utf-8'`. On some systems or with non-ASCII dict/data files, this can lead to wrong decoding or `UnicodeDecodeError`.
- **Impact:** Failures or wrong behavior when dict/data files contain non-ASCII characters or when the default encoding is not UTF-8.

---

## 5. **problems.py – `create_problems_dict()` returns empty dict**

- **Location:** `trainer.py` line 19: `all_problems = create_problems_dict()`, and line 286: `random.choices(list(problems.keys()), list(problems.values()))[0]`.
- **Issue:** If no problem classes are discovered (e.g. all filtered out or module loading issue), `create_problems_dict()` returns `{}`. The trainer still runs and in `main()` does `random.choices([], [])[0]`, which raises (e.g. `IndexError` or invalid `random.choices` call).
- **Impact:** Crash when no problem types are available, with no clear "no problems available" handling.

---

## 6. **problems.py – `num_pairs` / `num_flights` / `num_waypoints` = 0**

- **Location:**
  - `WordPairs.create(..., num_pairs=0)`: line 27 uses `random.randint(0, num_pairs - 1)` → `randint(0, -1)`.
  - `WordNumberPairs.create(..., num_pairs=0)`: line 40, same pattern.
  - `FlightInfo.create(num_flights=0)`: line 267, `random.randint(1, num_flights)` → `randint(1, 0)`.
  - `FlightPlan.create(num_waypoints=0)`: line 1002, `random.randint(0, num_waypoints - 1)` → `randint(0, -1)`.
- **Issue:** No guard against `num_pairs` / `num_flights` / `num_waypoints` being 0; `random.randint` is then called with an invalid range.
- **Impact:** `ValueError` if any of these `create()` methods are ever called with 0 (e.g. via a future UI or API).

---

## 7. **problems.py – `Number` / `NumberLong` / `NumberList` / `NumberBackward` with `number_length=0`**

- **Location:** `utils.rnd_number(0)` returns `''`. That string is then used as `memorize` and/or `solution` in several problem types (e.g. `Number`, `NumberLong`, `NumberList`, `NumberBackward`).
- **Issue:** `Problem.__post_init__` requires non-empty, non-blank `memorize` and `solution`, so constructing the problem with empty strings raises `ValueError`.
- **Impact:** Calling those problem `create()` methods with `number_length=0` (or any code path that yields `rnd_number(0)`) causes a validation error instead of a clear "invalid length" check.

---

## 8. **trainer.py – Empty `selected_problems` is not treated as "no selection"**

- **Location:** `trainer.py` lines 56–58 and 264.
- **Issue:** If the user enters only out-of-range numbers (e.g. `99 100`), `selected_problems` can be `{}`. The code returns `None` when `not selected_problems`, so we exit. But if another code path ever passed an empty dict (e.g. `main(..., selected_problems={})`), then `problems = selected_problems if selected_problems else all_problems` would use the empty dict (empty dict is falsy, so we'd actually use `all_problems`). So current CLI is safe; the only risk is if `main()` were called with `selected_problems={}` from elsewhere.
- **Impact:** Low; mainly a consistency/clarity point for "no problems selected" vs "use all problems."

---

## 9. **classes.py – `Record` allows any object with `to_dict`**

- **Location:** `classes.py` lines 96–98.
- **Issue:** `Record.__post_init__` only checks `hasattr(self.problem, "to_dict")`, not that `problem` is a `Problem` instance.
- **Impact:** Any object with a `to_dict` method can be stored as `problem`. If that object's `to_dict()` or structure differs from `Problem`, session serialization or stats logic may break or produce inconsistent data. Defensive validation is missing.

---

## 10. **sessions.py – Partial JSONL corruption loses all sessions**

- **Location:** `sessions.py` `_read_sessions()` (lines 76–90), used by `load_session_statistics()`.
- **Issue:** Sessions are read line-by-line with `json.loads(line)`. The first bad line raises `JSONDecodeError`; `load_session_statistics()` catches it and returns `empty_stats`, so the whole file is effectively treated as unusable.
- **Impact:** One corrupted line in the sessions file causes all history to be ignored; no "skip bad line and continue" behavior.

---

## Summary table

| # | Severity | Area      | Issue |
|---|----------|-----------|--------|
| 1 | High     | utils     | `load_dicts()` appends to `words`, duplicating data on repeated calls |
| 2 | Medium   | sessions  | Corrupt gzip in sessions file raises uncaught exception |
| 3 | Medium   | sessions  | New session not saved if reading existing file fails |
| 4 | Low–Med  | utils, problems | File opens without `encoding='utf-8'` |
| 5 | Medium   | trainer   | No handling when `create_problems_dict()` returns `{}` |
| 6 | Low      | problems  | `num_pairs`/`num_flights`/`num_waypoints` = 0 → `randint` error |
| 7 | Low      | problems  | `number_length=0` → empty string → `Problem` validation error |
| 8 | Low      | trainer   | Empty `selected_problems` semantics (minor) |
| 9 | Low      | classes   | `Record` accepts any object with `to_dict` |
| 10 | Low     | sessions  | One bad JSONL line causes full history to be discarded |
