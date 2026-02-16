"""Unit tests for problem classes."""

import random
import unittest

from classes import Problem
from utils import format_problem_name
from problems import (
    WordList,
    WordPairs,
    WordNumberPairs,
    Number,
    NumberLong,
    NumberList,
    NumberCalculate,
    RandomLetters,
    RandomLettersAndNumbers,
    WordBackward,
    WordForward,
    ArrowDirection,
    GeometricForms,
    FlightInfo,
    TokyoMetro,
    Appointments,
    Anagram,
    SequenceRecognition,
    Metar,
    Atc,
    FlightPlan,
    Road,
    TimeDuration,
    ChemicalFormula,
    NBack,
    Sternberg,
    MatrixMemory,
    ShoppingList,
    ColorSequence,
    SentenceCompletion,
    NumberBackward,
    NameAttributePairs,
    create_problems_dict,
)


def _valid_problem(pb: Problem) -> bool:
    return (
        pb.name
        and pb.memorize is not None
        and pb.prompt is not None
        and pb.solution is not None
        and pb.exposure_ms > 0
    )


class TestProblemCreate(unittest.TestCase):
    """Test that each problem class create() returns a valid Problem."""

    def setUp(self):
        random.seed(42)

    def _test_create(self, cls):
        pb = cls.create()
        self.assertTrue(_valid_problem(pb))
        self.assertEqual(pb.to_dict()["name"], pb.name)
        self.assertEqual(pb.to_dict()["solution"], pb.solution)

    def test_word_list(self):
        self._test_create(WordList)

    def test_word_pairs(self):
        self._test_create(WordPairs)

    def test_word_number_pairs(self):
        self._test_create(WordNumberPairs)

    def test_number(self):
        self._test_create(Number)

    def test_number_long(self):
        self._test_create(NumberLong)

    def test_number_list(self):
        self._test_create(NumberList)

    def test_number_calculate(self):
        self._test_create(NumberCalculate)

    def test_random_letters(self):
        self._test_create(RandomLetters)

    def test_random_letters_and_numbers(self):
        self._test_create(RandomLettersAndNumbers)

    def test_word_backward(self):
        self._test_create(WordBackward)

    def test_word_forward(self):
        self._test_create(WordForward)

    def test_arrow_direction(self):
        self._test_create(ArrowDirection)

    def test_geometry_forms(self):
        self._test_create(GeometricForms)

    def test_appointments(self):
        self._test_create(Appointments)

    def test_flight_info(self):
        self._test_create(FlightInfo)

    def test_tokyo_metro(self):
        self._test_create(TokyoMetro)

    def test_anagram(self):
        self._test_create(Anagram)


    def test_sequence_recognition(self):
        self._test_create(SequenceRecognition)

    def test_metar(self):
        self._test_create(Metar)

    def test_atc(self):
        self._test_create(Atc)

    def test_flight_plan(self):
        self._test_create(FlightPlan)

    def test_road(self):
        self._test_create(Road)

    def test_time_duration(self):
        self._test_create(TimeDuration)

    def test_chemical_formula(self):
        self._test_create(ChemicalFormula)

    def test_nback(self):
        self._test_create(NBack)

    def test_sternberg(self):
        self._test_create(Sternberg)

    def test_matrix_memory(self):
        self._test_create(MatrixMemory)

    def test_shopping_list(self):
        self._test_create(ShoppingList)

    def test_color_sequence(self):
        self._test_create(ColorSequence)

    def test_sentence_completion(self):
        self._test_create(SentenceCompletion)

    def test_number_backward(self):
        self._test_create(NumberBackward)

    def test_name_attribute_pairs(self):
        self._test_create(NameAttributePairs)


