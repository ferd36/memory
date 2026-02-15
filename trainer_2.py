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

# Full-screen memory trainer with countdown timers and screen clearing
# Designed for 2D problems and immersive training experience

checkmark = '\u2713'  # ✓
cross = '\u2717'  # ✗


test_date = datetime.datetime.now()
start_time = time.time()
duration_s = None

records = []


all_problems = create_problems_dict()


def select_problems_interactively():
  """Show numbered problems and let user select which ones to use"""
  problems = all_problems
  problem_list = sorted(problems.keys(), key=lambda x: x.__name__)
  
  print("MEMORY TRAINER")
  print("=" * 55)
  print()
  print("Available problem types:")
  # Calculate the width needed for the largest number
  max_num_width = len(str(len(problem_list)))
  for i, cls in enumerate(problem_list, 1):
    formatted_name = format_problem_name(cls.__name__)
    print(f"  {i:>{max_num_width}}. {formatted_name}")
  
  print("\nEnter problem numbers separated by spaces (e.g., '1 3 5')")
  print("Press Enter to select all problems")
  
  user_input = input("Choose problems: ").strip()
  
  # If empty (just Enter), return all problems
  if not user_input:
    return problems
  
  # Parse selected problem numbers
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
      for cls in selected_problems:
        formatted_name = format_problem_name(cls.__name__)
      return selected_problems
    else:
      print("No valid problems selected.")
      return None
      
  except ValueError:
    print("Error: Please enter valid numbers separated by spaces")
    return None


