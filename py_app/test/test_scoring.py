"""Scoring regressions: answers that got full credit when they should not, and
correct answers that could not get full credit."""

import random
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar
from unittest.mock import patch

import problems
from classes import Problem
from problems import (
    ColorSequence,
    FlightPlan,
    InventoryQuantities,
    JapaneseWord,
    MatrixMemory,
    Metar,
    NameList,
    PlayingCardSequence,
    SentenceCompletion,
    SimonColorSequence,
    SpatialGrid,
    create_problems_dict,
)


def _all_problem_classes():
    return sorted(create_problems_dict(), key=lambda c: c.__name__)


class TestEveryProblemType(unittest.TestCase):
    """Properties that must hold for every game, not only the ones seen failing."""

    def setUp(self):
        # SentenceCompletion would otherwise call the GNews API.
        patcher = patch.object(problems, "fetch_gnews_headlines", return_value=[])
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_create_returns_an_instance_of_its_own_class(self):
        # MatrixMemory, SpatialGrid and PlayingCardSequence returned a plain
        # Problem, so their evaluate_solution was never called in-process.
        for cls in _all_problem_classes():
            with self.subTest(cls=cls.__name__):
                self.assertIs(type(cls.create(round_num=1)), cls)

    def test_an_empty_answer_never_gets_full_credit(self):
        # An emoji solution normalised to '' and matched an empty answer.
        for cls in _all_problem_classes():
            for seed in range(25):
                random.seed(seed)
                pb = cls.create(round_num=3)
                if not getattr(pb, "is_scored", True):
                    continue
                with self.subTest(cls=cls.__name__, seed=seed, solution=pb.solution):
                    self.assertLess(pb.evaluate_solution(""), 1.0)

    def test_the_solution_itself_gets_full_credit(self):
        for cls in _all_problem_classes():
            for seed in range(25):
                random.seed(seed)
                pb = cls.create(round_num=3)
                with self.subTest(cls=cls.__name__, seed=seed, solution=pb.solution):
                    self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)


class TestListAnswers(unittest.TestCase):
    """The terminal trainer cannot enter a newline: Enter submits the answer."""

    def _name_list(self):
        return NameList("x", "m", "p", "Alice\nBob\nCara", 1000, "multiline")

    def test_any_whitespace_separates_the_items(self):
        for answer in ("alice bob cara", "Alice\nBob\nCara", "alice\r\nbob\r\ncara", " alice  bob\tcara "):
            with self.subTest(answer=answer):
                self.assertEqual(self._name_list().evaluate_solution(answer), 1.0)

    def test_the_wrong_order_does_not_get_full_credit(self):
        self.assertLess(self._name_list().evaluate_solution("cara bob alice"), 1.0)

    def test_items_run_together_do_not_get_full_credit(self):
        self.assertLess(self._name_list().evaluate_solution("alicebobcara"), 1.0)


def _problem(cls, solution):
    return cls("x", "m", "p", solution, 1000, "single line")


