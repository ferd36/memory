"""Unit tests for problem classes."""

import random
import unittest

from classes import Problem
from problems import (
    WordListProblem,
    WordPairsProblem,
    WordNumberPairsProblem,
    NumberProblem,
    NumberLongProblem,
    NumberListProblem,
    NumberCalculateProblem,
    RandomLettersProblem,
    RandomLettersAndNumbersProblem,
    WordBackwardProblem,
    WordForwardProblem,
    ArrowDirectionProblem,
    GeometryFormsProblem,
    FlightInfoProblem,
    TokyoMetroProblem,
    AppointmentsProblem,
    AnagramProblem,
    SequenceRecognitionProblem,
    MetarProblem,
    AtcProblem,
    FlightPlanProblem,
    RoadProblem,
    TimeDurationProblem,
    ChemicalFormulaProblem,
    NBackProblem,
    SternbergProblem,
    MatrixMemoryProblem,
    ShoppingListProblem,
    ColorSequenceProblem,
    SentenceCompletionProblem,
    NumberBackwardProblem,
    NameAttributePairsProblem,
    create_problems_dict,
    format_problem_name,
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
        self._test_create(WordListProblem)

    def test_word_pairs(self):
        self._test_create(WordPairsProblem)

    def test_word_number_pairs(self):
        self._test_create(WordNumberPairsProblem)

    def test_number(self):
        self._test_create(NumberProblem)

    def test_number_long(self):
        self._test_create(NumberLongProblem)

    def test_number_list(self):
        self._test_create(NumberListProblem)

    def test_number_calculate(self):
        self._test_create(NumberCalculateProblem)

    def test_random_letters(self):
        self._test_create(RandomLettersProblem)

    def test_random_letters_and_numbers(self):
        self._test_create(RandomLettersAndNumbersProblem)

    def test_word_backward(self):
        self._test_create(WordBackwardProblem)

    def test_word_forward(self):
        self._test_create(WordForwardProblem)

    def test_arrow_direction(self):
        self._test_create(ArrowDirectionProblem)

    def test_geometry_forms(self):
        self._test_create(GeometryFormsProblem)

    def test_appointments(self):
        self._test_create(AppointmentsProblem)

    def test_flight_info(self):
        self._test_create(FlightInfoProblem)

    def test_tokyo_metro(self):
        self._test_create(TokyoMetroProblem)

    def test_anagram(self):
        self._test_create(AnagramProblem)


    def test_sequence_recognition(self):
        self._test_create(SequenceRecognitionProblem)

    def test_metar(self):
        self._test_create(MetarProblem)

    def test_atc(self):
        self._test_create(AtcProblem)

    def test_flight_plan(self):
        self._test_create(FlightPlanProblem)

    def test_road(self):
        self._test_create(RoadProblem)

    def test_time_duration(self):
        self._test_create(TimeDurationProblem)

    def test_chemical_formula(self):
        self._test_create(ChemicalFormulaProblem)

    def test_nback(self):
        self._test_create(NBackProblem)

    def test_sternberg(self):
        self._test_create(SternbergProblem)

    def test_matrix_memory(self):
        self._test_create(MatrixMemoryProblem)

    def test_shopping_list(self):
        self._test_create(ShoppingListProblem)

    def test_color_sequence(self):
        self._test_create(ColorSequenceProblem)

    def test_sentence_completion(self):
        self._test_create(SentenceCompletionProblem)

    def test_number_backward(self):
        self._test_create(NumberBackwardProblem)

    def test_name_attribute_pairs(self):
        self._test_create(NameAttributePairsProblem)


class TestProblemEvaluateNone(unittest.TestCase):
    """Test evaluate_solution with None returns 0.0."""

    def setUp(self):
        random.seed(42)

    def test_word_list_none(self):
        self.assertEqual(WordListProblem.create().evaluate_solution(None), 0.0)

    def test_number_none(self):
        self.assertEqual(NumberProblem.create().evaluate_solution(None), 0.0)

    def test_nback_none(self):
        self.assertEqual(NBackProblem.create().evaluate_solution(None), 0.0)

    def test_sternberg_none(self):
        self.assertEqual(SternbergProblem.create().evaluate_solution(None), 0.0)

    def test_matrix_memory_none(self):
        self.assertEqual(MatrixMemoryProblem.create().evaluate_solution(None), 0.0)

    def test_color_sequence_none(self):
        self.assertEqual(ColorSequenceProblem.create().evaluate_solution(None), 0.0)

    def test_sentence_completion_none(self):
        self.assertEqual(SentenceCompletionProblem.create().evaluate_solution(None), 0.0)

    def test_flight_info_none(self):
        self.assertEqual(FlightInfoProblem.create(num_flights=1).evaluate_solution(None), 0.0)

    def test_metar_none(self):
        self.assertEqual(MetarProblem.create().evaluate_solution(None), 0.0)

    def test_atc_none(self):
        self.assertEqual(AtcProblem.create().evaluate_solution(None), 0.0)


class TestProblemEvaluateCorrect(unittest.TestCase):
    """Test evaluate_solution with correct answer returns 1.0."""

    def test_number_problem_correct(self):
        random.seed(1)
        pb = NumberProblem.create(number_length=4)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_number_backward(self):
        pb = NumberBackwardProblem.create(number_length=4)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_nback_yes(self):
        pb = NBackProblem("n back", "1:A 2:B 3:A", "Position 3 matches 2? (yes/no)", "yes", 4000, "")
        self.assertEqual(pb.evaluate_solution("yes"), 1.0)
        self.assertEqual(pb.evaluate_solution("y"), 1.0)

    def test_nback_no(self):
        pb = NBackProblem("n back", "1:A 2:B 3:C", "Position 3 matches 2? (yes/no)", "no", 4000, "")
        self.assertEqual(pb.evaluate_solution("no"), 1.0)
        self.assertEqual(pb.evaluate_solution("n"), 1.0)

    def test_sternberg_yes(self):
        pb = SternbergProblem("sternberg", "A B C", "Was 'A' in set? (yes/no)", "yes", 3500, "")
        self.assertEqual(pb.evaluate_solution("yes"), 1.0)

    def test_sternberg_no(self):
        pb = SternbergProblem("sternberg", "A B C", "Was 'X' in set? (yes/no)", "no", 3500, "")
        self.assertEqual(pb.evaluate_solution("no"), 1.0)

    def test_matrix_memory_a1(self):
        pb = MatrixMemoryProblem("matrix memory", "X . .\n. . .\n. . .", "Which cell?", "A1", 3000, "")
        self.assertEqual(pb.evaluate_solution("A1"), 1.0)
        self.assertEqual(pb.evaluate_solution("1A"), 1.0)

    def test_color_sequence_single(self):
        pb = ColorSequenceProblem("color sequence", "R G B", "Color at 1?", "R", 3000, "")
        self.assertEqual(pb.evaluate_solution("R"), 1.0)
        self.assertEqual(pb.evaluate_solution("red"), 1.0)

    def test_color_sequence_full(self):
        pb = ColorSequenceProblem("color sequence", "R G B", "Full sequence?", "R G B", 3000, "")
        self.assertEqual(pb.evaluate_solution("R G B"), 1.0)

    def test_sentence_completion(self):
        pb = SentenceCompletionProblem(
            "sentence completion", "The cat sat on the mat", "The cat sat on the ___", "mat", 4000, ""
        )
        self.assertEqual(pb.evaluate_solution("mat"), 1.0)

    def test_chemical_formula(self):
        pb = ChemicalFormulaProblem("chemical formula", "Chemical: Water", "Formula?", "H2O", 4000, "")
        self.assertEqual(pb.evaluate_solution("H2O"), 1.0)

    def test_flight_info_correct(self):
        pb = FlightInfoProblem.create(num_flights=1)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_tokyo_metro_correct(self):
        pb = TokyoMetroProblem.create(num_stations=2)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_metar_correct(self):
        pb = MetarProblem.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_atc_correct(self):
        pb = AtcProblem.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_flight_plan_correct(self):
        pb = FlightPlanProblem.create(num_waypoints=2)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_road_correct(self):
        pb = RoadProblem.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_word_list_correct(self):
        pb = WordListProblem.create(num_words=3)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_word_pairs_correct(self):
        pb = WordPairsProblem.create(num_pairs=2)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_arrow_direction_correct(self):
        pb = ArrowDirectionProblem.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_geometry_forms_correct(self):
        pb = GeometryFormsProblem.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_appointments_correct(self):
        pb = AppointmentsProblem.create(num_appointments=2)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_sequence_recognition_correct(self):
        pb = SequenceRecognitionProblem.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_sequence_recognition_various_generators(self):
        """Run create() with many seeds to hit different sequence generators."""
        for seed in range(50):
            random.seed(seed)
            pb = SequenceRecognitionProblem.create()
            self.assertTrue(_valid_problem(pb))
            self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_time_duration_correct(self):
        pb = TimeDurationProblem.create()
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_shopping_list_correct(self):
        pb = ShoppingListProblem.create(num_items=3)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)

    def test_name_attribute_pairs_correct(self):
        pb = NameAttributePairsProblem.create(num_pairs=2)
        self.assertEqual(pb.evaluate_solution(pb.solution), 1.0)


