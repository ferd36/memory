"""Terminal trainer regressions."""

import contextlib
import curses
import io
import itertools
import unittest
from unittest.mock import DEFAULT, patch

import trainer
from problems import Number, TwoBackRecall


class TestRoundNumbers(unittest.TestCase):
    def test_two_back_recall_is_scored_after_two_warmups(self):
        # create() was called without round_num, so every round was round 1:
        # the history reset each time and no round was ever scored.
        rounds_played = {}
        flags = [trainer.create_next_problem(TwoBackRecall, rounds_played).is_scored
                 for _ in range(4)]
        self.assertEqual(flags, [False, False, True, True])

    def test_other_games_do_not_advance_the_two_back_round(self):
        rounds_played = {}
        flags = []
        for _ in range(3):
            flags.append(trainer.create_next_problem(TwoBackRecall, rounds_played).is_scored)
            trainer.create_next_problem(Number, rounds_played)
        self.assertEqual(flags, [False, False, True])
        self.assertEqual(rounds_played, {TwoBackRecall: 3, Number: 3})


class FakeScreen:
    """A curses window that fails outside its bounds, as a real window does.

    `buffered` holds keys typed before the response phase. `keys` holds keys
    typed during it; a (height, width) tuple is a terminal resize.
    """

    def __init__(self, height=24, width=80, keys="", buffered=""):
        self.height, self.width = height, width
        self.keys = list(keys)
        self.buffered = list(buffered)
        self.drawn = []

    def getmaxyx(self):
        return self.height, self.width

    def getch(self):
        if self.buffered:
            return ord(self.buffered.pop(0))
        if not self.keys:
            return 10  # Enter, so that a test always ends.
        key = self.keys.pop(0)
        if isinstance(key, tuple):
            self.height, self.width = key
            return curses.KEY_RESIZE
        return key if isinstance(key, int) else ord(key)

    def move(self, y, x):
        if not (0 <= y < self.height and 0 <= x < self.width):
            raise curses.error("wmove() returned ERR")

    def addstr(self, y, x, text, *_attr):
        self.move(y, x)
        self.drawn.append(text)
        if y == self.height - 1 and x + len(text) >= self.width:
            raise curses.error("addwstr() returned ERR")

    def addch(self, y, x, ch, *_attr):
        self.addstr(y, x, chr(ch))

    def clear(self):
        pass

    def clrtoeol(self):
        pass

    def refresh(self):
        pass

    def timeout(self, _delay):
        pass


def respond(screen):
    """Run the response phase on a fake screen and return the typed answer."""
    with patch.object(trainer.curses, "color_pair", return_value=0), \
            patch.object(trainer.curses, "flushinp", screen.buffered.clear):
        answer, _ = trainer.display_response_phase(screen, "▶", 1, 5, 0.0, 0, 0.0)
    return answer


class TestResponsePhaseOnAnyScreen(unittest.TestCase):
    """A curses error ended the session and lost every answer."""

    def test_an_answer_wider_than_the_terminal(self):
        self.assertEqual(respond(FakeScreen(keys="a" * 70)), "a" * 70)

    def test_a_backspace_on_an_answer_wider_than_the_terminal(self):
        self.assertEqual(respond(FakeScreen(keys="a" * 70 + "\x7f")), "a" * 69)

    def test_a_very_small_terminal(self):
        for height, width in ((1, 1), (3, 10), (6, 80), (24, 8)):
            with self.subTest(height=height, width=width):
                self.assertEqual(respond(FakeScreen(height, width, keys="abc")), "abc")

    def test_a_terminal_that_shrinks_during_the_answer(self):
        self.assertEqual(respond(FakeScreen(keys=["a", (10, 80), "b", (3, 10), "c"])), "abc")


class TestKeysFromTheMemorizePhase(unittest.TestCase):
    def test_keys_typed_before_the_response_phase_are_discarded(self):
        self.assertEqual(respond(FakeScreen(buffered="leak", keys="ok")), "ok")

    def test_enter_typed_before_the_response_phase_does_not_submit(self):
        self.assertEqual(respond(FakeScreen(buffered="\n", keys="ok")), "ok")


