"""Unit tests for sessions module: gzip(JSONL) and session methods."""

import gzip
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from classes import Problem, Record

from sessions import (
    _read_file_content,
    _read_sessions,
    format_score,
    load_session_statistics,
    save_session_data,
)


def _make_problem(name="Test", memorize="a b", prompt="?", solution="b a", exposure_ms=3000, problem_type="single line"):
    return Problem(name=name, memorize=memorize, prompt=prompt, solution=solution, exposure_ms=exposure_ms, problem_type=problem_type)


def _make_session_dict(records=None):
    if records is None:
        records = []
    return {
        "date": "2025-01-15 12:00:00",
        "duration_seconds": 60,
        "total_questions": len(records),
        "correct_answers": sum(1 for r in records if r.get("correct")),
        "score_percentage": 100.0 if not records else sum(1 for r in records if r.get("correct")) / len(records) * 100,
        "records": records,
    }


def _make_record_dict(problem_dict=None, response="ans", response_ms=1000, score=1.0):
    if problem_dict is None:
        problem_dict = _make_problem().to_dict()
    return {
        "problem": problem_dict,
        "response": response,
        "response_ms": response_ms,
        "score": score,
        "correct": score >= 1.0,
    }


# --- _read_sessions -----------------------------------------------------------------


class TestReadSessions(unittest.TestCase):
    """_read_sessions: missing file, empty, JSONL, gzip."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.tmp.close()
        self.path = Path(self.tmp.name)

    def tearDown(self):
        if self.path.exists():
            self.path.unlink()

    def test_missing_file_returns_empty_list(self):
        self.path.unlink()
        self.assertEqual(_read_sessions(self.path), [])

    def test_empty_file_returns_empty_list(self):
        self.path.write_text("", encoding="utf-8")
        self.assertEqual(_read_sessions(self.path), [])

    def test_jsonl_one_line(self):
        session = _make_session_dict([_make_record_dict()])
        self.path.write_text(json.dumps(session, ensure_ascii=False) + "\n", encoding="utf-8")
        out = _read_sessions(self.path)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["total_questions"], 1)

    def test_jsonl_one_line_single_session(self):
        session = _make_session_dict([_make_record_dict()])
        self.path.write_text(json.dumps(session, ensure_ascii=False) + "\n", encoding="utf-8")
        out = _read_sessions(self.path)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["date"], session["date"])
        self.assertEqual(len(out[0]["records"]), 1)

    def test_jsonl_multiple_lines(self):
        s1 = _make_session_dict([_make_record_dict(response="x")])
        s2 = _make_session_dict([_make_record_dict(response="y")])
        self.path.write_text(
            json.dumps(s1, ensure_ascii=False) + "\n" + json.dumps(s2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        out = _read_sessions(self.path)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["records"][0]["response"], "x")
        self.assertEqual(out[1]["records"][0]["response"], "y")

    def test_gzip_file_decompressed_and_read(self):
        session = _make_session_dict([_make_record_dict(response="gzip")])
        line = json.dumps(session, ensure_ascii=False) + "\n"
        self.path.write_bytes(gzip.compress(line.encode("utf-8")))
        out = _read_sessions(self.path)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["records"][0]["response"], "gzip")


# --- format_score ------------------------------------------------------------------


class TestFormatScore(unittest.TestCase):
    """format_score with 0 questions, with records, single/multiple problem types."""

    def test_zero_questions(self):
        out = format_score(0, 0, [])
        self.assertIn("Training session completed!", out)
        self.assertIn("No questions answered", out)

    def test_with_total_score_and_final_percentage(self):
        pb = _make_problem(name="A")
        records = [Record(pb, "ok", 1000, 1.0)]
        out = format_score(1, 1, records, total_score=1.0, final_percentage=100.0)
        self.assertIn("100.0%", out)
        self.assertIn("Perfect answers", out)

    def test_without_total_score(self):
        pb = _make_problem(name="B")
        records = [Record(pb, "ok", 1000, 1.0)]
        out = format_score(1, 1, records)
        self.assertIn("1/1", out)
        self.assertIn("correct answers", out)

    def test_results_by_problem_type_when_multiple_types(self):
        p1 = _make_problem(name="Type One")
        p2 = _make_problem(name="Type Two")
        records = [
            Record(p1, "a", 100, 1.0),
            Record(p2, "b", 200, 1.0),
        ]
        out = format_score(2, 2, records)
        self.assertIn("Results by problem type:", out)
        self.assertIn("Type One", out)
        self.assertIn("Type Two", out)


# --- load_session_statistics -------------------------------------------------------


class TestLoadSessionStatistics(unittest.TestCase):
    """load_session_statistics: missing file, empty, with data."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.tmp.close()
        self.path = Path(self.tmp.name)

    def tearDown(self):
        if self.path.exists():
            self.path.unlink()

    def test_missing_file_returns_empty_stats(self):
        self.path.unlink()
        stats = load_session_statistics(str(self.path))
        self.assertEqual(stats["total_sessions"], 0)
        self.assertEqual(stats["total_questions"], 0)
        self.assertEqual(stats["problem_name_stats"], {})
        self.assertIsNone(stats["best_session"])
        self.assertEqual(stats["recent_average"], 0.0)

    def test_empty_compressed_file_returns_empty_stats(self):
        self.path.write_text("\n", encoding="utf-8")
        stats = load_session_statistics(str(self.path))
        self.assertEqual(stats["total_sessions"], 0)

    def test_one_session_jsonl(self):
        session = _make_session_dict([
            _make_record_dict(problem_dict=_make_problem(name="Anagram").to_dict(), response="x", score=1.0),
            _make_record_dict(problem_dict=_make_problem(name="Anagram").to_dict(), response="y", score=0.0),
        ])
        session["score_percentage"] = 50.0
        self.path.write_text(json.dumps(session, ensure_ascii=False) + "\n", encoding="utf-8")
        stats = load_session_statistics(str(self.path))
        self.assertEqual(stats["total_sessions"], 1)
        self.assertEqual(stats["total_questions"], 2)
        self.assertEqual(stats["total_correct_answers"], 1)
        self.assertEqual(stats["overall_average_score"], 50.0)
        self.assertIn("Anagram", stats["problem_name_stats"])
        self.assertEqual(stats["problem_name_stats"]["Anagram"]["total"], 2)
        self.assertEqual(stats["problem_name_stats"]["Anagram"]["correct"], 1)
        self.assertEqual(stats["best_session"]["score_percentage"], 50.0)
        self.assertEqual(stats["recent_average"], 50.0)

    def test_corrupt_file_returns_empty_stats(self):
        self.path.write_text("not valid json\n", encoding="utf-8")
        stats = load_session_statistics(str(self.path))
        self.assertEqual(stats["total_sessions"], 0)
        self.assertEqual(stats["problem_name_stats"], {})

    def test_stats_record_without_score_uses_accuracy_percentage(self):
        rec = _make_record_dict(problem_dict=_make_problem(name="X").to_dict(), response="a", score=1.0)
        del rec["score"]
        session = _make_session_dict([rec])
        session["total_questions"] = 1
        session["correct_answers"] = 1
        session["score_percentage"] = 100.0
        self.path.write_text(json.dumps(session, ensure_ascii=False) + "\n", encoding="utf-8")
        stats = load_session_statistics(str(self.path))
        self.assertEqual(stats["problem_name_stats"]["X"]["average_score"], 100.0)

    def test_stats_record_response_ms_zero_no_response_times(self):
        rec = _make_record_dict(problem_dict=_make_problem(name="Y").to_dict(), response="b", response_ms=0, score=0.0)
        session = _make_session_dict([rec])
        self.path.write_text(json.dumps(session, ensure_ascii=False) + "\n", encoding="utf-8")
        stats = load_session_statistics(str(self.path))
        self.assertEqual(stats["problem_name_stats"]["Y"]["avg_response_time"], 0.0)
        self.assertEqual(stats["problem_name_stats"]["Y"]["response_time_std_dev"], 0.0)

    def test_stats_single_record_per_type_std_dev_zero(self):
        rec = _make_record_dict(problem_dict=_make_problem(name="Z").to_dict(), response="c", response_ms=100, score=1.0)
        session = _make_session_dict([rec])
        self.path.write_text(json.dumps(session, ensure_ascii=False) + "\n", encoding="utf-8")
        stats = load_session_statistics(str(self.path))
        self.assertEqual(stats["problem_name_stats"]["Z"]["accuracy_std_dev"], 0.0)
        self.assertEqual(stats["problem_name_stats"]["Z"]["response_time_std_dev"], 0.0)

    def test_session_dates_skips_bad_date(self):
        session = _make_session_dict([])
        session["date"] = "2025-01-01 12:00:00"
        session2 = _make_session_dict([])
        session2["date"] = None
        session2["score_percentage"] = 0
        session2["total_questions"] = 0
        content = json.dumps(session, ensure_ascii=False) + "\n" + json.dumps(session2, ensure_ascii=False) + "\n"
        self.path.write_text(content, encoding="utf-8")
        stats = load_session_statistics(str(self.path))
        self.assertEqual(len(stats["session_dates"]), 1)

    def test_session_dates_skips_session_that_raises_on_get(self):
        """Session that raises TypeError in .get() is skipped (covers except branch)."""
        from unittest.mock import patch
        good = _make_session_dict([])
        good["date"] = "2025-01-01 12:00:00"
        class BadSession(dict):
            def get(self, k, d=None):
                if k == "date":
                    raise TypeError("bad")
                return super().get(k, d)
        bad = BadSession({"date": "x", "score_percentage": 0, "total_questions": 0, "records": []})
        with patch("sessions._read_sessions", return_value=[good, bad]):
            stats = load_session_statistics(str(self.path))
        self.assertEqual(len(stats["session_dates"]), 1)