class TestProblemEvaluateIncorrect(unittest.TestCase):
    """Test evaluate_solution with wrong answer returns < 1.0."""

    def test_nback_wrong_answer(self):
        pb = NBackProblem("n back", "1:A 2:B 3:A", "Position 3 matches 2? (yes/no)", "yes", 4000, "")
        self.assertEqual(pb.evaluate_solution("no"), 0.0)

    def test_sternberg_wrong_answer(self):
        pb = SternbergProblem("sternberg", "A B C", "Was 'A' in set? (yes/no)", "yes", 3500, "")
        self.assertEqual(pb.evaluate_solution("no"), 0.0)

    def test_matrix_memory_wrong(self):
        pb = MatrixMemoryProblem("matrix memory", "X . .\n. . .\n. . .", "Which cell?", "A1", 3000, "")
        self.assertLess(pb.evaluate_solution("B2"), 1.0)

    def test_levenshtein_partial(self):
        pb = Problem("test", "abc", "?", "abcdef", 1000, "")
        score = pb.evaluate_solution("abcde")
        self.assertGreater(score, 0)
        self.assertLess(score, 1.0)

    def test_flight_info_wrong(self):
        pb = FlightInfoProblem.create(num_flights=1)
        self.assertLess(pb.evaluate_solution("wrong answer"), 1.0)

    def test_metar_wrong(self):
        pb = MetarProblem.create()
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
        self.assertEqual(format_problem_name("WordListProblem"), "Word List")
        self.assertEqual(format_problem_name("NBackProblem"), "N Back")


if __name__ == "__main__":
    unittest.main()
