import json
import os
import random
import re
import sys
import time
from pathlib import Path

_UTILS_DIR = Path(__file__).resolve().parent

# This file is src/apps/memory/py_app/utils.py.
_ENV_PATHS = [
    _UTILS_DIR.parents[2] / ".env",  # src/.env
    _UTILS_DIR.parents[1] / "news" / ".env",  # apps/news/.env, same GNEWS_KEY
]

# Try to load .env from project root or news app
try:
    from dotenv import load_dotenv
    for env_path in _ENV_PATHS:
        try:
            if env_path.exists():
                load_dotenv(env_path)
                break
        except PermissionError:
            pass
    else:
        load_dotenv()
except ImportError:
    pass


def format_problem_name(class_name: str) -> str:
    """Format problem class name for display by parsing camelcase."""
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', class_name)
    name = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', name)
    return name.strip()

_DICTS_DIR = _UTILS_DIR / 'dicts'


def _dict_path(name: str) -> Path:
    return _DICTS_DIR / name


_APP_DICT_NAMES = ('common_english_words.txt', 'common_french_words.txt', 'german_words.txt')
_APP_DICT_PATHS = [str(_DICTS_DIR / name) for name in _APP_DICT_NAMES]
dict_paths = ['/usr/share/dict/words'] + _APP_DICT_PATHS

words = []


def load_dicts(word_length_min=4, word_length_max=6):
    if words:
        return
    if not _DICTS_DIR.is_dir():
        print(f"Error: dicts folder not found: {_DICTS_DIR}", file=sys.stderr)
        sys.exit(1)
    for name in _APP_DICT_NAMES:
        path = _DICTS_DIR / name
        if not path.exists():
            print(f"Error: dictionary file not found: {path}", file=sys.stderr)
            sys.exit(1)
    for dict_path in dict_paths:
        if not os.path.exists(dict_path):
            # The system word list is absent on many Linux systems. Keep an
            # empty entry: Anagram reads the lists by position.
            print(f"Warning: dictionary file not found, skipped: {dict_path}", file=sys.stderr)
            words.append([])
            continue
        with open(dict_path) as f:
            words_tmp = [w.strip().lower() for w in f if w.strip().isalpha()]
            if "german" in dict_path:
                words_tmp = [w.replace('ß', 'ss') for w in words_tmp]
            words.append([w for w in words_tmp if word_length_min <= len(w) <= word_length_max])
    if not words or all(len(w) == 0 for w in words):
        print("Error: all dictionary files are empty or contain no words in length range 4–6.", file=sys.stderr)
        sys.exit(1)


load_dicts()


def _pick_word_list(min_size: int) -> list[str]:
    """Pick a non-empty word list. Raises ValueError if none available."""
    available = [w for w in words if len(w) >= min_size]
    if not available:
        raise ValueError("No word list with enough entries")
    return random.choice(available)


def rnd_number(number_length: int) -> str:
    """Generate a random number of a given length. Requires number_length >= 0."""
    if number_length < 0:
        raise ValueError("number_length must be non-negative")
    return ''.join([random.choice('0123456789') for _ in range(number_length)])


def load_frequencies() -> dict[str, list[str]]:
    """Load frequencies from dicts/frequencies.txt. Returns empty lists if file missing."""
    path = _UTILS_DIR / 'dicts/frequencies.txt'
    frequencies: dict[str, list[str]] = {'approach': [], 'tower': [], 'ground': []}
    if not path.exists():
        return frequencies
    try:
        with open(path) as f:
            lines = f.readlines()
    except OSError:
        return frequencies
    current_section = None
    for line in lines:
        line = line.strip()
        if line.startswith('# Approach frequencies'):
            current_section = 'approach'
        elif line.startswith('# Tower frequencies'):
            current_section = 'tower'
        elif line.startswith('# Ground frequencies'):
            current_section = 'ground'
        elif line and current_section and not line.startswith('#'):
            frequencies[current_section].append(line)
    return frequencies


def load_airline_codes() -> list[str]:
    """Load the airline codes. dicts/airlines.txt also has invalid codes, such as '--'."""
    path = _dict_path('airlines.txt')
    if not path.exists():
        return []
    with open(path, encoding='utf-8') as f:
        codes = [line.split(',', 1)[0].strip() for line in f if ',' in line]
    return [code for code in codes if code.isalnum()]