class TestProblemEvaluateNone(unittest.TestCase):
    """Test evaluate_solution with None returns 0.0."""

    def setUp(self):
        random.seed(42)

    def test_word_list_none(self):
        self.assertEqual(WordList.create().evaluate_solution(None), 0.0)

    def test_number_none(self):
        self.assertEqual(Number.create().evaluate_solution(None), 0.0)

    def test_nback_none(self):
        self.assertEqual(NBack.create().evaluate_solution(None), 0.0)

    def test_sternberg_none(self):
        self.assertEqual(Sternberg.create().evaluate_solution(None), 0.0)

    def test_matrix_memory_none(self):
        self.assertEqual(MatrixMemory.create().evaluate_solution(None), 0.0)

    def test_color_sequence_none(self):
        self.assertEqual(ColorSequence.create().evaluate_solution(None), 0.0)

    def test_sentence_completion_none(self):
        self.assertEqual(SentenceCompletion.create().evaluate_solution(None), 0.0)

    def test_flight_info_none(self):
        self.assertEqual(FlightInfo.create(num_flights=1).evaluate_solution(None), 0.0)

    def test_metar_none(self):
        self.assertEqual(Metar.create().evaluate_solution(None), 0.0)

    def test_atc_none(self):
        self.assertEqual(Atc.create().evaluate_solution(None), 0.0)

    def test_word_pairs_none(self):
        self.assertEqual(WordPairs.create().evaluate_solution(None), 0.0)

    def test_word_number_pairs_none(self):
        self.assertEqual(WordNumberPairs.create().evaluate_solution(None), 0.0)

    def test_number_long_none(self):
        self.assertEqual(NumberLong.create().evaluate_solution(None), 0.0)

    def test_number_list_none(self):
        self.assertEqual(NumberList.create().evaluate_solution(None), 0.0)

    def test_number_calculate_none(self):
        self.assertEqual(NumberCalculate.create().evaluate_solution(None), 0.0)

    def test_random_letters_none(self):
        self.assertEqual(RandomLetters.create().evaluate_solution(None), 0.0)

    def test_random_letters_and_numbers_none(self):
        self.assertEqual(RandomLettersAndNumbers.create().evaluate_solution(None), 0.0)

    def test_word_backward_none(self):
        self.assertEqual(WordBackward.create().evaluate_solution(None), 0.0)

    def test_word_forward_none(self):
        self.assertEqual(WordForward.create().evaluate_solution(None), 0.0)

    def test_arrow_direction_none(self):
        self.assertEqual(ArrowDirection.create().evaluate_solution(None), 0.0)

    def test_geometric_forms_none(self):
        self.assertEqual(GeometricForms.create().evaluate_solution(None), 0.0)

    def test_tokyo_metro_none(self):
        self.assertEqual(TokyoMetro.create(num_stations=2).evaluate_solution(None), 0.0)

    def test_appointments_none(self):
        self.assertEqual(Appointments.create().evaluate_solution(None), 0.0)

    def test_anagram_none(self):
        self.assertEqual(Anagram.create().evaluate_solution(None), 0.0)

    def test_sequence_recognition_none(self):
        self.assertEqual(SequenceRecognition.create().evaluate_solution(None), 0.0)

    def test_flight_plan_none(self):
        self.assertEqual(FlightPlan.create(num_waypoints=2).evaluate_solution(None), 0.0)

    def test_road_none(self):
        self.assertEqual(Road.create().evaluate_solution(None), 0.0)

    def test_time_duration_none(self):
        self.assertEqual(TimeDuration.create().evaluate_solution(None), 0.0)

    def test_chemical_formula_none(self):
        self.assertEqual(ChemicalFormula.create().evaluate_solution(None), 0.0)

    def test_shopping_list_none(self):
        self.assertEqual(ShoppingList.create().evaluate_solution(None), 0.0)

    def test_number_backward_none(self):
        self.assertEqual(NumberBackward.create().evaluate_solution(None), 0.0)

    def test_name_attribute_pairs_none(self):
        self.assertEqual(NameAttributePairs.create().evaluate_solution(None), 0.0)