class TestAnswersInTheFormShown(unittest.TestCase):
    """Correct answers in a reasonable form got only partial credit."""

    CORRECT: ClassVar[list[tuple]] = [
        (FlightPlan, "33000", "33,000ft"),
        (FlightPlan, "33000", "33,000"),
        (FlightPlan, "33000", "33000 FT"),
        (FlightPlan, "121.5", "121.5MHz"),
        (FlightPlan, "121.5", "121.5 mhz"),
        (FlightPlan, "090", "090°"),
        (FlightPlan, "090", "90"),
        (FlightPlan, "RDU GKA", "rdu gka"),
        (ColorSequence, "R G B Y R", "rgbyr"),
        (ColorSequence, "R G B Y R", "r, g, b, y, r"),
        (ColorSequence, "R G B Y R", "red green blue yellow red"),
        (ColorSequence, "R", "red"),
        (SimonColorSequence, "RGBYP", "r g b y p"),
        (SimonColorSequence, "RGBYP", "red green blue yellow purple"),
        (SimonColorSequence, "P", "purple"),
        (InventoryQuantities, "2L", "2 l"),
        (InventoryQuantities, "500g", "500 G"),
        (SentenceCompletion, "rates,", "rates"),
        (SentenceCompletion, "markets?", "markets"),
        (SentenceCompletion, "What's", "whats"),
        (SentenceCompletion, "What's", "what's"),
        (SentenceCompletion, '"historic"', "historic"),
        (SentenceCompletion, "rates, signals", "rates signals"),
        (SentenceCompletion, "U.S.", "us"),
    ]

    WRONG: ClassVar[list[tuple]] = [
        (FlightPlan, "33000", "34,000ft"),
        (FlightPlan, "121.5", "121.7MHz"),
        (FlightPlan, "090", "91"),
        (FlightPlan, "RDU GKA", "rdu"),
        (ColorSequence, "R G B Y R", "rgbyg"),
        (ColorSequence, "R", "green"),
        (SimonColorSequence, "RGBYP", "r g b y r"),
        (InventoryQuantities, "2L", "3 l"),
        (InventoryQuantities, "2L", "2"),
        (SentenceCompletion, "rates,", "rate"),
        (SentenceCompletion, "rates,", ""),
        (SentenceCompletion, "rates,", ",,,"),
    ]

    def test_the_correct_answers_get_full_credit(self):
        for cls, solution, answer in self.CORRECT:
            with self.subTest(cls=cls.__name__, solution=solution, answer=answer):
                self.assertEqual(_problem(cls, solution).evaluate_solution(answer), 1.0)

    def test_the_wrong_answers_do_not(self):
        for cls, solution, answer in self.WRONG:
            with self.subTest(cls=cls.__name__, solution=solution, answer=answer):
                self.assertLess(_problem(cls, solution).evaluate_solution(answer), 1.0)