GNEWS_URL = "https://gnews.io/api/v4/top-headlines"

# Headlines change slowly and the GNews free plan has a small daily request
# limit, so a game round must not make a request each time. The Electron app
# starts a new process for each round, so this state must be in a file. The
# file does not contain the API key.
_HEADLINE_TTL_S = 600
_HEADLINE_TIMEOUT_S = 5  # The Electron window is frozen during a request.
_MAX_USED_HEADLINES = 200
_HEADLINE_CACHE_FILE = _UTILS_DIR / 'data' / 'headlines.json'


def _read_headline_store() -> dict:
    """Read the headline file. A missing or damaged file counts as empty."""
    try:
        store = json.loads(_HEADLINE_CACHE_FILE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return store if isinstance(store, dict) else {}


def _write_headline_store(store: dict) -> None:
    """Write the headline file. If this fails, the game still works without a cache."""
    tmp = _HEADLINE_CACHE_FILE.with_name(_HEADLINE_CACHE_FILE.name + '.tmp')
    try:
        _HEADLINE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(store, ensure_ascii=False), encoding='utf-8')
        os.replace(tmp, _HEADLINE_CACHE_FILE)
    except OSError:
        pass


def _fresh_titles(entry, now: float) -> list[str] | None:
    """Return the titles of a cache entry, or None if it is old or damaged."""
    if not isinstance(entry, dict):
        return None
    fetched_at, titles = entry.get('fetched_at'), entry.get('titles')
    if not isinstance(fetched_at, (int, float)) or not 0 <= now - fetched_at < _HEADLINE_TTL_S:
        return None
    if not isinstance(titles, list) or not all(isinstance(t, str) for t in titles):
        return None
    return titles


def fetch_gnews_headlines(topic: str = "general", max_items: int = 10) -> list[str]:
    """Fetch headline titles from GNews API. Returns empty list if unavailable."""
    api_key = os.getenv("GNEWS_KEY", "")
    if not api_key or api_key == "your_gnews_key_here":
        return []
    key = f"{topic}|{max_items}"
    now = time.time()
    store = _read_headline_store()
    entries = store.get('titles')
    if not isinstance(entries, dict):
        entries = {}
    cached = _fresh_titles(entries.get(key), now)
    if cached is not None:
        return cached
    titles = _request_gnews_headlines(api_key, topic, max_items)
    # A failed request is also kept, so that an offline game does not wait for a
    # timeout in each round.
    entries[key] = {'fetched_at': now, 'titles': titles}
    store['titles'] = entries
    _write_headline_store(store)
    return titles


def used_headlines() -> set[str]:
    """Return the headlines that a game already showed."""
    used = _read_headline_store().get('used')
    return {h for h in used if isinstance(h, str)} if isinstance(used, list) else set()


def mark_headline_used(title: str) -> None:
    """Remember a headline that a game shows, up to a limit."""
    store = _read_headline_store()
    used = store.get('used')
    store['used'] = [*(used if isinstance(used, list) else []), title][-_MAX_USED_HEADLINES:]
    _write_headline_store(store)


def _request_gnews_headlines(api_key: str, topic: str, max_items: int) -> list[str]:
    try:
        import requests
        params = {
            "token": api_key,
            "topic": topic,
            "lang": "en",
            "country": "us",
            "max": max_items,
        }
        resp = requests.get(GNEWS_URL, params=params, timeout=_HEADLINE_TIMEOUT_S)
        resp.raise_for_status()
        data = resp.json()
        titles = []
        for article in data.get("articles", []):
            title = article.get("title", "").strip()
            if title and len(title.split()) >= 4:
                titles.append(title)
        return titles
    # No requests module, a network or HTTP error, or a response of an unexpected shape.
    except (ImportError, OSError, ValueError, AttributeError, TypeError):
        return []


def levenshtein_distance(s1, s2):
    """Calculate the Levenshtein distance between two strings"""
    if len(s1) < len(s2):
      return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
      return len(s1)
    
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
      current_row = [i + 1]
      for j, c2 in enumerate(s2):
        insertions = previous_row[j + 1] + 1
        deletions = current_row[j] + 1
        substitutions = previous_row[j] + (c1 != c2)
        current_row.append(min(insertions, deletions, substitutions))
      previous_row = current_row
    
    return previous_row[-1]