def display_centered_text(stdscr, y, text, color_pair=0):
  """Display text centered on the screen"""
  height, width = stdscr.getmaxyx()
  x = max(0, (width - len(text)) // 2)
  if 0 <= y < height:
    try:
      stdscr.addstr(y, x, text, color_pair)
    except curses.error:
      pass  # Ignore if text doesn't fit


def display_memorize_phase(stdscr, memorize, exposure_ms, problem_num, total_problems, current_avg, correct_count, session_time):
  """Display the memorize phase with countdown timer"""
  height, width = stdscr.getmaxyx()
  
  # Display problem info at top
  problem_info = f"Problem {problem_num}/{total_problems} | Avg: {current_avg:.1f}%"
  display_centered_text(stdscr, 1, problem_info, curses.color_pair(3))
  
  # Display status line with progress and timing
  minutes, seconds = divmod(int(session_time), 60)
  status_line = f"Completed: {problem_num-1} / {total_problems} | Correct: {correct_count} | Session time: {minutes}:{seconds:02d}"
  display_centered_text(stdscr, 2, status_line, curses.color_pair(2))
  
  # Display memorize content in center
  center_y = height // 2
  
  # For multi-line content (like pairs or multiline problems), split and center each line
  if ':' in memorize and 'pair' in str(type(memorize)).lower():
    lines = memorize.split(' : ')
    start_y = center_y - len(lines) // 2
    for i, line in enumerate(lines):
      display_centered_text(stdscr, start_y + i, line)
  elif '\n' in memorize:
    # Handle multiline problems (like flight plans)
    lines = memorize.split('\n')
    start_y = center_y - len(lines) // 2
    for i, line in enumerate(lines):
      display_centered_text(stdscr, start_y + i, line)
  else:
    display_centered_text(stdscr, center_y, memorize)
  
  # Display countdown timer
  countdown_y = center_y + 3
  
  steps = 20  # Number of countdown steps
  step_ms = exposure_ms // steps
  
  for i in range(steps, 0, -1):
    stdscr.clear()
    
    # Redisplay problem info
    display_centered_text(stdscr, 1, problem_info, curses.color_pair(3))
    
    # Redisplay status line
    display_centered_text(stdscr, 2, status_line, curses.color_pair(2))
    
    # Redisplay memorize content
    if ':' in memorize and 'pair' in str(type(memorize)).lower():
      lines = memorize.split(' : ')
      start_y = center_y - len(lines) // 2
      for j, line in enumerate(lines):
        display_centered_text(stdscr, start_y + j, line)
    elif '\n' in memorize:
      # Handle multiline problems (like flight plans)
      lines = memorize.split('\n')
      start_y = center_y - len(lines) // 2
      for j, line in enumerate(lines):
        display_centered_text(stdscr, start_y + j, line)
    else:
      display_centered_text(stdscr, center_y, memorize)
    
    # Show countdown
    remaining_ms = i * step_ms
    remaining_s = remaining_ms / 1000.0
    countdown_text = f"Time remaining: {remaining_s:.1f}s"
    display_centered_text(stdscr, countdown_y, countdown_text, curses.color_pair(2))
    
    # Progress bar
    progress = (steps - i) / steps
    bar_width = 40
    filled = int(progress * bar_width)
    bar = '█' * filled + '░' * (bar_width - filled)
    display_centered_text(stdscr, countdown_y + 2, f"[{bar}]")
    
    stdscr.refresh()
    curses.napms(step_ms)


def display_response_phase(stdscr, prompt, problem_num, total_problems, current_avg, correct_count, session_time):
  """Display the response phase with increasing timer"""
  height, width = stdscr.getmaxyx()
  stdscr.clear()
  
  # Display problem info at top
  problem_info = f"Problem {problem_num}/{total_problems} | Avg: {current_avg:.1f}%"
  display_centered_text(stdscr, 1, problem_info, curses.color_pair(3))
  
  # Display status line with progress and timing
  minutes, seconds = divmod(int(session_time), 60)
  status_line = f"Completed: {problem_num-1} / {total_problems} | Correct: {correct_count} | Session time: {minutes}:{seconds:02d}"
  display_centered_text(stdscr, 2, status_line, curses.color_pair(2))
  
  # Display prompt in center
  center_y = height // 2
  
  # Convert arrow symbols
  display_prompt = prompt
  if prompt == '>':
    display_prompt = '→'
  elif prompt == '<':
    display_prompt = '←'
  
  prompt_text = f"{display_prompt}"
  display_centered_text(stdscr, center_y - 2, prompt_text)
  
  # Input area
  input_text = "Answer: "
  input_y = center_y
  input_x = max(0, (width - len(input_text) - 30) // 2)  # More space for input
  
  try:
    stdscr.addstr(input_y, input_x, input_text)
  except curses.error:
    pass
  
  # Timer display area
  timer_y = center_y + 3
  
  # Start timing
  start_time_ns = time.time_ns()
  
  # Get user input with custom character-by-character input to show timer
  user_input = ""
  input_cursor_x = input_x + len(input_text)
  
  # Initial timer display
  elapsed_ms = 0
  timer_text = f"Response time: {elapsed_ms:.0f}ms"
  display_centered_text(stdscr, timer_y, timer_text, curses.color_pair(1))
  stdscr.move(input_y, input_cursor_x)
  stdscr.refresh()
  
  # Character-by-character input (no auto-advance, user has all the time they need)
  while True:
    stdscr.timeout(50)  # 50ms timeout for getch
    key = stdscr.getch()
    
    # Update timer
    elapsed_ms = (time.time_ns() - start_time_ns) / 1e6
    timer_text = f"Response time: {elapsed_ms:.0f}ms"
    
    # Update session time and redraw status line
    current_session_time = time.time() - start_time
    minutes, seconds = divmod(int(current_session_time), 60)
    updated_status_line = f"Completed: {problem_num-1} / {total_problems} | Correct: {correct_count} | Session time: {minutes}:{seconds:02d}"
    
    # Clear and redraw status line
    stdscr.move(2, 0)
    stdscr.clrtoeol()
    display_centered_text(stdscr, 2, updated_status_line, curses.color_pair(2))
    
    # Clear timer line and redraw
    stdscr.move(timer_y, 0)
    stdscr.clrtoeol()
    display_centered_text(stdscr, timer_y, timer_text, curses.color_pair(1))
    
    if key == -1:  # Timeout, no key pressed
      stdscr.move(input_y, input_cursor_x + len(user_input))
      stdscr.refresh()
      continue
    elif key == 10 or key == 13:  # Enter key to submit answer
      break
    elif key == 127 or key == curses.KEY_BACKSPACE:  # Backspace
      if user_input:
        user_input = user_input[:-1]
        # Clear the input line and redraw
        stdscr.move(input_y, input_x)
        stdscr.clrtoeol()
        stdscr.addstr(input_y, input_x, input_text + user_input)
    elif 32 <= key <= 126:  # Printable characters
      user_input += chr(key)
      stdscr.addch(input_y, input_cursor_x + len(user_input) - 1, key)
    
    stdscr.move(input_y, input_cursor_x + len(user_input))
    stdscr.refresh()
  
  stdscr.timeout(-1)  # Reset timeout
  response_ms = int((time.time_ns() - start_time_ns) / 1e6)
  return user_input.strip().lower(), response_ms


def display_feedback_phase(stdscr, score, solution, user_input, response_ms, exposure_ms):
  """Display feedback for the answer"""
  height, width = stdscr.getmaxyx()
  stdscr.clear()
  
  center_y = height // 2
  
  # Show result
  if score == 1.0:
    result_text = f"{checkmark} CORRECT!"
    display_centered_text(stdscr, center_y - 2, result_text, curses.color_pair(2))
  elif score >= 0.7:
    result_text = f"* CLOSE! ({score:.1%})"
    display_centered_text(stdscr, center_y - 2, result_text, curses.color_pair(3))
    display_centered_text(stdscr, center_y, f"Your answer: {user_input}")
    display_centered_text(stdscr, center_y + 1, f"Correct answer: {solution}")
  else:
    result_text = f"{cross} INCORRECT ({score:.1%})"
    display_centered_text(stdscr, center_y - 2, result_text, curses.color_pair(1))
    display_centered_text(stdscr, center_y, f"Your answer: {user_input}")
    display_centered_text(stdscr, center_y + 1, f"Correct answer: {solution}")
  
  # Show timing
  timing_text = f"Study time: {exposure_ms}ms | Response time: {response_ms}ms"
  display_centered_text(stdscr, center_y + 3, timing_text)
  
  stdscr.refresh()
  
  # Auto-advance after 0.5 seconds (or allow manual advance with SPACE)
  start_wait = time.time()
  feedback_delay = 0.5  # 0.5 seconds to view feedback
  
  while True:
    stdscr.timeout(50)  # 50ms timeout
    key = stdscr.getch()
    elapsed = time.time() - start_wait
    
    if key == ord(' '):  # Manual advance with SPACE
      break
    elif elapsed >= feedback_delay:  # Auto-advance after 0.5 seconds
      break
  
  stdscr.timeout(-1)  # Reset timeout


def main(stdscr, max_nr=10, selected_problems=None):
  global start_time, test_date, records

  problems = selected_problems if selected_problems else all_problems

  try:
    curses.endwin()  # Temporarily exit curses mode
    
    print(f"Starting immersive training session with {max_nr} questions...")
    print("Each problem will use the full screen with countdown timers.")
    input("Press Enter to start...")
    
    # Re-initialize curses
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_BLUE, -1)
    curses.curs_set(0)  # Hide cursor initially

    stdscr.clear()

    nr = 0
    total_score = 0.0  # Running sum of fractional scores

    while nr < max_nr:
      problem_class = random.choices(list(problems.keys()), list(problems.values()))[0]
      pb = problem_class.create()
      memorize, prompt, solution, exposure_ms = pb.memorize, pb.prompt, pb.solution, pb.exposure_ms

      current_avg = (total_score / nr * 100) if nr > 0 else 0
      
      # Calculate correct count and session time
      correct_count = sum(1 for r in records if r.score >= 1.0)
      session_time = time.time() - start_time

      # Phase 1: Display memorize content with countdown
      display_memorize_phase(stdscr, memorize, exposure_ms, nr + 1, max_nr, current_avg, correct_count, session_time)

      # Phase 2: Display prompt and get response with timer
      curses.curs_set(1)  # Show cursor for input
      user_input, response_ms = display_response_phase(stdscr, prompt, nr + 1, max_nr, current_avg, correct_count, session_time)
      curses.curs_set(0)  # Hide cursor again

      # Calculate fractional score
      score = pb.evaluate_solution(user_input)
      total_score += score
      
      # Phase 3: Display feedback
      display_feedback_phase(stdscr, score, solution, user_input, response_ms, exposure_ms)
      
      record = Record(pb, user_input, response_ms, score)

      nr += 1
      records.append(record)

  finally:
    # Ensure proper terminal cleanup
    try:
      curses.curs_set(1)  # Restore cursor
      curses.endwin()     # Exit curses mode
      curses.reset_shell_mode()  # Reset terminal to shell mode
    except curses.error:
      pass

  # Calculate final statistics
  final_percentage = (total_score / nr * 100) if nr > 0 else 0
  n_perfect = sum(1 for r in records if r.problem.evaluate_solution(r.response) == 1.0)
  
  # Save session data first
  save_session_data(test_date, start_time, nr, n_perfect, records)
  
  # Print final score and statistics
  final_score_text = format_score(nr, n_perfect, records, total_score, final_percentage)
  print(f"\n{final_score_text}")
  
  # Display all-time statistics
  print("\n" + "="*50)
  print("ALL-TIME STATISTICS")
  print("="*50)
  
  all_time_stats = load_session_statistics()
  
  if all_time_stats['total_sessions'] > 0:
    print(f"Total training sessions: {all_time_stats['total_sessions']}")
    print(f"Total questions answered: {all_time_stats['total_questions']}")
    print(f"Overall average score: {all_time_stats['overall_average_score']:.1f}%")
    print(f"Recent average (last 5): {all_time_stats['recent_average']:.1f}%")
    
    if all_time_stats['best_session']:
      best = all_time_stats['best_session']
      print(f"Best session: {best['score_percentage']:.1f}% on {best['date']}")
    
    # Problem type breakdown
    if all_time_stats['problem_name_stats']:
      print("\nPerformance by problem type:")
      max_name_length = max(len(ptype) for ptype in all_time_stats['problem_name_stats'].keys())
      
      for problem_name in sorted(all_time_stats['problem_name_stats'].keys()):
        stats = all_time_stats['problem_name_stats'][problem_name]
        accuracy = stats['accuracy_percentage']
        acc_std = stats.get('accuracy_std_dev', 0)
        avg_time = stats.get('avg_response_time', 0)
        time_std = stats.get('response_time_std_dev', 0)
        total = stats['total']
        correct = stats['correct']
        
        padded_type = problem_name.ljust(max_name_length)
        print(f"  {padded_type}: {correct:>3}/{total:<3}  {accuracy:>5.1f}% ± {acc_std:>4.1f}%  {avg_time:>4.1f}s ± {time_std:>3.1f}s")
    
  else:
    print("This is your first training session - keep it up!")


def parse_args():
  parser = argparse.ArgumentParser(description='Immersive Memory Training Application')
  parser.add_argument('-n', '--questions', type=int, default=10, 
                      help='Number of questions to answer (default: 10)')
  return parser.parse_args()


if __name__ == '__main__':
  args = parse_args()
  
  try:
    if args.questions <= 0:
      print("Error: Number of questions must be positive")
      sys.exit(1)
    
    # Always show problem selection (like trainer.py)
    selected_problems = select_problems_interactively()
    if not selected_problems:
      print("No problems selected. Exiting.")
      sys.exit(0)
    
    curses.wrapper(lambda stdscr: main(stdscr, args.questions, selected_problems))
    
  finally:
    # Final terminal reset to ensure shell prompt is restored
    os.system('stty sane')  # More gentle reset than full 'reset' command