"""Generation regressions: problems whose prompt or solution did not match what
was shown."""

import json
import random
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import problems
import utils
from problems import (
    Atc,
    FlightInfo,
    FlightPlan,
    SentenceCompletion,
    TimeDuration,
    TwoBackRecall,
)


class TestSentenceCompletionBlank(unittest.TestCase):
    HEADLINE = "What the Fed said at the meeting on rates"

    def _create_many(self, headline, seeds=200):
        with patch.object(problems, "fetch_gnews_headlines", return_value=[headline]), \
                patch.object(problems, "used_headlines", return_value=set()), \
                patch.object(problems, "mark_headline_used"):
            for seed in range(seeds):
                random.seed(seed)
                yield SentenceCompletion.create()

    def test_the_blank_replaces_whole_words_only(self):
        # "at" used to be blanked inside "What": "Wh___ the Fed said at ...".
        for pb in self._create_many(self.HEADLINE):
            with self.subTest(prompt=pb.prompt, solution=pb.solution):
                self.assertIn("___", pb.prompt.split())
                self.assertEqual(pb.prompt.replace("___", pb.solution, 1), self.HEADLINE)

    def test_punctuated_words_are_blanked_as_a_whole(self):
        headline = "Markets: stocks rally, oil's price falls again"
        for pb in self._create_many(headline):
            with self.subTest(prompt=pb.prompt, solution=pb.solution):
                self.assertIn("___", pb.prompt.split())
                self.assertEqual(pb.prompt.replace("___", pb.solution, 1), headline)


class TestFlightPlanFields(unittest.TestCase):
    def setUp(self):
        saved = FlightPlan._vors
        self.addCleanup(setattr, FlightPlan, "_vors", saved)

    def test_a_vor_name_with_a_space_does_not_shift_the_fields(self):
        # dicts/vors.txt contains "RDU GKA".
        FlightPlan._vors = ["RDU GKA"]
        expected = {
            "VOR": lambda s: s == "RDU GKA",
            "Heading": lambda s: re.fullmatch(r"\d{3}", s),
            "Altitude": lambda s: re.fullmatch(r"\d+", s),
            "Frequency": lambda s: re.fullmatch(r"\d+(\.\d+)?", s),
            "Contact": lambda s: s in ("Approach", "Tower", "Ground"),
        }
        seen = set()
        for seed in range(200):
            random.seed(seed)
            pb = FlightPlan.create(num_waypoints=1)
            aspect = pb.prompt.split()[0]
            seen.add(aspect)
            with self.subTest(prompt=pb.prompt, solution=pb.solution):
                self.assertTrue(expected[aspect](pb.solution))
        self.assertEqual(seen, set(expected))


class TestTimeDuration(unittest.TestCase):
    @staticmethod
    def _minutes(hhmm):
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)

    def test_duration_is_positive_and_consistent(self):
        # A start time of 23:59 gave an end time of 23:59 and a duration of 00:00.
        for seed in range(20000):
            random.seed(seed)
            pb = TimeDuration.create()
            parts = dict(p.split(": ") for p in pb.memorize.split(" | "))
            if pb.prompt.startswith("Duration"):
                parts["Duration"] = pb.solution
            elif pb.prompt.startswith("Start"):
                parts["Start"] = pb.solution
            else:
                parts["End"] = pb.solution
            start, end, duration = (self._minutes(parts[k]) for k in ("Start", "End", "Duration"))
            with self.subTest(seed=seed, parts=parts):
                self.assertGreater(duration, 0)
                self.assertEqual(start + duration, end)
                self.assertLess(end, 24 * 60)


class TestHeadlinesAcrossProcesses(unittest.TestCase):
    """The Electron app starts a new process for each round."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        patcher = patch.object(utils, "_HEADLINE_CACHE_FILE", Path(directory.name) / "headlines.json")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_used_headline_is_not_shown_again(self):
        headlines = ["One Two Three Four", "Five Six Seven Eight"]
        with patch.object(problems, "fetch_gnews_headlines", return_value=headlines):
            shown = [SentenceCompletion.create().memorize for _ in range(3)]
        self.assertCountEqual(shown[:2], headlines)
        self.assertNotIn(shown[2], headlines)  # A fallback template.


class TestTwoBackHistoryFile(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "memory_twoback.json"
        patcher = patch.object(tempfile, "gettempdir", return_value=directory.name)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_valid_json_that_is_not_a_list_starts_a_new_history(self):
        for content in ("null", "{}", "5", '"text"'):
            with self.subTest(content=content):
                self.path.write_text(content, encoding="utf-8")
                pb = TwoBackRecall.create(round_num=2)
                self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), [pb.memorize])

    def test_the_prompt_says_that_rounds_of_other_games_do_not_count(self):
        for round_num in (1, 2):
            TwoBackRecall.create(round_num=round_num)
        self.assertIn("in this game", TwoBackRecall.create(round_num=3).prompt)


class TestAirlineCodes(unittest.TestCase):
    def test_invalid_codes_in_the_file_are_not_used(self):
        codes = utils.load_airline_codes()
        self.assertGreater(len(codes), 900)
        self.assertEqual([c for c in codes if not c.isalnum()], [])

    def test_flight_info_and_atc_use_only_valid_codes(self):
        with patch.object(problems, "load_airline_codes", return_value=["AA"]), \
                patch.object(Atc, "_airlines", None):
            self.assertTrue(FlightInfo.create().solution.startswith("AA "))
            Atc.create()
            self.assertEqual(Atc._airlines, ["AA"])


if __name__ == "__main__":
    unittest.main()
