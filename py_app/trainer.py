#!/usr/bin/env python3
"""Full-screen memory trainer with countdown timers."""

import argparse
import curses
import datetime
import os
import random
import sys
import time

from classes import Record
from problems import create_problems_dict
from sessions import format_score, load_session_statistics, save_session_data

checkmark = "\u2713"  # ✓
cross = "\u2717"  # ✗

CORRECT_FEEDBACK_S = 0.5  # A wrong answer stays until a key press.

records: list[Record] = []
all_problems = create_problems_dict()


def select_problems_interactively():
    """Show numbered problems and let user select which ones to use."""
    problems = all_problems
    problem_list = sorted(problems.keys(), key=lambda x: x.__name__)

    print("MEMORY TRAINER")
    print("=" * 55)
    print()
    print("Available problem types:")
    max_num_width = len(str(len(problem_list)))
    for i, cls in enumerate(problem_list, 1):
        formatted_name = cls.display_name()
        print(f"  {i:>{max_num_width}}. {formatted_name}")

    print("\nModes:")
    print("  p. Pick 1 for me (randomly selects one game, continues until you stop)")
    print("  r. Random each (changes game on each turn, continues until you stop)")
    print("\nOr enter problem numbers separated by spaces (e.g., '1 3 5')")
    print("Press Enter to select all problems (uses default question count)")

    user_input = input("Choose problems or mode: ").strip().lower()

    infinite_mode = False

    if user_input == 'p':
        chosen_cls = random.choice(problem_list)
        infinite_mode = True
        return {chosen_cls: problems[chosen_cls]}, infinite_mode
    elif user_input == 'r':
        infinite_mode = True
        return problems, infinite_mode
    elif not user_input:
        return problems, infinite_mode

    try:
        selected_numbers = [int(x) for x in user_input.split()]
        selected_problems = {}

        for num in selected_numbers:
            if 1 <= num <= len(problem_list):
                cls = problem_list[num - 1]
                selected_problems[cls] = problems[cls]
            else:
                print(f"Warning: Problem number {num} is out of range (1-{len(problem_list)})")

        if selected_problems:
            return selected_problems, infinite_mode
        print("No valid problems selected.")
        return None, infinite_mode

    except ValueError:
        print("Error: Please enter valid numbers, 'p', or 'r'")
        return None, infinite_mode


def create_next_problem(problem_class, rounds_played: dict):
    """Create the next problem of a class, with its own round number.

    TwoBackRecall resets its history on round 1, so every class needs a count
    of its own rounds in this session.
    """
    rounds_played[problem_class] = rounds_played.get(problem_class, 0) + 1
    return problem_class.create(round_num=rounds_played[problem_class])