class TestProblemEvaluateCorrect(unittest.TestCase):
    """Test evaluate_solution with correct answer returns 1.0."""

    def test_number_problem_correct(self):
        random.seed(1)
        pb = Number.create(number_length=4)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_number_backward(self):
        pb = NumberBackward.create(number_length=4)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_nback_yes(self):
        pb = NBack("N Back", "1:A 2:B 3:A", "Position 3 matches 2? (yes/no)", "yes", 4000, "")
        self.assertEqual(pb.evaluate_solution("yes"), 1.0)
        self.assertEqual(pb.evaluate_solution("y"), 1.0)

    def test_nback_no(self):
        pb = NBack("N Back", "1:A 2:B 3:C", "Position 3 matches 2? (yes/no)", "no", 4000, "")
        self.assertEqual(pb.evaluate_solution("no"), 1.0)
        self.assertEqual(pb.evaluate_solution("n"), 1.0)

    def test_sternberg_yes(self):
        pb = Sternberg("Sternberg", "A B C", "Was 'A' in set? (yes/no)", "yes", 3500, "")
        self.assertEqual(pb.evaluate_solution("yes"), 1.0)

    def test_sternberg_no(self):
        pb = Sternberg("Sternberg", "A B C", "Was 'X' in set? (yes/no)", "no", 3500, "")
        self.assertEqual(pb.evaluate_solution("no"), 1.0)

    def test_matrix_memory_a1(self):
        pb = MatrixMemory("Matrix Memory", "X . .\n. . .\n. . .", "Which cell?", "A1", 3000, "")
        self.assertEqual(pb.evaluate_solution("A1"), 1.0)
        self.assertEqual(pb.evaluate_solution("1A"), 1.0)

    def test_color_sequence_single(self):
        pb = ColorSequence("Color Sequence", "R G B", "Color at 1?", "R", 3000, "")
        self.assertEqual(pb.evaluate_solution("R"), 1.0)
        self.assertEqual(pb.evaluate_solution("red"), 1.0)

    def test_color_sequence_full(self):
        pb = ColorSequence("Color Sequence", "R G B", "Full sequence?", "R G B", 3000, "")
        self.assertEqual(pb.evaluate_solution("R G B"), 1.0)

    def test_sentence_completion(self):
        pb = SentenceCompletion(
            "Sentence Completion", "The cat sat on the mat", "The cat sat on the ___", "mat", 4000, ""
        )
        self.assertEqual(pb.evaluate_solution("mat"), 1.0)
        self.assertEqual(pb.evaluate_solution("MAT"), 1.0)
        self.assertEqual(pb.evaluate_solution("Mat"), 1.0)

    def test_chemical_formula(self):
        pb = ChemicalFormula("Chemical Formula", "Chemical: Water", "Formula?", "H2O", 4000, "")
        self.assertEqual(pb.evaluate_solution("H2O"), 1.0)

    def test_flight_info_correct(self):
        pb = FlightInfo.create(num_flights=1)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_tokyo_metro_correct(self):
        pb = TokyoMetro.create(num_stations=2)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_metar_correct(self):
        pb = Metar.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_atc_correct(self):
        pb = Atc.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_flight_plan_correct(self):
        pb = FlightPlan.create(num_waypoints=2)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_road_correct(self):
        pb = Road.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_word_list_correct(self):
        pb = WordList.create(num_words=3)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_word_pairs_correct(self):
        pb = WordPairs.create(num_pairs=2)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_arrow_direction_correct(self):
        pb = ArrowDirection.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_geometry_forms_correct(self):
        pb = GeometricForms.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_appointments_correct(self):
        pb = Appointments.create(num_appointments=2)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_sequence_recognition_correct(self):
        pb = SequenceRecognition.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_sequence_recognition_various_generators(self):
        """Run create() with many seeds to hit different sequence generators."""
        for seed in range(50):
            random.seed(seed)
            pb = SequenceRecognition.create()
            self.assertTrue(_valid_problem(pb))
            self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_time_duration_correct(self):
        pb = TimeDuration.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_shopping_list_correct(self):
        pb = ShoppingList.create(num_items=3)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_name_attribute_pairs_correct(self):
        pb = NameAttributePairs.create(num_pairs=2)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_word_number_pairs_correct(self):
        pb = WordNumberPairs.create(num_pairs=2)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_number_long_correct(self):
        pb = NumberLong.create(number_length=6)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_number_list_correct(self):
        pb = NumberList.create(num_numbers=3)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_number_calculate_correct(self):
        pb = NumberCalculate.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_random_letters_correct(self):
        pb = RandomLetters.create(num_letters=6)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_random_letters_and_numbers_correct(self):
        pb = RandomLettersAndNumbers.create(size=6)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_word_backward_correct(self):
        pb = WordBackward.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_word_forward_correct(self):
        pb = WordForward.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_anagram_correct(self):
        pb = Anagram.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)


