"""Full-screen memory trainer with countdown timers."""

import argparse
import curses
import datetime
import os
import random
import sys
import time

from classes import Record
from problems import create_problems_dict, format_problem_name
from sessions import save_session_data, format_score, load_session_statistics

checkmark = "\u2713"  # ✓
cross = "\u2717"  # ✗

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
        formatted_name = format_problem_name(cls.__name__)
        print(f"  {i:>{max_num_width}}. {formatted_name}")

    print("\nEnter problem numbers separated by spaces (e.g., '1 3 5')")
    print("Press Enter to select all problems")

    user_input = input("Choose problems: ").strip()

    if not user_input:
        return problems

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
            return selected_problems
        print("No valid problems selected.")
        return None

    except ValueError:
        print("Error: Please enter valid numbers separated by spaces")
        return None


def display_centered_text(stdscr, y: int, text: str, color_pair: int = 0) -> None:
    """Display text centered on the screen."""
    height, width = stdscr.getmaxyx()
    x = max(0, (width - len(text)) // 2)
    if 0 <= y < height:
        try:
            stdscr.addstr(y, x, text, color_pair)
        except curses.error:
            pass


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
    height, width = stdscr.getmaxyx()
    center_y = height // 2

    problem_info = f"Problem {problem_num}/{total_problems} | Avg: {current_avg:.1f}%"
    minutes, seconds = divmod(int(session_time), 60)
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
    session_time: float,
    session_start: float,
) -> tuple[str, int]:
    """Display the response phase with increasing timer."""
    height, width = stdscr.getmaxyx()
    stdscr.clear()

    problem_info = f"Problem {problem_num}/{total_problems} | Avg: {current_avg:.1f}%"
    minutes, seconds = divmod(int(session_time), 60)
    status_line = (
        f"Completed: {problem_num - 1} / {total_problems} | Correct: {correct_count} | "
        f"Session time: {minutes}:{seconds:02d}"
    )

    display_centered_text(stdscr, 1, problem_info, curses.color_pair(3))
    display_centered_text(stdscr, 2, status_line, curses.color_pair(2))

    center_y = height // 2
    display_prompt = "→" if prompt == ">" else "←" if prompt == "<" else prompt
    display_centered_text(stdscr, center_y - 2, display_prompt)

    input_text = "Answer: "
    input_y = center_y
    input_x = max(0, (width - len(input_text) - 30) // 2)

    try:
        stdscr.addstr(input_y, input_x, input_text)
    except curses.error:
        pass

    timer_y = center_y + 3
    input_cursor_x = input_x + len(input_text)
    start_time_ns = time.time_ns()
    user_input = ""

    display_centered_text(stdscr, timer_y, "Response time: 0ms", curses.color_pair(1))
    stdscr.move(input_y, input_cursor_x)
    stdscr.refresh()

    while True:
        stdscr.timeout(50)
        key = stdscr.getch()

        elapsed_ms = (time.time_ns() - start_time_ns) / 1e6
        timer_text = f"Response time: {elapsed_ms:.0f}ms"
        current_session_time = time.time() - session_start
        minutes, seconds = divmod(int(current_session_time), 60)
        updated_status = (
            f"Completed: {problem_num - 1} / {total_problems} | Correct: {correct_count} | "
            f"Session time: {minutes}:{seconds:02d}"
        )

        stdscr.move(2, 0)
        stdscr.clrtoeol()
        display_centered_text(stdscr, 2, updated_status, curses.color_pair(2))
        stdscr.move(timer_y, 0)
        stdscr.clrtoeol()
        display_centered_text(stdscr, timer_y, timer_text, curses.color_pair(1))

        if key == -1:
            stdscr.move(input_y, input_cursor_x + len(user_input))
            stdscr.refresh()
            continue
        if key in (10, 13):
            break
        if key in (127, curses.KEY_BACKSPACE):
            if user_input:
                user_input = user_input[:-1]
                stdscr.move(input_y, input_x)
                stdscr.clrtoeol()
                stdscr.addstr(input_y, input_x, input_text + user_input)
        elif 32 <= key <= 126:
            user_input += chr(key)
            stdscr.addch(input_y, input_cursor_x + len(user_input) - 1, key)

        stdscr.move(input_y, input_cursor_x + len(user_input))
        stdscr.refresh()

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
    height = stdscr.getmaxyx()[0]
    stdscr.clear()
    center_y = height // 2

    if score >= 1.0:
        display_centered_text(stdscr, center_y - 2, f"{checkmark} CORRECT!", curses.color_pair(2))
    elif score >= 0.7:
        display_centered_text(stdscr, center_y - 2, f"* CLOSE! ({score:.0%})", curses.color_pair(3))
        display_centered_text(stdscr, center_y, f"Your answer: {user_input}")
        display_centered_text(stdscr, center_y + 1, f"Correct answer: {solution}")
    else:
        display_centered_text(stdscr, center_y - 2, f"{cross} INCORRECT ({score:.0%})", curses.color_pair(1))
        display_centered_text(stdscr, center_y, f"Your answer: {user_input}")
        display_centered_text(stdscr, center_y + 1, f"Correct answer: {solution}")

    display_centered_text(stdscr, center_y + 3, f"Study time: {exposure_ms}ms | Response time: {response_ms}ms")
    stdscr.refresh()

    start_wait = time.time()
    while True:
        stdscr.timeout(50)
        key = stdscr.getch()
        if key == ord(" ") or (time.time() - start_wait) >= 0.5:
            break
    stdscr.timeout(-1)


def main(stdscr, max_nr: int, selected_problems: dict | None) -> None:
    global records

    problems = selected_problems if selected_problems else all_problems
    records = []

    try:
        curses.endwin()
        print(f"Starting immersive training session with {max_nr} questions...")
        print("Each problem will use the full screen with countdown timers.")
        input("Press Enter to start...")

        start_time = time.time()
        test_date = datetime.datetime.now()

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_BLUE, -1)
        curses.curs_set(0)

        stdscr.clear()
        nr = 0
        total_score = 0.0

        while nr < max_nr:
            problem_class = random.choices(list(problems.keys()), list(problems.values()))[0]
            pb = problem_class.create()
            memorize, prompt, solution, exposure_ms = (
                pb.memorize,
                pb.prompt,
                pb.solution,
                pb.exposure_ms,
            )

            current_avg = (total_score / nr * 100) if nr > 0 else 0
            correct_count = sum(1 for r in records if r.score >= 1.0)
            session_time = time.time() - start_time

            display_memorize_phase(
                stdscr, memorize, exposure_ms, nr + 1, max_nr, current_avg, correct_count, session_time
            )

            curses.curs_set(1)
            user_input, response_ms = display_response_phase(
                stdscr, prompt, nr + 1, max_nr, current_avg, correct_count, session_time, start_time
            )
            curses.curs_set(0)

            score = pb.evaluate_solution(user_input)
            total_score += score
            records.append(Record(pb, user_input, response_ms, score))

            display_feedback_phase(stdscr, score, solution, user_input, response_ms, exposure_ms)
            nr += 1

    finally:
        try:
            curses.curs_set(1)
            curses.endwin()
            curses.reset_shell_mode()
        except curses.error:
            pass

    final_percentage = (total_score / nr * 100) if nr > 0 else 0
    n_perfect = sum(1 for r in records if r.score >= 1.0)
    save_session_data(test_date, start_time, nr, n_perfect, records)

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
            print(f"Best session: {best['score_percentage']:.1f}% on {best['date']}")
        if all_time_stats["problem_name_stats"]:
            print("\nPerformance by problem type:")
            max_name_length = max(len(pt) for pt in all_time_stats["problem_name_stats"])
            for problem_name in sorted(all_time_stats["problem_name_stats"]):
                stats = all_time_stats["problem_name_stats"][problem_name]
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

    selected_problems = select_problems_interactively()
    if not selected_problems:
        print("No problems selected. Exiting.")
        sys.exit(0)

    curses.wrapper(lambda stdscr: main(stdscr, args.questions, selected_problems))

    os.system("stty sane")