class TestJapaneseReadings(unittest.TestCase):
    """家 "house" has two readings, and each round accepted only one of them."""

    def _create(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "japanese_words.txt"
            path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            with patch.object(problems, "_dict_path", return_value=path):
                return JapaneseWord.create()

    def test_each_reading_of_the_same_word_gets_full_credit(self):
        pb = self._create(["家,ie,house", "家,uchi,house"])
        self.assertEqual(pb.evaluate_solution("ie"), 1.0)
        self.assertEqual(pb.evaluate_solution("UCHI"), 1.0)
        self.assertLess(pb.evaluate_solution("ko"), 1.0)

    def test_a_reading_with_another_meaning_does_not(self):
        pb = self._create(["下手,heta,unskillful", "下手,shimote,lower part of the stage"])
        other = "shimote" if pb.solution == "heta" else "heta"
        self.assertLess(pb.evaluate_solution(other), 1.0)

    def test_the_readings_can_travel_in_the_bridge_state(self):
        # The Electron app evaluates in a new process, with scalar state only.
        pb = self._create(["家,ie,house", "家,uchi,house"])
        self.assertIsInstance(pb._readings, str)


class TestSymbolSolutions(unittest.TestCase):
    """unidecode maps emoji to '' and suit glyphs to words."""

    def test_empty_answer_does_not_match_an_emoji(self):
        pb = Problem("X", "m", "p", "🍎", 1000)
        self.assertEqual(pb.evaluate_solution(""), 0.0)

    def test_a_different_emoji_does_not_match(self):
        pb = Problem("X", "m", "p", "🍎", 1000)
        self.assertEqual(pb.evaluate_solution("🚗"), 0.0)

    def test_the_same_emoji_matches(self):
        pb = Problem("X", "m", "p", "🍎", 1000)
        self.assertEqual(pb.evaluate_solution("🍎"), 1.0)

    def test_accents_are_still_ignored(self):
        pb = Problem("X", "m", "p", "São Paulo", 1000)
        self.assertEqual(pb.evaluate_solution("sao paulo"), 1.0)


class TestSpatialGrid(unittest.TestCase):
    def test_wrong_emoji_is_wrong(self):
        pb = SpatialGrid("Spatial Grid", "m", "What is at (1, 2)?", "🍎", 5000)
        self.assertLess(pb.evaluate_solution("🚗"), 1.0)
        self.assertLess(pb.evaluate_solution(""), 1.0)

    def test_the_emoji_name_is_accepted(self):
        # The terminal trainer only accepts ASCII keys.
        for emoji, name in SpatialGrid.EMOJI_NAMES.items():
            pb = SpatialGrid("Spatial Grid", "m", "What is at (1, 2)?", emoji, 5000)
            with self.subTest(emoji=emoji):
                self.assertEqual(pb.evaluate_solution(name), 1.0)
                self.assertEqual(pb.evaluate_solution(name.upper()), 1.0)

    def test_the_prompt_lists_the_names(self):
        for seed in range(30):
            random.seed(seed)
            pb = SpatialGrid.create()
            if pb.solution in SpatialGrid.EMOJI_NAMES:
                self.assertIn(SpatialGrid.EMOJI_NAMES[pb.solution], pb.prompt)

    def test_coordinates_in_parentheses_are_accepted_in_process(self):
        for seed in range(30):
            random.seed(seed)
            pb = SpatialGrid.create()
            if "," in pb.solution:
                self.assertEqual(pb.evaluate_solution(f"({pb.solution})"), 1.0)
                return
        self.fail("no coordinate question in 30 seeds")


class TestMatrixMemory(unittest.TestCase):
    def test_reversed_cell_is_accepted_in_process(self):
        # The terminal trainer scores the object create() returns.
        random.seed(1)
        pb = MatrixMemory.create()
        self.assertEqual(pb.evaluate_solution(pb.solution[::-1]), 1.0)


class TestPlayingCardSequence(unittest.TestCase):
    def _pb(self, solution):
        return PlayingCardSequence("Playing Card Sequence", "m", "p", solution, 4000)

    def test_ascii_suit_letters_are_accepted(self):
        for answer in ("AS", "as", "SA", "a s", "A♠", "♠A", "a spades", "ace of spades"):
            with self.subTest(answer=answer):
                self.assertEqual(self._pb("♠A").evaluate_solution(answer), 1.0)

    def test_ten_of_hearts(self):
        for answer in ("10H", "h10", "10 hearts", "♥10"):
            with self.subTest(answer=answer):
                self.assertEqual(self._pb("♥10").evaluate_solution(answer), 1.0)

    def test_wrong_suit_or_rank_is_wrong(self):
        for answer in ("AH", "2S", "S", "A", ""):
            with self.subTest(answer=answer):
                self.assertLess(self._pb("♠A").evaluate_solution(answer), 1.0)

    def test_every_generated_card_can_be_typed_in_ascii(self):
        letters = {"♠": "S", "♥": "H", "♣": "C", "♦": "D"}
        for seed in range(40):
            random.seed(seed)
            pb = PlayingCardSequence.create()
            ascii_answer = pb.solution[1:] + letters[pb.solution[0]]
            with self.subTest(solution=pb.solution):
                self.assertEqual(pb.evaluate_solution(ascii_answer), 1.0)


class TestMetar(unittest.TestCase):
    def _pb(self, solution, prompt="Wind speed (knots)?"):
        return Metar("Metar", "KJFK 010000Z 15005KT 10SM CLR M03/M08 A2992", prompt, solution, 6000)

    def test_wind_speed_as_shown_in_the_report(self):
        self.assertEqual(self._pb("5").evaluate_solution("05"), 1.0)
        self.assertEqual(self._pb("5").evaluate_solution("5"), 1.0)

    def test_negative_temperature_in_either_notation(self):
        pb = self._pb("-3", "Temperature (°C)?")
        self.assertEqual(pb.evaluate_solution("M03"), 1.0)
        self.assertEqual(pb.evaluate_solution("m3"), 1.0)
        self.assertEqual(pb.evaluate_solution("-3"), 1.0)
        self.assertLess(pb.evaluate_solution("3"), 1.0)

    def test_wind_direction_without_leading_zero(self):
        self.assertEqual(self._pb("050", "Wind direction?").evaluate_solution("50"), 1.0)

    def test_every_numeric_answer_can_be_copied_from_the_report(self):
        for seed in range(300):
            random.seed(seed)
            pb = Metar.create()
            tokens = pb.memorize.split()
            if pb.prompt.startswith("Wind speed"):
                shown = next(t for t in tokens if t.endswith("KT"))[3:5]
            elif pb.prompt.startswith("Temperature"):
                shown = next(t for t in tokens if "/" in t and not t.endswith("SM")).split("/")[0]
            else:
                continue
            with self.subTest(seed=seed, shown=shown, solution=pb.solution):
                self.assertEqual(pb.evaluate_solution(shown), 1.0)


if __name__ == "__main__":
    unittest.main()