# --- save_session_data -------------------------------------------------------------


class TestSaveSessionData(unittest.TestCase):
    """save_session_data appends one JSON line; file is gzip(JSONL)."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.tmp.close()
        self.path = Path(self.tmp.name)

    def tearDown(self):
        if self.path.exists():
            self.path.unlink()

    def test_save_appends_json_line(self):
        import sessions as sessions_mod
        original = sessions_mod._SESSIONS_FILE
        try:
            sessions_mod._SESSIONS_FILE = self.path
            self.path.write_text("", encoding="utf-8")
            pb = _make_problem(name="Saved")
            records = [Record(pb, "answer", 1234, 1.0)]
            start = datetime(2025, 2, 1, 10, 0, 0)
            save_session_data(start, start.timestamp(), 1, 1, records)
            content = _read_file_content(self.path)
            self.assertTrue(content.endswith("\n"))
            line = content.strip()
            decoded = json.loads(line)
            self.assertEqual(decoded["total_questions"], 1)
            self.assertEqual(decoded["correct_answers"], 1)
            self.assertEqual(len(decoded["records"]), 1)
            self.assertEqual(decoded["records"][0]["problem"]["name"], "Saved")
            self.assertEqual(decoded["records"][0]["response"], "answer")
            self.assertEqual(decoded["records"][0]["response_ms"], 1234)
        finally:
            sessions_mod._SESSIONS_FILE = original


# --- Full JSON round-trip (integration) ------------------------------------------


class TestJsonRoundTripCorrectness(unittest.TestCase):
    """Full round-trip: session as JSON line, unicode, all problem fields."""

    def test_full_session_round_trip_identical(self):
        session = {
            "date": "2025-06-15 14:30:00",
            "duration_seconds": 120,
            "total_questions": 3,
            "correct_answers": 2,
            "score_percentage": round(2 / 3 * 100, 1),
            "records": [
                _make_record_dict(
                    problem_dict=_make_problem(name="Unicode", memorize="café", prompt="?", solution="éfac", problem_type="").to_dict(),
                    response="éfac",
                    response_ms=2000,
                    score=1.0,
                ),
                _make_record_dict(
                    problem_dict=_make_problem(name="Long", memorize="a" * 200, prompt="p", solution="s" * 200, exposure_ms=5000).to_dict(),
                    response="s" * 200,
                    response_ms=100,
                    score=0.0,
                ),
                _make_record_dict(
                    problem_dict=_make_problem(name="Matrix", problem_type="matrix").to_dict(),
                    response="x",
                    response_ms=500,
                    score=0.5,
                ),
            ],
        }
        line = json.dumps(session, ensure_ascii=False)
        decoded = json.loads(line)
        self.assertEqual(decoded["date"], session["date"])
        self.assertEqual(decoded["duration_seconds"], session["duration_seconds"])
        self.assertEqual(decoded["total_questions"], session["total_questions"])
        self.assertEqual(decoded["correct_answers"], session["correct_answers"])
        self.assertEqual(decoded["score_percentage"], session["score_percentage"])
        self.assertEqual(len(decoded["records"]), 3)
        for i, rec in enumerate(decoded["records"]):
            orig = session["records"][i]
            self.assertEqual(rec["problem"], orig["problem"])
            self.assertEqual(rec["response"], orig["response"])
            self.assertEqual(rec["response_ms"], orig["response_ms"])
            self.assertEqual(rec["score"], orig["score"])
            self.assertEqual(rec["correct"], orig["correct"])