def display_centered_text(stdscr, y: int, text: str, color_pair: int = 0) -> None:
    """Display text centered on the screen."""
    height, width = stdscr.getmaxyx()
    x = max(0, (width - len(text)) // 2)
    if 0 <= y < height:
        try:
            stdscr.addstr(y, x, text, color_pair)
        except curses.error:
            pass


def redraw_centered_line(stdscr, y: int, text: str, color_pair: int = 0) -> None:
    """Replace a whole line. A line outside the window is skipped."""
    try:
        stdscr.move(y, 0)
        stdscr.clrtoeol()
    except curses.error:
        return
    display_centered_text(stdscr, y, text, color_pair)


def draw_answer_line(stdscr, label: str, answer: str) -> None:
    """Draw the answer line and put the cursor at its end.

    An answer wider than the window shows only its end. The full answer is still
    kept and scored.
    """
    height, width = stdscr.getmaxyx()
    y = height // 2
    x = max(0, (width - len(label) - 30) // 2)
    answer_x = x + len(label)
    room = max(0, width - answer_x - 1)
    visible = answer[-room:] if room else ""
    try:
        stdscr.move(y, 0)
        stdscr.clrtoeol()
        stdscr.addstr(y, x, label + visible)
        stdscr.move(y, answer_x + len(visible))
    except curses.error:
        pass


def session_totals(session_records: list[Record]) -> tuple[int, float, int]:
    """Return the number of answers, the total score and the perfect answers."""
    return (
        len(session_records),
        sum(r.score for r in session_records),
        sum(1 for r in session_records if r.correct),
    )


def display_memorize_phase(
    stdscr,
    memorize: str,
    exposure_ms: int,
    problem_num: int,
    total_problems: int,
    current_avg: float,
    correct_count: int,
    session_time: float,
) -> None:
    """Display the memorize phase with countdown timer."""
    height = stdscr.getmaxyx()[0]
    center_y = height // 2

    minutes, seconds = divmod(int(session_time), 60)
    
    if total_problems == float('inf'):
        problem_info = f"Problem {problem_num} | Avg: {current_avg:.1f}%"
        status_line = (
            f"Completed: {problem_num - 1} | Correct: {correct_count} | "
            f"Session time: {minutes}:{seconds:02d}"
        )
    else:
        problem_info = f"Problem {problem_num}/{total_problems} | Avg: {current_avg:.1f}%"
        status_line = (
            f"Completed: {problem_num - 1} / {total_problems} | Correct: {correct_count} | "
            f"Session time: {minutes}:{seconds:02d}"
        )

    steps = 20
    step_ms = exposure_ms // steps
    countdown_y = center_y + 3

    for i in range(steps, 0, -1):
        stdscr.clear()

        display_centered_text(stdscr, 1, problem_info, curses.color_pair(3))
        display_centered_text(stdscr, 2, status_line, curses.color_pair(2))

        if "\n" in memorize:
            lines = memorize.split("\n")
            start_y = center_y - len(lines) // 2
            for j, line in enumerate(lines):
                display_centered_text(stdscr, start_y + j, line)
        else:
            display_centered_text(stdscr, center_y, memorize)

        remaining_ms = i * step_ms
        remaining_s = remaining_ms / 1000.0
        countdown_text = f"Time remaining: {remaining_s:.1f}s"
        display_centered_text(stdscr, countdown_y, countdown_text, curses.color_pair(2))

        progress = (steps - i) / steps
        bar_width = 40
        filled = int(progress * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        display_centered_text(stdscr, countdown_y + 2, f"[{bar}]")

        stdscr.refresh()
        curses.napms(step_ms)


def display_response_phase(
    stdscr,
    prompt: str,
    problem_num: int,
    total_problems: int,
    current_avg: float,
    correct_count: int,
    session_start: float,
) -> tuple[str, int]:
    """Display the response phase with increasing timer."""
    if total_problems == float('inf'):
        problem_info = f"Problem {problem_num} | Avg: {current_avg:.1f}%"
        completed = f"Completed: {problem_num - 1}"
    else:
        problem_info = f"Problem {problem_num}/{total_problems} | Avg: {current_avg:.1f}%"
        completed = f"Completed: {problem_num - 1} / {total_problems}"

    if prompt == ">":
        display_prompt = "  →→→  "  # Forward
    elif prompt == "<":
        display_prompt = "  ←←←  "  # Backward
    else:
        display_prompt = prompt

    def draw_fixed_lines() -> None:
        stdscr.clear()
        display_centered_text(stdscr, 1, problem_info, curses.color_pair(3))
        display_centered_text(stdscr, stdscr.getmaxyx()[0] // 2 - 2, display_prompt)

    # Keys typed while the problem was on screen are not part of the answer.
    curses.flushinp()

    start_time_ns = time.time_ns()
    user_input = ""
    draw_fixed_lines()

    while True:
        elapsed_ms = (time.time_ns() - start_time_ns) / 1e6
        minutes, seconds = divmod(int(time.time() - session_start), 60)
        status = f"{completed} | Correct: {correct_count} | Session time: {minutes}:{seconds:02d}"

        redraw_centered_line(stdscr, 2, status, curses.color_pair(2))
        redraw_centered_line(stdscr, stdscr.getmaxyx()[0] // 2 + 3,
                             f"Response time: {elapsed_ms:.0f}ms", curses.color_pair(1))
        # Last, so that the answer stays visible when a small window overlaps lines.
        draw_answer_line(stdscr, "Answer: ", user_input)
        stdscr.refresh()

        stdscr.timeout(50)
        key = stdscr.getch()

        if key in (10, 13):
            break
        if key == curses.KEY_RESIZE:
            draw_fixed_lines()
        elif key in (127, curses.KEY_BACKSPACE):
            user_input = user_input[:-1]
        elif 32 <= key <= 126:
            user_input += chr(key)

    stdscr.timeout(-1)
    response_ms = int((time.time_ns() - start_time_ns) / 1e6)
    return user_input.strip().lower(), response_ms


def display_feedback_phase(
    stdscr,
    score: float,
    solution: str,
    user_input: str,
    response_ms: int,
    exposure_ms: int,
) -> None:
    """Display feedback for the answer."""
    solution = solution.replace("\n", " ")
    is_correct = score >= 1.0

    def draw() -> None:
        height = stdscr.getmaxyx()[0]
        center_y = height // 2
        stdscr.clear()

        if is_correct:
            display_centered_text(stdscr, center_y - 2, f"{checkmark} CORRECT!", curses.color_pair(2))
        elif score >= 0.7:
            display_centered_text(stdscr, center_y - 2, f"* CLOSE! ({score:.0%})", curses.color_pair(3))
        else:
            display_centered_text(stdscr, center_y - 2, f"{cross} INCORRECT ({score:.0%})", curses.color_pair(1))
        if not is_correct:
            display_centered_text(stdscr, center_y, f"Your answer: {user_input}")
            display_centered_text(stdscr, center_y + 1, f"Correct answer: {solution}")

        display_centered_text(stdscr, center_y + 3, f"Study time: {exposure_ms}ms | Response time: {response_ms}ms")
        if not is_correct:
            # On the last row at most, so that a small window still shows what to do.
            display_centered_text(stdscr, min(center_y + 5, height - 1), "Press Space or Enter to continue")
        stdscr.refresh()

    draw()
    # A held Enter from the answer must not close this screen.
    curses.flushinp()

    start_wait = time.time()
    while True:
        stdscr.timeout(50)
        key = stdscr.getch()
        if key in (ord(" "), 10, 13):
            break
        if key == curses.KEY_RESIZE:
            draw()
        if is_correct and time.time() - start_wait >= CORRECT_FEEDBACK_S:
            break
    stdscr.timeout(-1)


def performance_names(problem_names: list[str], stats_by_name: dict) -> list[str]:
    """Return the games for the statistics table, with old games that only the history knows."""
    known = {name.lower() for name in problem_names}
    return sorted(problem_names + [name for name in stats_by_name if name.lower() not in known])


def main(stdscr, max_nr: int, selected_problems: dict | None) -> None:
    global records

    problems = selected_problems if selected_problems else all_problems
    records = []
    start_time = None
    test_date = None

    try:
        curses.endwin()
        if max_nr == float('inf'):
            print("Starting immersive training session in continuous mode...")
            print("Press Ctrl+C at any time to stop and save your score.")
        else:
            print(f"Starting immersive training session with {max_nr} questions...")
            print("Each problem will use the full screen with countdown timers.")
        input("Press Enter to start...")

        start_time = time.time()
        test_date = datetime.datetime.now().astimezone()

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_BLUE, -1)
        curses.curs_set(0)

        stdscr.clear()
        rounds_played = {}

        try:
            while len(records) < max_nr:
                problem_class = random.choices(list(problems.keys()), list(problems.values()))[0]
                pb = create_next_problem(problem_class, rounds_played)
                memorize, prompt, solution, exposure_ms = (
                    pb.memorize,
                    pb.prompt,
                    pb.solution,
                    pb.exposure_ms,
                )

                nr, total_score, correct_count = session_totals(records)
                current_avg = (total_score / nr * 100) if nr > 0 else 0
                session_time = time.time() - start_time

                is_scored = getattr(pb, 'is_scored', True)

                display_memorize_phase(
                    stdscr, memorize, exposure_ms, nr + 1, max_nr, current_avg, correct_count, session_time
                )

                if is_scored:
                    curses.curs_set(1)
                    user_input, response_ms = display_response_phase(
                        stdscr, prompt, nr + 1, max_nr, current_avg, correct_count, start_time
                    )
                    curses.curs_set(0)

                    score = pb.evaluate_solution(user_input)
                    records.append(Record(pb, user_input, response_ms, score))

                    display_feedback_phase(stdscr, score, solution, user_input, response_ms, exposure_ms)
                else:
                    stdscr.clear()
                    stdscr.refresh()
                    curses.napms(500)
        except KeyboardInterrupt:
            pass


    finally:
        try:
            curses.curs_set(1)
            curses.endwin()
            curses.reset_shell_mode()
        except curses.error:
            pass
        # Here, so that an unexpected error does not lose the answers.
        if start_time is not None:
            nr, _, n_perfect = session_totals(records)
            save_session_data(test_date, start_time, nr, n_perfect, records)

    nr, total_score, n_perfect = session_totals(records)
    final_percentage = (total_score / nr * 100) if nr > 0 else 0

    print(f"\n{format_score(nr, n_perfect, records, total_score, final_percentage)}")
    print("\n" + "=" * 50)
    print("ALL-TIME STATISTICS")
    print("=" * 50)

    all_time_stats = load_session_statistics()
    if all_time_stats["total_sessions"] > 0:
        print(f"Total training sessions: {all_time_stats['total_sessions']}")
        print(f"Total questions answered: {all_time_stats['total_questions']}")
        print(f"Overall average score: {all_time_stats['overall_average_score']:.1f}%")
        print(f"Recent average (last 5): {all_time_stats['recent_average']:.1f}%")
        if all_time_stats["best_session"]:
            best = all_time_stats["best_session"]
            problem_types = sorted(
                {(r.get("problem") or {}).get("name", "unknown") for r in best.get("records", [])}
            )
            games_str = ", ".join(problem_types) if problem_types else "mixed"
            print(f"Best session: {best['score_percentage']:.1f}% on {best.get('date', 'unknown date')} ({games_str})")
        stats_by_name = all_time_stats["problem_name_stats"]
        all_problem_names = performance_names([cls.display_name() for cls in all_problems], stats_by_name)
        if all_problem_names:
            print("\nPerformance by problem type:")
            max_name_length = max(len(name) for name in all_problem_names)
            for problem_name in all_problem_names:
                stats = stats_by_name.get(problem_name) or stats_by_name.get(problem_name.lower())
                if stats is None:
                    stats = {"correct": 0, "total": 0, "accuracy_percentage": 0.0}
                accuracy = stats["accuracy_percentage"]
                total = stats["total"]
                correct = stats["correct"]
                padded = problem_name.ljust(max_name_length)
                print(f"  {padded}: {correct:>3}/{total:<3}  {accuracy:>5.1f}%")
    else:
        print("This is your first training session - keep it up!")


def parse_args():
    parser = argparse.ArgumentParser(description="Immersive Memory Training Application")
    parser.add_argument("-n", "--questions", type=int, default=10, help="Number of questions (default: 10)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.questions <= 0:
        print("Error: Number of questions must be positive")
        sys.exit(1)

    result = select_problems_interactively()
    if result[0] is None:
        print("No problems selected. Exiting.")
        sys.exit(0)
        
    selected_problems, infinite_mode = result

    if infinite_mode:
        args.questions = float('inf')

    curses.wrapper(lambda stdscr: main(stdscr, args.questions, selected_problems))

    os.system("stty sane")