class TestFeedbackPhase(unittest.TestCase):
    def _show(self, screen, score, solution="Alice"):
        # Each read of the clock advances one second.
        with patch.object(trainer.curses, "color_pair", return_value=0), \
                patch.object(trainer.curses, "flushinp", screen.buffered.clear), \
                patch.object(trainer.time, "time", side_effect=itertools.count()):
            trainer.display_feedback_phase(screen, score, solution, "alice", 10, 4000)

    def test_a_multiline_solution_stays_on_one_line(self):
        # A newline moved the cursor, so the other lines overwrote the timings.
        screen = FakeScreen(keys=" ")
        self._show(screen, 0.5, "Alice\nBob")
        self.assertIn("Correct answer: Alice Bob", screen.drawn)

    def test_a_wrong_answer_stays_until_a_key_press(self):
        # The screen closed after 0.5 s, so the correct answer was hard to read.
        for score in (0.0, 0.8):
            with self.subTest(score=score):
                screen = FakeScreen(keys=[-1] * 5 + ["x", -1, " "])
                self._show(screen, score)
                self.assertEqual(screen.keys, [])
                self.assertTrue(any("to continue" in text for text in screen.drawn))

    def test_enter_also_closes_a_wrong_answer(self):
        screen = FakeScreen(keys=[-1, "\n", -1])
        self._show(screen, 0.0)
        self.assertEqual(screen.keys, [-1])

    def test_a_correct_answer_closes_without_a_key_press(self):
        screen = FakeScreen(keys=[-1] * 5)
        self._show(screen, 1.0)
        self.assertGreater(len(screen.keys), 0)

    def test_a_held_enter_does_not_close_a_wrong_answer(self):
        screen = FakeScreen(buffered="\n\n", keys=[-1, " "])
        self._show(screen, 0.0)
        self.assertEqual(screen.keys, [])

    def test_a_resize_does_not_close_a_wrong_answer(self):
        screen = FakeScreen(keys=[(10, 80), -1, " "])
        self._show(screen, 0.0)
        self.assertEqual(screen.keys, [])


class TestPerformanceNames(unittest.TestCase):
    def test_a_game_that_only_the_history_knows_is_listed(self):
        # Records of the old "Chemical Formula" game were left out of the table.
        names = trainer.performance_names(["Number", "Word List"], {"Chemical Formula": {}, "Number": {}})
        self.assertEqual(names, ["Chemical Formula", "Number", "Word List"])

    def test_a_lower_case_name_in_the_history_is_not_listed_twice(self):
        names = trainer.performance_names(["Word List"], {"word list": {}})
        self.assertEqual(names, ["Word List"])


class AlwaysCorrect(Number):
    def evaluate_solution(self, user_input):
        return 1.0


class TestSessionTotals(unittest.TestCase):
    def _run_main(self, feedback=None, response=None, statistics=None):
        """Run a session. Returns (saved sessions, printed text, raised error)."""
        saved = []

        def save(_date, _start, total, perfect, records):
            saved.append((total, perfect, len(records)))

        output = io.StringIO()
        error = None
        with patch.multiple(trainer.curses, endwin=DEFAULT, start_color=DEFAULT,
                            use_default_colors=DEFAULT, init_pair=DEFAULT, curs_set=DEFAULT,
                            color_pair=DEFAULT, reset_shell_mode=DEFAULT, napms=DEFAULT), \
                patch.multiple(trainer, display_memorize_phase=DEFAULT, save_session_data=save,
                               load_session_statistics=lambda: statistics or {"total_sessions": 0},
                               display_response_phase=response or (lambda *a: ("x", 10)),
                               display_feedback_phase=feedback or (lambda *a: None)), \
                patch("builtins.input", return_value=""), \
                contextlib.redirect_stdout(output):
            try:
                trainer.main(FakeScreen(), 5, {AlwaysCorrect: 1.0})
            except curses.error as e:
                error = e
        return saved, output.getvalue(), error

    @staticmethod
    def _interrupt_on_call(number):
        calls = []

        def interrupt(*_args):
            calls.append(1)
            if len(calls) == number:
                raise KeyboardInterrupt

        return interrupt

    def test_ctrl_c_on_the_first_feedback_screen_keeps_the_answer(self):
        saved, text, _ = self._run_main(feedback=self._interrupt_on_call(1))
        self.assertEqual(saved, [(1, 1, 1)])
        self.assertNotIn("No questions answered", text)

    def test_ctrl_c_on_a_later_feedback_screen_keeps_the_totals_equal(self):
        saved, text, _ = self._run_main(feedback=self._interrupt_on_call(2))
        self.assertEqual(saved, [(2, 2, 2)])
        self.assertIn("Final score: 100.0%", text)
        self.assertNotIn("200.0%", text)

    def test_a_best_session_without_a_date_or_problem_can_be_printed(self):
        statistics = {
            "total_sessions": 1, "total_questions": 1, "overall_average_score": 50.0,
            "recent_average": 50.0, "problem_name_stats": {},
            "best_session": {"score_percentage": 50.0, "records": [{"problem": None}]},
        }
        _, text, _ = self._run_main(feedback=self._interrupt_on_call(1), statistics=statistics)
        self.assertIn("Best session: 50.0% on unknown date", text)

    def test_a_curses_error_during_the_session_keeps_the_answers(self):
        calls = []

        def response(*_args):
            calls.append(1)
            if len(calls) == 2:
                raise curses.error("wmove() returned ERR")
            return "x", 10

        saved, _, error = self._run_main(response=response)
        self.assertIsNotNone(error)
        self.assertEqual(saved, [(1, 1, 1)])


if __name__ == "__main__":
    unittest.main()