class TestProblemEvaluateIncorrect(unittest.TestCase):
    """Test evaluate_solution with wrong answer returns < 1.0."""

    def test_nback_wrong_answer(self):
        pb = NBack("N Back", "1:A 2:B 3:A", "Position 3 matches 2? (yes/no)", "yes", 4000, "")
        self.assertEqual(pb.evaluate_solution("no"), 0.0)

    def test_sternberg_wrong_answer(self):
        pb = Sternberg("Sternberg", "A B C", "Was 'A' in set? (yes/no)", "yes", 3500, "")
        self.assertEqual(pb.evaluate_solution("no"), 0.0)

    def test_matrix_memory_wrong(self):
        pb = MatrixMemory("Matrix Memory", "X . .\n. . .\n. . .", "Which cell?", "A1", 3000, "")
        self.assertLess(pb.evaluate_solution("B2"), 1.0)

    def test_levenshtein_partial(self):
        pb = Problem("test", "abc", "?", "abcdef", 1000, "")
        score = pb.evaluate_solution("abcde")
        self.assertGreater(score, 0)
        self.assertLess(score, 1.0)

    def test_flight_info_wrong(self):
        pb = FlightInfo.create(num_flights=1)
        self.assertLess(pb.evaluate_solution("wrong answer"), 1.0)

    def test_metar_wrong(self):
        pb = Metar.create()
        self.assertLess(pb.evaluate_solution("wrong"), 1.0)

    def test_word_list_wrong(self):
        pb = WordList.create(num_words=3)
        self.assertLess(pb.evaluate_solution("wrong answer"), 1.0)

    def test_word_pairs_wrong(self):
        pb = WordPairs.create(num_pairs=2)
        self.assertLess(pb.evaluate_solution("wrong"), 1.0)

    def test_word_number_pairs_wrong(self):
        pb = WordNumberPairs.create(num_pairs=2)
        self.assertLess(pb.evaluate_solution("wrong"), 1.0)

    def test_number_wrong(self):
        pb = Number.create(number_length=4)
        self.assertLess(pb.evaluate_solution("9999"), 1.0)

    def test_number_long_wrong(self):
        pb = NumberLong.create(number_length=6)
        self.assertLess(pb.evaluate_solution("000000"), 1.0)

    def test_number_list_wrong(self):
        pb = NumberList.create(num_numbers=3)
        self.assertLess(pb.evaluate_solution("11 22 99"), 1.0)

    def test_number_calculate_wrong(self):
        pb = NumberCalculate.create()
        self.assertLess(pb.evaluate_solution("999"), 1.0)

    def test_random_letters_wrong(self):
        pb = RandomLetters.create(num_letters=6)
        self.assertLess(pb.evaluate_solution("xxxxxx"), 1.0)

    def test_random_letters_and_numbers_wrong(self):
        pb = RandomLettersAndNumbers.create(size=6)
        self.assertLess(pb.evaluate_solution("000000"), 1.0)

    def test_word_backward_wrong(self):
        pb = WordBackward.create()
        self.assertLess(pb.evaluate_solution("wrong"), 1.0)

    def test_word_forward_wrong(self):
        pb = WordForward.create()
        self.assertLess(pb.evaluate_solution("wrong"), 1.0)

    def test_arrow_direction_wrong(self):
        pb = ArrowDirection.create()
        self.assertLess(pb.evaluate_solution("wrong"), 1.0)

    def test_geometric_forms_wrong(self):
        pb = GeometricForms.create()
        self.assertLess(pb.evaluate_solution("wrong"), 1.0)

    def test_tokyo_metro_wrong(self):
        pb = TokyoMetro.create(num_stations=2)
        self.assertLess(pb.evaluate_solution("wrong"), 1.0)

    def test_appointments_wrong(self):
        pb = Appointments.create(num_appointments=2)
        self.assertLess(pb.evaluate_solution("wrong"), 1.0)

    def test_anagram_wrong(self):
        pb = Anagram.create()
        self.assertLess(pb.evaluate_solution("wrong"), 1.0)

    def test_sequence_recognition_wrong(self):
        pb = SequenceRecognition.create()
        self.assertLess(pb.evaluate_solution("999"), 1.0)

    def test_flight_plan_wrong(self):
        pb = FlightPlan.create(num_waypoints=2)
        self.assertLess(pb.evaluate_solution("wrong"), 1.0)

    def test_road_wrong(self):
        pb = Road.create()
        self.assertLess(pb.evaluate_solution("wrong"), 1.0)

    def test_time_duration_wrong(self):
        pb = TimeDuration.create()
        self.assertLess(pb.evaluate_solution("99:99"), 1.0)

    def test_chemical_formula_wrong(self):
        pb = ChemicalFormula.create()
        self.assertLess(pb.evaluate_solution("wrong"), 1.0)

    def test_shopping_list_wrong(self):
        pb = ShoppingList.create(num_items=3)
        self.assertLess(pb.evaluate_solution("wrong"), 1.0)

    def test_color_sequence_wrong(self):
        pb = ColorSequence.create()
        self.assertLess(pb.evaluate_solution("wrong"), 1.0)

    def test_sentence_completion_wrong(self):
        pb = SentenceCompletion("Sentence Completion", "The cat sat on the mat", "The cat sat on the ___", "mat", 4000, "")
        self.assertLess(pb.evaluate_solution("wrong"), 1.0)

    def test_number_backward_wrong(self):
        pb = NumberBackward.create(number_length=4)
        self.assertLess(pb.evaluate_solution("0000"), 1.0)

    def test_name_attribute_pairs_wrong(self):
        pb = NameAttributePairs.create(num_pairs=2)
        self.assertLess(pb.evaluate_solution("wrong"), 1.0)


