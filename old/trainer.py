import curses
import datetime
import random
import time

from dataclasses import dataclass
from typing import Any

from unidecode import unidecode

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
# airplane, metro, uber details, to restitute after a few
# dates/heures/doc de rdv medicaux
# show a sentence one word at a time at speed, then ask question

# structure: sous classes de probleme, fonctions pour poser le probleme et evaluer (
# plusieurs solutions pour anagrammes)
# rester sur tache pendant 3 ou 4 rounds puis switcher au hasard
# short shows
# complete sentence and restitute n-th word, from beginning, from end
# decoy or wait before prompt
# count letters of word
# add progression based on prior progress
# add db to store results and analyze them for progress

checkmark = '\u2713'  # ✓
cross = '\u2717'  # ✗

dict_paths = [
  '/usr/share/dict/words',
  'dicts/common_english_words.txt',
  'dicts/common_french_words.txt',
  'dicts/german_words.txt',
  # 'dicts/french_words.txt',
  ]


@dataclass
class Problem:
  problem_type: str
  memorize: str
  prompt: str
  solution: str
  exposure_ms: int

  def __reduce__(self) -> str | tuple[Any, ...]:
    return self.memorize, self.prompt, self.solution, self.exposure_ms

  def __repr__(self):
    return (f'type={self.problem_type}, '
            f'memorize={self.memorize} '
            f'prompt={self.prompt} '
            f'solution={self.solution} '
            f'exposure_ms={self.exposure_ms}')


words = []


# load by lengths
def load_dicts(word_length_min=4, word_length_max=6):
  for dict_path in dict_paths:
    with open(dict_path) as f:
      words_tmp = [w.strip().lower() for w in f if w.strip().isalpha()]
      if "german" in dict_path:
        words_tmp = [w.replace('ß', 'ss') for w in words_tmp]
      words.append([w for w in words_tmp if word_length_min <= len(w) <= word_length_max])


load_dicts()


def rnd_number(number_length):
  return ''.join([random.choice('0123456789') for _ in range(number_length)])


def word_list_problem(num_words=4):
  d = random.randint(0, len(words) - 1)
  sample = random.sample(words[d], num_words)
  memorize = ' '.join(sample)
  prompt = random.choice(['>', '<'])
  solution = ' '.join(sample[::1 if prompt == '>' else -1])
  return Problem('word list', memorize, prompt, solution, 4000)


def word_pairs_problem(num_pairs=3):
  d = random.randint(0, len(words) - 1)
  sample = random.sample(words[d], 2 * num_pairs)
  pairs = [(sample[2*i], sample[1 + 2 * i]) for i in range(num_pairs)]
  memorize = ' '.join(f'{p[0]}:{p[1]}' for p in pairs)
  chosen = random.randint(0, num_pairs - 1)
  prompt = f'? {pairs[chosen][0]}'
  solution = pairs[chosen][1]
  return Problem('word pairs', memorize, prompt, solution, 4000)


def word_number_pairs(num_pairs=3, number_length=4):
  d = random.randint(0, len(words) - 1)
  sample = random.sample(words[d], num_pairs)
  pairs = [(sample[i], rnd_number(number_length)) for i in range(num_pairs)]
  memorize = ' '.join(f'{p[0]}:{p[1]}' for p in pairs)
  chosen = random.randint(0, num_pairs - 1)
  prompt = f'? {pairs[chosen][0]}'
  solution = pairs[chosen][1]
  return Problem('word pairs', memorize, prompt, solution, 4000)


def number_problem(number_length=6):
  memorize = rnd_number(number_length)
  prompt = random.choice(['>', '<'])
  solution = ''.join(memorize[::1 if prompt == '>' else -1])
  return Problem('short number', memorize, prompt, solution, 3000)


def number_problem_long(number_length=8):
  prompt = '>'
  memorize = rnd_number(number_length)
  solution = memorize
  return Problem('long number', memorize, prompt, solution, 4000)


def number_problem_list(number_length=2, num_numbers=4):
  sample = [rnd_number(number_length) for _ in range(num_numbers)]
  memorize = ' '.join(sample)
  prompt = random.choice(['>', '<'])
  solution = ' '.join(sample[::1 if prompt == '>' else -1])
  return Problem('number list', memorize, prompt, solution, 2000)


def number_problem_calculate():
  a, b = random.randint(1, 20), random.randint(1, 20)
  memorize = f'{a} {b}'
  prompt = random.choice(['+', '-', '*'])
  solution = str(eval(f'{a}{prompt}{b}'))
  return Problem('calculus', memorize, prompt, solution, 2000)


