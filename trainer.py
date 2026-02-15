import argparse
import curses
import datetime
import random
import sys
import time

from classes import Record
from problems import create_problems_dict, format_problem_name
from sessions import save_session_data, format_score, load_session_statistics

# word/number pairs, bilingual pairs
# japanese pronunciation
# show progressively and hide
# traduction, words with translations like anki
# sequence de symboles et questions sur eg 3eme symbole (up arrow)
# n-back
# words/colors
# distracteurs, mots dans des distracteurs
# pairs with colors
# random letters and numbers, remove some, restitute missing
# une faute dans un mot, restituer le mot correct
# restituer un anagramme
# show a sentence one word at a time at speed, then ask question 
# raw facts like city populations

# structure: sous classes de probleme, fonctions pour poser le probleme et evaluer (
# plusieurs solutions pour anagrammes)
# rester sur tache pendant 3 ou 4 rounds puis switcher au hasard
# short shows
# complete sentence and restitute n-th word, from beginning, from end
# decoy or wait before prompt
# count letters of word
# add progression based on prior progress
# add db to store results and analyze them for progress
# stay on a problem for a while then change

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


def main(stdscr, max_nr=10, selected_problems=None):

  problems = selected_problems if selected_problems else all_problems

  curses.endwin()  # Temporarily exit curses mode
  
  print(f"Starting training session with {max_nr} questions...")
  input("Press Enter to start...")
  
  # Re-initialize curses
  curses.start_color()
  curses.use_default_colors()
  curses.init_pair(1, curses.COLOR_RED, -1)
  curses.init_pair(2, curses.COLOR_GREEN, -1)
  curses.init_pair(3, curses.COLOR_BLUE, -1)

  stdscr.clear()

  nr = 0
  total_score = 0.0  # Running sum of fractional scores
  stats_col = 60
  response_ms_col = 75
  correction_col = 86

  while nr < max_nr:

    problem_class = random.choices(list(problems.keys()), list(problems.values()))[0]
    pb = problem_class.create()
    memorize, prompt, solution, exposure_ms = pb.memorize, pb.prompt, pb.solution, pb.exposure_ms

    n_minutes, n_seconds = divmod(time.time() - start_time, 60)
    n_minutes, n_seconds = int(n_minutes), int(n_seconds)
    stdscr.addstr(nr, 0, memorize)
    current_avg = (total_score / nr * 100) if nr > 0 else 0
    stdscr.addstr(nr, stats_col, f'{current_avg:.1f}% {n_minutes}:{n_seconds}')
    stdscr.refresh()
    curses.napms(exposure_ms)

    stdscr.addstr(nr, 0, ' ' * (stats_col-1))
    stdscr.addstr(nr, 0, f'{prompt}')
    stdscr.refresh()
    stdscr.move(nr, len(prompt) + 1)

    curses.echo()
    t0 = time.time_ns()
    user_input = stdscr.getstr(nr, len(prompt) + 1, 256).decode('utf-8').strip().lower()
    response_ms = int((time.time_ns() - t0) / 1e6)
    curses.noecho()

    stdscr.addstr(nr, response_ms_col, f'{exposure_ms}/{response_ms}s')

    # Calculate fractional score
    score = pb.evaluate_solution(user_input)
    total_score += score
    
    # Display score with visual feedback
    if score == 1.0:
      stdscr.addstr(nr, 0, checkmark, curses.color_pair(2))
    elif score >= 0.7:
      stdscr.addstr(nr, 0, '*', curses.color_pair(3))  # Close match
      stdscr.addstr(nr, correction_col, solution)
    else:
      stdscr.addstr(nr, 0, cross, curses.color_pair(1))
      stdscr.addstr(nr, correction_col, solution)
    
    # Show score percentage
    stdscr.addstr(nr, correction_col + len(solution) + 1, f'({score:.1%})')
    
    record = Record(pb, user_input, response_ms, score)

    nr += 1
    records.append(record)

  curses.endwin()

  # Calculate final statistics
  final_percentage = (total_score / nr * 100) if nr > 0 else 0
  n_perfect = sum(1 for r in records if r.problem.evaluate_solution(r.response) == 1.0)
  
  # Print final score and statistics
  final_score_text = format_score(nr, n_perfect, records, total_score, final_percentage)
  print(f"\n{final_score_text}")
  
  # Save session data first
  save_session_data(test_date, start_time, nr, n_perfect, records)
  
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
  parser = argparse.ArgumentParser(description='Memory Training Application')
  parser.add_argument('-n', '--questions', type=int, default=10, 
                      help='Number of questions to answer (default: 10)')
  parser.add_argument('-l', '--list-problems', action='store_true',
                      help='List available problem types and exit')
  return parser.parse_args()


if __name__ == '__main__':
  args = parse_args()
  
  # Handle --list-problems option
  if args.list_problems:
    selected_problems = select_problems_interactively()
    if not selected_problems:
      print("No problems selected. Exiting.")
      sys.exit(0)
    curses.wrapper(lambda stdscr: main(stdscr, args.questions, selected_problems))
    sys.exit(0)
  
  if args.questions <= 0:
    print("Error: Number of questions must be positive")
    sys.exit(1)
  
  curses.wrapper(lambda stdscr: main(stdscr, args.questions))
