"""Unit tests for classes module: Problem and Record validation, __repr__, to_dict."""

import unittest

from classes import Problem, Record


def _valid_problem(**kwargs):
    defaults = dict(name="N", memorize="a", prompt="?", solution="b", exposure_ms=1000)
    defaults.update(kwargs)
    return Problem(**defaults)


class TestProblemValidation(unittest.TestCase):
    """Problem __post_init__ raises for invalid fields."""

    def test_name_empty_raises(self):
        with self.assertRaises(ValueError) as ctx:
            Problem(name="", memorize="a", prompt="?", solution="b", exposure_ms=1000)
        self.assertIn("name", str(ctx.exception))

    def test_name_blank_raises(self):
        with self.assertRaises(ValueError):
            Problem(name="   ", memorize="a", prompt="?", solution="b", exposure_ms=1000)

    def test_name_not_str_raises(self):
        with self.assertRaises(ValueError):
            Problem(name=123, memorize="a", prompt="?", solution="b", exposure_ms=1000)

    def test_memorize_empty_raises(self):
        with self.assertRaises(ValueError):
            Problem(name="N", memorize="", prompt="?", solution="b", exposure_ms=1000)

    def test_prompt_empty_raises(self):
        with self.assertRaises(ValueError):
            Problem(name="N", memorize="a", prompt="", solution="b", exposure_ms=1000)

    def test_solution_empty_raises(self):
        with self.assertRaises(ValueError):
            Problem(name="N", memorize="a", prompt="?", solution="", exposure_ms=1000)

    def test_exposure_ms_zero_raises(self):
        with self.assertRaises(ValueError):
            Problem(name="N", memorize="a", prompt="?", solution="b", exposure_ms=0)

    def test_exposure_ms_negative_raises(self):
        with self.assertRaises(ValueError):
            Problem(name="N", memorize="a", prompt="?", solution="b", exposure_ms=-1)

    def test_exposure_ms_not_int_raises(self):
        with self.assertRaises(ValueError):
            Problem(name="N", memorize="a", prompt="?", solution="b", exposure_ms="1000")

    def test_problem_type_not_str_raises(self):
        with self.assertRaises(TypeError):
            Problem(name="N", memorize="a", prompt="?", solution="b", exposure_ms=1000, problem_type=1)


class TestProblemMethods(unittest.TestCase):
    """Problem display_name, evaluate_solution, to_dict, __repr__."""

    def test_display_name(self):
        class WordList(Problem):
            pass
        self.assertEqual(WordList.display_name(), "Word List")

    def test_evaluate_solution_none_returns_zero(self):
        p = _valid_problem(solution="abc")
        self.assertEqual(p.evaluate_solution(None), 0.0)

    def test_to_dict(self):
        p = _valid_problem(name="X", problem_type="matrix")
        d = p.to_dict()
        self.assertEqual(d["name"], "X")
        self.assertEqual(d["problem_type"], "matrix")

    def test_repr(self):
        p = _valid_problem(name="R", memorize="m", prompt="p", solution="s", exposure_ms=500)
        r = repr(p)
        self.assertIn("name=R", r)
        self.assertIn("memorize=m", r)
        self.assertIn("exposure_ms=500", r)


class TestRecordValidation(unittest.TestCase):
    """Record __post_init__ raises for invalid fields."""

    def test_problem_without_to_dict_raises(self):
        with self.assertRaises(TypeError):
            Record(object(), "r", 0, 0.0)

    def test_response_not_str_raises(self):
        p = _valid_problem()
        with self.assertRaises(TypeError):
            Record(p, 123, 0, 0.0)

    def test_response_ms_negative_raises(self):
        p = _valid_problem()
        with self.assertRaises(ValueError):
            Record(p, "r", -1, 0.0)

    def test_response_ms_not_int_raises(self):
        p = _valid_problem()
        with self.assertRaises(ValueError):
            Record(p, "r", "100", 0.0)

    def test_score_not_number_raises(self):
        p = _valid_problem()
        with self.assertRaises(TypeError):
            Record(p, "r", 0, "0.5")

    def test_score_below_zero_raises(self):
        p = _valid_problem()
        with self.assertRaises(ValueError):
            Record(p, "r", 0, -0.1)

    def test_score_above_one_raises(self):
        p = _valid_problem()
        with self.assertRaises(ValueError):
            Record(p, "r", 0, 1.1)


class TestRecordMethods(unittest.TestCase):
    """Record to_dict and correct property."""

    def test_to_dict_includes_correct(self):
        p = _valid_problem()
        r = Record(p, "ans", 100, 1.0)
        d = r.to_dict()
        self.assertIn("correct", d)
        self.assertTrue(d["correct"])
        r2 = Record(p, "x", 50, 0.0)
        self.assertFalse(r2.to_dict()["correct"])