def random_letters(num_letters=8):
  alphabet = 'abcdefghijklmnopqrstuvwxyz'
  memorize = ''.join([random.choice(alphabet) for _ in range(num_letters)])
  prompt = '>'
  solution = memorize
  return Problem('random word', memorize, prompt, solution, 2000)


def random_letters_and_numbers(size=8):
  alphabet = 'abcdefghijklmnopqrstuvwxyz'
  numbers = '0123456789'
  memorize = ''.join([random.choice(alphabet + numbers) for _ in range(size)])
  prompt = '='
  solution = memorize
  return Problem('random word', memorize, prompt, solution, 2000)


def word_backward():
  d = random.randint(0, len(words) - 1)
  memorize = random.sample(words[d], 1)[0]
  prompt = '<'
  solution = ''.join(memorize[::-1])
  return Problem('word reverse', memorize + ' >>', prompt, solution, 1000)


def word_forward():
  d = random.randint(0, len(words) - 1)
  memorize = random.sample(words[d], 1)[0][::-1]
  prompt = '>'
  solution = ''.join(memorize[::-1])
  return Problem('word scramble', memorize + ' <<', prompt, solution, 1000)


problems = {
  word_list_problem: 0.1,
  word_pairs_problem: 0.1,
  word_forward: 0.1,
  word_backward: 0.1,
  number_problem: 0.1,
  number_problem_long: 0.1,
  number_problem_list: 0.1,
  number_problem_calculate: 0.1,
  random_letters: 0.1,
  random_letters_and_numbers: 0.1,
}


@dataclass
class Record:
  problem: Problem
  response: str
  response_ms: int
  correct: bool

  def __repr__(self):
      return (f'{self.problem} '
              f'response={self.response}, '
              f'response_ms={self.response_ms}, '
              f'correct={self.correct}')


test_date = datetime.datetime.now()
start_time = time.time()
duration_s = None
max_nr = 50
records = []


def main(stdscr):

  curses.start_color()
  curses.use_default_colors()
  curses.init_pair(1, curses.COLOR_RED, -1)
  curses.init_pair(2, curses.COLOR_GREEN, -1)
  curses.init_pair(3, curses.COLOR_BLUE, -1)

  stdscr.clear()

  # max_y, _ = stdscr.getmaxyx()

  nr = 0
  n_correct = 0
  stats_col = 50
  response_ms_col = 65
  correction_col = 80

  while nr < max_nr:

    # if nr >= max_y - 1:  # Last line of screen
    #     stdscr.scrollok(True)
    #     stdscr.scroll()  # Scroll window up by one line or scrl(1)
    #     stdscr.move(max_y - 2, 0)

    problem_func = random.choices(list(problems.keys()), list(problems.values()))[0]
    pb = problem_func()
    memorize, prompt, solution, exposure_ms = pb.memorize, pb.prompt, pb.solution, pb.exposure_ms

    n_minutes, n_seconds = divmod(time.time() - start_time, 60)
    n_minutes, n_seconds = int(n_minutes), int(n_seconds)
    stdscr.addstr(nr, 0, memorize)
    stdscr.addstr(nr, stats_col, f'{n_correct}/{nr} {n_minutes}:{n_seconds}')
    stdscr.refresh()
    curses.napms(exposure_ms)

    stdscr.addstr(nr, 0, ' ' * len(memorize))
    stdscr.addstr(nr, 0, f'{prompt}')
    stdscr.refresh()
    stdscr.move(nr, len(prompt) + 1)

    curses.echo()
    t0 = time.time_ns()
    user_input = stdscr.getstr(nr, len(prompt) + 1, 256).decode('utf-8').strip().lower()
    response_ms = int((time.time_ns() - t0) / 1e6)
    curses.noecho()

    stdscr.addstr(nr, response_ms_col, f'{exposure_ms}/{response_ms}s')

    record = Record(pb, user_input, response_ms, True)

    if unidecode(user_input) == unidecode(solution):
      n_correct += 1
      stdscr.addstr(nr, 0, checkmark, curses.color_pair(2))
      record.correct = True
    else:
      record.correct = False
      stdscr.addstr(nr, 0, cross, curses.color_pair(1))
      stdscr.addstr(nr, correction_col, solution)

    nr += 1
    records.append(record)

  curses.endwin()

  with open('records.txt', 'a+') as f:
    f.write(test_date.strftime('%Y-%m-%d %H:%M'))
    f.write(str(int(time.time() - start_time)))
    for record in records:
      f.write(str(record))

  for record in records:
    print(record)


if __name__ == '__main__':
  curses.wrapper(main)