class TestUtils(unittest.TestCase):
    """Test utils module for coverage."""

    def test_levenshtein_distance(self):
        from utils import levenshtein_distance
        self.assertEqual(levenshtein_distance("", ""), 0)
        self.assertEqual(levenshtein_distance("a", "a"), 0)
        self.assertEqual(levenshtein_distance("kitten", "sitting"), 3)
        self.assertEqual(levenshtein_distance("abc", "abcd"), 1)

    def test_load_frequencies(self):
        from utils import load_frequencies
        freqs = load_frequencies()
        self.assertIn("approach", freqs)
        self.assertIn("tower", freqs)
        self.assertIn("ground", freqs)
        self.assertIsInstance(freqs["approach"], list)
        self.assertGreater(len(freqs["approach"]), 0)

    def test_rnd_number(self):
        from utils import rnd_number
        num = rnd_number(6)
        self.assertEqual(len(num), 6)
        self.assertTrue(num.isdigit())


class TestCreateProblemsDict(unittest.TestCase):
    """Test create_problems_dict and format_problem_name."""

    def test_create_problems_dict_returns_dict(self):
        d = create_problems_dict()
        self.assertIsInstance(d, dict)
        self.assertGreater(len(d), 0)
        for cls, prob in d.items():
            self.assertGreater(prob, 0)
            self.assertLessEqual(prob, 1.0)

    def test_format_problem_name(self):
        self.assertEqual(format_problem_name("WordList"), "Word List")
        self.assertEqual(format_problem_name("NBack"), "N Back")


if __name__ == "__main__":
    unittest.main()
