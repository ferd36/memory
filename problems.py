import random
from pathlib import Path

from classes import Problem
from utils import rnd_number, load_frequencies
from unidecode import unidecode

_PROBLEMS_DIR = Path(__file__).resolve().parent


def _dict_path(name: str) -> Path:
    return _PROBLEMS_DIR / 'dicts' / name
dict_paths = [
  '/usr/share/dict/words',
  str(_PROBLEMS_DIR / 'dicts/common_english_words.txt'),
  str(_PROBLEMS_DIR / 'dicts/common_french_words.txt'),
  str(_PROBLEMS_DIR / 'dicts/german_words.txt'),
]

words = []


def load_dicts(word_length_min=4, word_length_max=6):
  for dict_path in dict_paths:
    if not Path(dict_path).exists():
      continue
    with open(dict_path) as f:
      words_tmp = [w.strip().lower() for w in f if w.strip().isalpha()]
      if "german" in dict_path:
        words_tmp = [w.replace('ß', 'ss') for w in words_tmp]
      words.append([w for w in words_tmp if word_length_min <= len(w) <= word_length_max])


load_dicts()

# Fallback if no dict files found
if not words or all(len(w) == 0 for w in words):
    words = [['test', 'word', 'list', 'fall', 'back', 'data', 'here', 'more', 'some', 'make', 'take', 'from']]


def _pick_word_list(min_size: int) -> list[str]:
    """Pick a non-empty word list. Raises ValueError if none available."""
    available = [w for w in words if len(w) >= min_size]
    if not available:
        raise ValueError("No word list with enough entries")
    return random.choice(available)


class WordListProblem(Problem):
  @staticmethod
  def create(num_words=4, **kwargs):
    wlist = _pick_word_list(num_words)
    sample = random.sample(wlist, num_words)
    memorize = ' '.join(sample)
    prompt = random.choice(['>', '<'])
    solution = ' '.join(sample[::1 if prompt == '>' else -1])
    return Problem('word list', memorize, prompt, solution, 4000, 'single line')


class WordPairsProblem(Problem):
  @staticmethod
  def create(num_pairs=3, **kwargs):
    wlist = _pick_word_list(2 * num_pairs)
    sample = random.sample(wlist, 2 * num_pairs)
    pairs = [(sample[2*i], sample[1 + 2 * i]) for i in range(num_pairs)]
    memorize = ' '.join(f'{p[0]}:{p[1]}' for p in pairs)
    chosen = random.randint(0, num_pairs - 1)
    prompt = f'? {pairs[chosen][0]}'
    solution = pairs[chosen][1]
    return Problem('word pairs', memorize, prompt, solution, 4000, 'matrix')


class WordNumberPairsProblem(Problem):
  @staticmethod
  def create(num_pairs=3, number_length=4, **kwargs):
    wlist = _pick_word_list(num_pairs)
    sample = random.sample(wlist, num_pairs)
    pairs = [(sample[i], rnd_number(number_length)) for i in range(num_pairs)]
    memorize = ' '.join(f'{p[0]}:{p[1]}' for p in pairs)
    chosen = random.randint(0, num_pairs - 1)
    prompt = f'? {pairs[chosen][0]}'
    solution = pairs[chosen][1]
    return Problem('word number pairs', memorize, prompt, solution, 4000, 'matrix')


class NumberProblem(Problem):
  @staticmethod
  def create(number_length=6, **kwargs):
    memorize = rnd_number(number_length)
    prompt = random.choice(['>', '<'])
    solution = ''.join(memorize[::1 if prompt == '>' else -1])
    return Problem('short number', memorize, prompt, solution, 3000, 'single line')


class NumberLongProblem(Problem):
  @staticmethod
  def create(number_length=8, **kwargs):
    prompt = '>'
    memorize = rnd_number(number_length)
    solution = memorize
    return Problem('long number', memorize, prompt, solution, 4000, 'single line')


class NumberListProblem(Problem):
  @staticmethod
  def create(number_length=2, num_numbers=4, **kwargs):
    sample = [rnd_number(number_length) for _ in range(num_numbers)]
    memorize = ' '.join(sample)
    prompt = random.choice(['>', '<'])
    solution = ' '.join(sample[::1 if prompt == '>' else -1])
    return Problem('number list', memorize, prompt, solution, 2000, 'single line')


class NumberCalculateProblem(Problem):
  @staticmethod
  def create(**kwargs):
    a, b = random.randint(1, 20), random.randint(1, 20)
    memorize = f'{a} {b}'
    prompt = random.choice(['+', '-', '*'])
    ops = {'+': a + b, '-': a - b, '*': a * b}
    solution = str(ops[prompt])
    return Problem('calculus', memorize, prompt, solution, 2000, 'single line')


class RandomLettersProblem(Problem):
  @staticmethod
  def create(num_letters=8, **kwargs):
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    memorize = ''.join([random.choice(alphabet) for _ in range(num_letters)])
    prompt = '>'
    solution = memorize
    return Problem('random word', memorize, prompt, solution, 2000, 'single line')


class RandomLettersAndNumbersProblem(Problem):
  @staticmethod
  def create(size=8, **kwargs):
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    numbers = '0123456789'
    memorize = ''.join([random.choice(alphabet + numbers) for _ in range(size)])
    prompt = '='
    solution = memorize
    return Problem('random word', memorize, prompt, solution, 2000, 'single line')


class WordBackwardProblem(Problem):
  @staticmethod
  def create(**kwargs):
    wlist = _pick_word_list(1)
    memorize = random.choice(wlist)
    prompt = '<'
    solution = ''.join(memorize[::-1])
    return Problem('word reverse', memorize + ' >>', prompt, solution, 1000, 'single line')


class WordForwardProblem(Problem):
  @staticmethod
  def create(**kwargs):
    wlist = _pick_word_list(1)
    memorize = random.choice(wlist)[::-1]
    prompt = '>'
    solution = ''.join(memorize[::-1])
    return Problem('word scramble', memorize + ' <<', prompt, solution, 1000, 'single line')


class ArrowDirectionProblem(Problem):
  @staticmethod
  def create(**kwargs):
    # Unicode arrows from range U+2190 to U+21FF
    arrows = {
      'left': '←',    # U+2190
      'up': '↑',      # U+2191  
      'right': '→',   # U+2192
      'down': '↓'     # U+2193
    }
    
    directions = ['left', 'up', 'right', 'down']
    
    # Create a single line of 4-6 arrows
    num_arrows = random.randint(4, 6)
    
    # Generate random arrows for the line
    arrow_line = []
    arrow_directions = []
    
    for i in range(num_arrows):
      direction = random.choice(directions)
      arrow_line.append(arrows[direction])
      arrow_directions.append(direction)
    
    # Create display string with spacing
    memorize = ' '.join(arrow_line)
    
    # Choose a random position to ask about (1-indexed for user)
    ask_position = random.randint(1, num_arrows)
    
    prompt = f"{ask_position}"
    solution = arrow_directions[ask_position - 1]  # Convert back to 0-indexed
    
    return Problem('arrow direction', memorize, prompt, solution, 2500, 'single line')


class GeometryFormsProblem(Problem):
  @staticmethod
  def create(**kwargs):
    # Unicode geometric shapes from range U+25A0 to U+25FF
    shapes = {
      'square': ['■', '□', '▪', '▫'],     # U+25A0, U+25A1, U+25AA, U+25AB
      'triangle': ['▲', '△', '▼', '▽'],   # U+25B2, U+25B3, U+25BC, U+25BD
      'circle': ['●', '○', '◉', '◯']      # U+25CF, U+25CB, U+25C9, U+25EF
    }
    
    form_names = ['square', 'triangle', 'circle']
    
    # Create a line of 4-6 shapes
    num_shapes = random.randint(4, 6)
    
    # Generate random shapes for the line
    shape_line = []
    shape_forms = []
    
    for i in range(num_shapes):
      form_name = random.choice(form_names)
      shape_char = random.choice(shapes[form_name])
      shape_line.append(shape_char)
      shape_forms.append(form_name)
    
    # Create display string with spacing
    memorize = ' '.join(shape_line)
    
    # Choose a random position to ask about (1-indexed for user)
    ask_position = random.randint(1, num_shapes)
    
    prompt = f"{ask_position}"
    solution = shape_forms[ask_position - 1]  # Convert back to 0-indexed
    
    return Problem('geometry forms', memorize, prompt, solution, 2500, 'single line')


class FlightInfoProblem(Problem):
  @staticmethod
  def create(num_flights=1, **kwargs):

    airlines = []
    with open(_dict_path('airlines.txt')) as f:
      for line in f:
        code, name = line.strip().split(',')
        airlines.append((code, name))
    

    destinations = []
    with open(_dict_path('cities.txt')) as f:
      destinations = [line.strip() for line in f if line.strip()]
    
    flights = []
    used_airlines = []
    used_destinations = []
    used_gates = []
    
    def generate_random_gate():
      gate_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
      letter = random.choice(gate_letters)
      number = random.randint(1, 99)
      return f"{letter}{number}"
    
    for i in range(num_flights):
      airline_code, airline_name = random.choice([a for a in airlines if a[0] not in used_airlines])
      used_airlines.append(airline_code)
      
      destination = random.choice([d for d in destinations if d not in used_destinations])
      used_destinations.append(destination)
      
      gate = generate_random_gate()
      while gate in used_gates:
        gate = generate_random_gate()
      used_gates.append(gate)
      
      flight_num = random.randint(100, 9999)
      
      hour = random.randint(6, 23)
      minute = random.choice([0, 15, 30, 45])
      time_str = f"{hour:02d}:{minute:02d}"
      
      flight_info = f"{airline_code} {flight_num} {destination} {gate} {time_str}"
      flights.append(flight_info)
    
    memorize = ""
    for i, flight in enumerate(flights, 1):
      if i > 1:
        memorize += "\n"
      memorize += f"{i}. {flight}"
    
    ask_flight = random.randint(1, num_flights)
    prompt = f"{ask_flight}"
    solution = flights[ask_flight - 1]  # Convert to 0-indexed
    
    return Problem('flight info', memorize, prompt, solution, 5000, 'single line')


class TokyoMetroProblem(Problem):
  @staticmethod
  def create(num_stations=3, **kwargs):
    # Load Tokyo Metro lines and stations from file
    metro_lines = {}
    current_line_english = None
    current_line_kanji = None
    
    with open(_dict_path('tokyo_metro.txt')) as f:
      for line in f:
        line = line.strip()
        if not line:
          continue
        
        # Check if this is a line name (format "English:Kanji")
        if ',' not in line and ':' in line:
          english_line, kanji_line = line.split(':', 1)
          current_line_english = english_line.strip()
          current_line_kanji = kanji_line.strip()
          metro_lines[current_line_english] = {
            'english': [],
            'kanji': [],
            'line_kanji': current_line_kanji
          }
        elif current_line_english and ',' in line:
          # This is a station list for the current line in format "English:Kanji"
          station_pairs = [station.strip() for station in line.split(',')]
          for pair in station_pairs:
            if ':' in pair:
              english, kanji = pair.split(':', 1)
              metro_lines[current_line_english]['english'].append(english.strip())
              metro_lines[current_line_english]['kanji'].append(kanji.strip())
            else:
              # Fallback for stations without kanji
              metro_lines[current_line_english]['english'].append(pair.strip())
              metro_lines[current_line_english]['kanji'].append(pair.strip())
    
    # Generate itinerary with num_stations stops
    itinerary = []
    used_combinations = set()
    
    # Generate starting time (7:00 - 21:00)
    start_hour = random.randint(7, 21)
    start_minute = random.choice([0, 15, 30, 45])
    current_minutes = start_hour * 60 + start_minute
    
    for i in range(num_stations):
      # Pick a random line and station
      line_name = random.choice(list(metro_lines.keys()))
      line_data = metro_lines[line_name]
      station_index = random.randint(0, len(line_data['english']) - 1)
      english_station = line_data['english'][station_index]
      kanji_station = line_data['kanji'][station_index]
      
      # Ensure we don't repeat the same line-station combination
      combo = (line_name, english_station)
      attempts = 0
      while combo in used_combinations and attempts < 50:
        line_name = random.choice(list(metro_lines.keys()))
        line_data = metro_lines[line_name]
        station_index = random.randint(0, len(line_data['english']) - 1)
        english_station = line_data['english'][station_index]
        kanji_station = line_data['kanji'][station_index]
        combo = (line_name, english_station)
        attempts += 1
      
      used_combinations.add(combo)
      
      # Format time
      hour = (current_minutes // 60) % 24
      minute = current_minutes % 60
      time_str = f"{hour:02d}:{minute:02d}"
      
      itinerary.append((english_station, kanji_station, time_str))
      
      # Add 5-15 minutes for next station
      current_minutes += random.randint(5, 15)
    
    # Create memorize string (using kanji for display)
    memorize_parts = []
    for i, (english_station, kanji_station, time) in enumerate(itinerary):
      part = f"{kanji_station} {time}"
      memorize_parts.append(part)
    
    memorize = " → ".join(memorize_parts)
    
    # Choose which station to ask about (1-indexed)
    ask_position = random.randint(1, num_stations)
    prompt = f"{ask_position}"
    # Solution uses English (what they need to type)
    solution = f"{itinerary[ask_position - 1][0]} {itinerary[ask_position - 1][2]}"
    
    return Problem('tokyo metro', memorize, prompt, solution, 4000, 'single line')


class AppointmentsProblem(Problem):
  @staticmethod
  def create(num_appointments=3, **kwargs):
    # List of possible appointment types
    appointment_types = [
      'Doctor', 'Dentist', 'Plumber', 'Car repair', 'Electrician',
      'Hair', 'Vet', 'Lawyer', 'Accountant', 'Mechanic',
      'Eye exam', 'PT', 'Massage', 'Interview',
      'Bank', 'Grocery', 'Insurance', 'Tax',
      'Computer', 'Inspection', 'Cleaning',
      'Piano', 'Tutoring', 'Chiropractor', 'Orthodontist'
    ]
    
    # Generate appointment times and types
    appointments = []
    used_times = set()
    used_types = set()
    
    # Generate starting time between 8:00 and 17:00 (office hours)
    for i in range(num_appointments):
      # Generate a unique time
      attempts = 0
      while attempts < 100:  # Prevent infinite loops
        hour = random.randint(8, 17)
        minute = random.choice([0, 15, 30, 45])  # Quarter-hour intervals
        time_str = f"{hour:02d}:{minute:02d}"
        
        if time_str not in used_times:
          used_times.add(time_str)
          
          # Pick a unique appointment type
          available_types = [t for t in appointment_types if t not in used_types]
          if not available_types:  # If all types used, reset
            used_types.clear()
            available_types = appointment_types
          
          appointment_type = random.choice(available_types)
          used_types.add(appointment_type)
          
          appointments.append((time_str, appointment_type))
          break
        attempts += 1
      
      # If we couldn't find a unique time, just use a random one
      if attempts >= 100:
        hour = random.randint(8, 17)
        minute = random.choice([0, 15, 30, 45])
        time_str = f"{hour:02d}:{minute:02d}"
        appointment_type = random.choice(appointment_types)
        appointments.append((time_str, appointment_type))
    
    # Sort appointments by time for realistic scheduling
    appointments.sort(key=lambda x: x[0])
    
    # Create memorize string on one line
    memorize_parts = []
    for i, (time, apt_type) in enumerate(appointments, 1):
      memorize_parts.append(f"{i}. {time} {apt_type}")
    
    memorize = "  ".join(memorize_parts)
    
    # Choose which appointment to ask about (1-indexed)
    ask_appointment = random.randint(1, num_appointments)
    prompt = f"{ask_appointment}"
    solution = f"{appointments[ask_appointment - 1][0]} {appointments[ask_appointment - 1][1]}"
    
    return Problem('appointments', memorize, prompt, solution, 3500, 'single line')


class AnagramProblem(Problem):
  @staticmethod
  def create(**kwargs):
    # Use existing word lists from dictionaries (length 4-6)
    if not words:
      load_dicts(4, 6)  # Load words of length 4-6
    
    # Only use English (index 1) and French (index 2) common word dictionaries
    # dict_paths[1] = 'dicts/common_english_words.txt'
    # dict_paths[2] = 'dicts/common_french_words.txt'
    available_dicts = []
    dict_languages = {}
    
    if len(words) > 1 and len(words[1]) > 0:  # English dictionary
      available_dicts.append(1)
      dict_languages[1] = 'English'
    
    if len(words) > 2 and len(words[2]) > 0:  # French dictionary
      available_dicts.append(2)
      dict_languages[2] = 'French'
    
    if not available_dicts:
      try:
        wlist = _pick_word_list(1)
        original_word = random.choice(wlist)
        dict_index = 0
        language = 'English'
      except ValueError:
        return Problem('anagram', 'No words available', '>', 'error', 2000, 'single line')
    else:
      dict_index = random.choice(available_dicts)
      language = dict_languages[dict_index]
      original_word = random.choice(words[dict_index])
    
    # Create anagram by shuffling letters
    anagram_word = create_anagram(original_word)
    
    # Make sure anagram is different from original
    attempts = 0
    while anagram_word.lower() == original_word.lower() and attempts < 20:
      anagram_word = create_anagram(original_word)
      attempts += 1
    
    # Combine anagram and language in prompt
    memorize = f"{anagram_word} ({language})"
    
    # Create a custom AnagramProblem instance to store language info
    problem = AnagramProblem('anagram', memorize, '>', original_word, 3000, 'single line')
    # Store additional info for evaluation
    problem._dict_index = dict_index
    problem._language = language
    return problem

  def evaluate_solution(self, user_input):
    """Custom evaluation that accepts valid anagrams from the dictionary"""
    if user_input is None:
      return 0.0

    # Normalize with unidecode to remove accents
    user_normalized = unidecode(str(user_input).lower().strip())
    solution_normalized = unidecode(self.solution.lower())
    
    # First check exact match
    if user_normalized == solution_normalized:
      return 1.0
    
    # Check if it's a valid anagram and in the dictionary
    if self._is_valid_anagram(user_normalized, solution_normalized):
      return 1.0
    
    # Fall back to standard evaluation (Levenshtein distance)
    return super().evaluate_solution(user_input)
  
  def _is_valid_anagram(self, user_word, original_word):
    """Check if user_word is a valid anagram of original_word and exists in dictionary"""
    
    # Check if letters match (anagram test) - both should already be normalized
    if sorted(user_word) != sorted(original_word):
      return False
    
    # Check if the anagram exists in the appropriate dictionary
    if not hasattr(self, '_dict_index'):
      return False
    
    # Ensure words are loaded
    if not words:
      load_dicts(4, 6)
    
    # Check if user's word exists in the same dictionary that was used
    # Normalize dictionary words with unidecode for comparison
    dict_index = getattr(self, '_dict_index', 1)
    if dict_index < len(words) and len(words[dict_index]) > 0:
      normalized_dict_words = [unidecode(w.lower()) for w in words[dict_index]]
      return user_word in normalized_dict_words
    
    return False


def create_anagram(word):
  """Create an anagram by shuffling the letters of a word"""
  letters = list(word.lower())
  random.shuffle(letters)
  return ''.join(letters)


class SequenceRecognitionProblem(Problem):
  @staticmethod
  def create(**kwargs):
    """Generate a sequence recognition problem with the first 5 elements"""
    # Dictionary of sequence generators - easy to add new ones!
    sequence_generators = {
      'arithmetic': SequenceRecognitionProblem._generate_arithmetic,
      'geometric': SequenceRecognitionProblem._generate_geometric,
      'fibonacci': SequenceRecognitionProblem._generate_fibonacci,
      'squares': SequenceRecognitionProblem._generate_squares,
      'powers_of_2': SequenceRecognitionProblem._generate_powers_of_2,
      'triangular': SequenceRecognitionProblem._generate_triangular,
      'cubes': SequenceRecognitionProblem._generate_cubes,
      'primes': SequenceRecognitionProblem._generate_primes,
      'factorial': SequenceRecognitionProblem._generate_factorial,
      'alternating': SequenceRecognitionProblem._generate_alternating,
      'recursive': SequenceRecognitionProblem._generate_recursive,
      'exponential': SequenceRecognitionProblem._generate_exponential,
      'lucas': SequenceRecognitionProblem._generate_lucas,
      'padovan': SequenceRecognitionProblem._generate_padovan,
      'catalan': SequenceRecognitionProblem._generate_catalan,
    }
    
    # Randomly select a sequence type
    sequence_type = random.choice(list(sequence_generators.keys()))
    generator = sequence_generators[sequence_type]
    
    # Generate the sequence (first 6 elements)
    sequence = generator()
    
    # Show first 5, ask for 6th
    shown_sequence = sequence[:5]
    next_element = sequence[5]
    
    # Format the problem
    memorize = ' '.join(map(str, shown_sequence))
    prompt = '>'
    solution = str(next_element)
    
    return Problem('sequence recognition', memorize, prompt, solution, 3000, 'single line')
  
  @staticmethod
  def _generate_arithmetic():
    """Arithmetic sequence: a, a+d, a+d*2, ..."""
    start = random.randint(1, 20)
    diff = random.randint(2, 10)
    return [start + i * diff for i in range(6)]
  
  @staticmethod
  def _generate_geometric():
    """Geometric sequence: a, a*r, a*r^2, ..."""
    start = random.randint(1, 5)
    ratio = random.choice([2, 3])  # Keep numbers manageable
    return [start * (ratio ** i) for i in range(6)]
  
  @staticmethod
  def _generate_fibonacci():
    """Fibonacci-like sequence: a, b, a+b, a+2b, 2a+3b, ..."""
    a, b = random.randint(1, 5), random.randint(1, 5)
    sequence = [a, b]
    for i in range(4):  # Generate 4 more elements
      sequence.append(sequence[-1] + sequence[-2])
    return sequence
  
  @staticmethod
  def _generate_squares():
    """Perfect squares: 1^2, 2^2, 3^2, ..."""
    start = random.randint(1, 8)
    return [(start + i) ** 2 for i in range(6)]
  
  @staticmethod
  def _generate_powers_of_2():
    """Powers of 2: 2^1, 2^2, 2^3, ..."""
    start_power = random.randint(0, 4)
    return [2 ** (start_power + i) for i in range(6)]
  
  @staticmethod
  def _generate_triangular():
    """Triangular numbers: 1, 3, 6, 10, 15, ..."""
    start = random.randint(1, 5)
    sequence = []
    for i in range(6):
      n = start + i
      triangular = n * (n + 1) // 2
      sequence.append(triangular)
    return sequence
  
  @staticmethod
  def _generate_cubes():
    """Perfect cubes: 1^3, 2^3, 3^3, ..."""
    start = random.randint(1, 6)
    return [(start + i) ** 3 for i in range(6)]

  @staticmethod
  def _generate_primes():
    """Prime numbers sequence"""
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
    start_idx = random.randint(0, len(primes) - 6)
    return primes[start_idx:start_idx + 6]

  @staticmethod
  def _generate_factorial():
    """Factorial sequence: 1!, 2!, 3!, ..."""
    start = random.randint(1, 4)
    sequence = []
    for i in range(6):
      n = start + i
      factorial = 1
      for j in range(1, n + 1):
        factorial *= j
      sequence.append(factorial)
    return sequence

  @staticmethod
  def _generate_alternating():
    """Alternating arithmetic sequence: a, a+d, a+2d, a+3d, a+4d, a+5d with alternating signs"""
    start = random.randint(1, 10)
    diff = random.randint(2, 8)
    sequence = []
    for i in range(6):
      if i % 2 == 0:
        sequence.append(start + i * diff)
      else:
        sequence.append(-(start + i * diff))
    return sequence

  @staticmethod
  def _generate_recursive():
    """Recursive sequence: a(n) = a(n-1) + a(n-2) + c"""
    a, b = random.randint(1, 5), random.randint(1, 5)
    c = random.randint(1, 3)
    sequence = [a, b]
    for i in range(4):
      sequence.append(sequence[-1] + sequence[-2] + c)
    return sequence

  @staticmethod
  def _generate_exponential():
    """Exponential sequence: a * b^n"""
    a = random.randint(1, 3)
    b = random.choice([2, 3, 4])
    return [a * (b ** i) for i in range(6)]

  @staticmethod
  def _generate_lucas():
    """Lucas sequence: L(n) = L(n-1) + L(n-2) with L(0)=2, L(1)=1"""
    sequence = [2, 1]
    for i in range(4):
      sequence.append(sequence[-1] + sequence[-2])
    return sequence

  @staticmethod
  def _generate_padovan():
    """Padovan sequence: P(n) = P(n-2) + P(n-3) with P(0)=1, P(1)=1, P(2)=1"""
    sequence = [1, 1, 1]
    for i in range(3):
      sequence.append(sequence[-2] + sequence[-3])
    return sequence

  @staticmethod
  def _generate_catalan():
    """Catalan numbers: C(n) = (2n)!/(n!(n+1)!)"""
    def catalan(n):
      if n <= 1:
        return 1
      return catalan(n-1) * (4*n - 2) // (n + 1)
    
    start = random.randint(0, 3)
    return [catalan(start + i) for i in range(6)]


class MetarProblem(Problem):
  @staticmethod
  def create(**kwargs):
    """Generate a METAR/TAF aviation weather report memorization problem"""
    
    # Airport codes (mix of major international airports)
    airports = ['KJFK', 'KLAX', 'KORD', 'KATL', 'KDEN', 'KDFW', 'KSEA', 'KLAS', 
                'KMIA', 'KBOS', 'KPHX', 'KSFO', 'KIAD', 'KMSP', 'KDTW', 'KPHL',
                'EGLL', 'LFPG', 'EDDF', 'EHAM', 'LIRF', 'LEMD', 'LOWW', 'ESSA',
                'RJTT', 'VHHH', 'WSSS', 'YSSY', 'NZAA', 'OMDB', 'OTHH', 'RKSI',
                'CYYZ', 'CYVR', 'SBGR', 'SAEZ', 'FACT', 'HECA', 'VIDP', 'UUEE']
    
    # Generate METAR components
    airport = random.choice(airports)
    
    # Date/time (DDHHMMZ format)
    day = random.randint(1, 31)
    hour = random.randint(0, 23)
    minute = random.choice([0, 30])  # Usually on the hour or half-hour
    datetime_str = f"{day:02d}{hour:02d}{minute:02d}Z"
    
    # Wind (direction/speed)
    wind_dir = random.randint(1, 36) * 10  # Wind direction in 10-degree increments
    wind_speed = random.randint(5, 25)
    is_variable = random.random() < 0.1  # 10% chance of variable winds
    if is_variable:
      wind = "VRB"
    else:
      wind = f"{wind_dir:03d}"
    wind += f"{wind_speed:02d}KT"
    
    # Visibility
    visibility = random.choice(['10SM', '7SM', '5SM', '3SM', '1SM', '1/2SM'])
    
    # Weather phenomena (optional)
    weather_phenomena = ['', '-RA', 'RA', '+RA', '-SN', 'SN', 'FG', 'BR', 'HZ']
    weather = random.choice(weather_phenomena)
    
    # Cloud layers
    cloud_types = ['FEW', 'SCT', 'BKN', 'OVC']
    cloud_altitudes = ['008', '015', '025', '035', '050', '080', '120']
    
    if random.random() < 0.2:  # 20% chance of clear skies
      clouds = 'CLR'
    else:
      cloud_type = random.choice(cloud_types)
      cloud_alt = random.choice(cloud_altitudes)
      clouds = f"{cloud_type}{cloud_alt}"
    
    # Temperature/Dewpoint
    temp = random.randint(-10, 35)
    dewpoint = temp - random.randint(0, 15)  # Dewpoint is always <= temperature
    temp_str = f"{temp:02d}" if temp >= 0 else f"M{abs(temp):02d}"
    dewpoint_str = f"{dewpoint:02d}" if dewpoint >= 0 else f"M{abs(dewpoint):02d}"
    temp_dewpoint = f"{temp_str}/{dewpoint_str}"
    
    # Altimeter setting
    altimeter = f"A{random.randint(2800, 3100)}"
    
    # Build complete METAR
    metar_parts = [airport, datetime_str, wind, visibility]
    if weather:
      metar_parts.append(weather)
    metar_parts.extend([clouds, temp_dewpoint, altimeter])
    
    full_metar = ' '.join(metar_parts)
    
    # Choose what to ask for
    question_types = [
      ('airport', airport, 'Airport code?'),
      ('wind_direction', "VRB" if is_variable else f"{wind_dir:03d}", 'Wind direction?'),
      ('wind_speed', f"{wind_speed}", 'Wind speed (knots)?'),
      ('visibility', visibility, 'Visibility?'),
      ('clouds', clouds, 'Cloud coverage?'),
      ('temperature', str(temp), 'Temperature (°C)?'),
      ('altimeter', altimeter, 'Altimeter setting?')
    ]
    
    question_type, answer, prompt = random.choice(question_types)
    
    return Problem('metar', full_metar, prompt, answer, 6000, 'single line')


class AtcProblem(Problem):
  _airlines = None
  _frequencies = None

  @classmethod
  def _load_airlines(cls):
      if cls._airlines is None:
          with open(_dict_path('airlines.txt')) as f:
              cls._airlines = [line.strip().split(',')[0] for line in f]

  @classmethod
  def _load_frequencies(cls):
      if cls._frequencies is None:
          cls._frequencies = load_frequencies()

  @staticmethod
  def create(**kwargs):
    """Generate ATC IFR departure/landing instructions"""
    AtcProblem._load_airlines()
    AtcProblem._load_frequencies()
    
    # Aircraft callsigns (mix of airlines and general aviation)
    flight_numbers = [f"{random.choice(AtcProblem._airlines)}{random.randint(100, 9999)}" for _ in range(5)]
    ga_callsigns = [f"N{random.randint(100, 999)}{random.choice(['AB', 'CD', 'EF', 'GH'])}" for _ in range(3)]
    callsigns = flight_numbers + ga_callsigns
    
    # Runways (common runway numbers)
    runways = ['09L', '09R', '27L', '27R', '04L', '04R', '22L', '22R', 
               '01L', '01R', '19L', '19R', '16L', '16R', '34L', '34R',
               '08L', '26R', '06R', '24L', '12L', '30R', '15L', '33R',
               '03L', '21R', '05L', '23R', '07L', '25R', '10L', '28R', 
               '13L', '31R']
    
    # Instruction type (departure, arrival, or vector)
    instruction_type = random.choice(['departure', 'arrival', 'vector'])
    
    callsign = random.choice(callsigns)
    runway = random.choice(runways)
    
    if instruction_type == 'departure':
      # Generate departure instruction
      squawk = ''.join([str(random.randint(0, 7)) for _ in range(4)])
      if squawk[0] == '0':  # Ensure first digit is 1-7
        squawk = str(random.randint(1, 7)) + squawk[1:]
      departure_heading = random.randint(1, 36) * 10
      initial_altitude = random.choice([3000, 4000, 5000, 6000, 8000, 10000])
      
      # Departure frequencies
      departure_freq = random.choice(AtcProblem._frequencies['approach'])
      
      instruction = f"{callsign}, runway {runway}, cleared for takeoff, fly heading {departure_heading:03d}, climb and maintain {initial_altitude}, squawk {squawk}, contact departure {departure_freq}"
      
      # Choose what to ask for
      questions = [
        ('callsign', callsign, 'Aircraft callsign?'),
        ('runway', runway, 'Departure runway?'),
        ('heading', f"{departure_heading:03d}", 'Initial heading?'),
        ('altitude', str(initial_altitude), 'Initial altitude?'),
        ('squawk', squawk, 'Squawk code?'),
        ('frequency', departure_freq, 'Departure frequency?')
      ]
      
    elif instruction_type == 'arrival':
      # Generate arrival instruction
      approach_type = random.choice(['ILS', 'RNAV', 'VOR', 'GPS'])
      final_altitude = random.choice([2000, 2500, 3000, 3500, 4000])
      speed_restriction = random.choice([180, 200, 210, 220, 250])
      
      # Approach frequencies  
      approach_freq = random.choice(AtcProblem._frequencies['tower'])
      
      instruction = f"{callsign}, descend and maintain {final_altitude}, reduce speed {speed_restriction} knots, cleared {approach_type} approach runway {runway}, contact tower {approach_freq}"
      
      # Choose what to ask for
      questions = [
        ('callsign', callsign, 'Aircraft callsign?'),
        ('runway', runway, 'Landing runway?'),
        ('altitude', str(final_altitude), 'Final altitude?'),
        ('speed', str(speed_restriction), 'Speed restriction (knots)?'),
        ('approach_type', approach_type, 'Approach type?'),
        ('frequency', approach_freq, 'Tower frequency?')
      ]
      
    else:  # vector
      # Generate vector instruction
      vector_types = [
        'traffic',
        'spacing', 
        'final_approach',
        'navigation',
        'weather_deviation'
      ]
      
      vector_type = random.choice(vector_types)
      vector_heading = random.randint(1, 36) * 10
      
      if vector_type == 'traffic':
        instruction = f"{callsign}, turn left heading {vector_heading:03d}, vector for traffic"
        reason = "traffic"
      elif vector_type == 'spacing':
        instruction = f"{callsign}, turn right heading {vector_heading:03d}, vector for spacing"
        reason = "spacing"
      elif vector_type == 'final_approach':
        instruction = f"{callsign}, turn left heading {vector_heading:03d}, vector to final approach course runway {runway}"
        reason = "final approach"
      elif vector_type == 'navigation':
        waypoints = ['STAR1', 'FIXME', 'ABCDE', 'POINT', 'NAVPT', 'INTER']
        waypoint = random.choice(waypoints)
        instruction = f"{callsign}, turn right heading {vector_heading:03d}, vector direct {waypoint}"
        reason = waypoint
      else:  # weather_deviation
        instruction = f"{callsign}, turn left heading {vector_heading:03d}, vector for weather deviation, advise when able to resume course"
        reason = "weather"
      
      # Choose what to ask for
      questions = [
        ('callsign', callsign, 'Aircraft callsign?'),
        ('heading', f"{vector_heading:03d}", 'Vector heading?'),
        ('turn_direction', 'left' if 'left' in instruction else 'right', 'Turn direction?'),
        ('reason', reason, 'Vector reason?')
      ]
      
      if vector_type == 'final_approach':
        questions.append(('runway', runway, 'Runway?'))
    
    question_type, answer, prompt = random.choice(questions)
    
    return Problem('atc', instruction, prompt, answer, 5000, 'single line')


class FlightPlanProblem(Problem):
  _vors = None
  _frequencies = None

  @classmethod
  def _load_vors(cls):
    if cls._vors is None:
      with open(_dict_path('vors.txt')) as f:
        cls._vors = [line.strip() for line in f]

  @classmethod
  def _load_frequencies(cls):
    if cls._frequencies is None:
      cls._frequencies = load_frequencies()

  @staticmethod
  def create(num_waypoints=5, **kwargs):
    FlightPlanProblem._load_vors()
    FlightPlanProblem._load_frequencies()
    
    vor_list = FlightPlanProblem._vors
    approach_freqs = FlightPlanProblem._frequencies['approach']
    tower_freqs = FlightPlanProblem._frequencies['tower']
    ground_freqs = FlightPlanProblem._frequencies['ground']
    
    # Generate flight plan waypoints
    waypoints = []
    used_vors = set()
    for i in range(num_waypoints):
      available_vors = [v for v in vor_list if v not in used_vors]
      if not available_vors:  # Fallback if we run out
        available_vors = vor_list
      vor = random.choice(available_vors)
      used_vors.add(vor)
      heading = random.randint(0, 359)
      altitude = random.choice([3000, 5000, 7000, 9000, 11000, 13000, 15000, 17000, 19000, 21000, 23000, 25000, 27000, 29000, 31000, 33000, 35000, 37000, 39000, 41000])
      freq_type = random.choice(['approach', 'tower', 'ground'])
      
      if freq_type == 'approach':
        freq = random.choice(approach_freqs)
        contact = 'Approach'
      elif freq_type == 'tower':
        freq = random.choice(tower_freqs)
        contact = 'Tower'
      else:
        freq = random.choice(ground_freqs)
        contact = 'Ground'
      
      waypoint = f"{vor} {heading:03d}° {altitude:,}ft {freq}MHz {contact}"
      waypoints.append(waypoint)
    
    memorize = '\n'.join(waypoints)
    
    # Choose a random waypoint to ask about
    chosen_idx = random.randint(0, num_waypoints - 1)
    chosen_waypoint = waypoints[chosen_idx]
    
    # Ask about different aspects randomly
    aspect = random.choice(['vor', 'heading', 'altitude', 'frequency', 'contact'])
    
    if aspect == 'vor':
      prompt = f"VOR at waypoint {chosen_idx + 1}?"
      solution = chosen_waypoint.split()[0]
    elif aspect == 'heading':
      prompt = f"Heading at waypoint {chosen_idx + 1}?"
      solution = chosen_waypoint.split()[1].replace('°', '')
    elif aspect == 'altitude':
      prompt = f"Altitude at waypoint {chosen_idx + 1}?"
      solution = chosen_waypoint.split()[2].replace('ft', '').replace(',', '')
    elif aspect == 'frequency':
      prompt = f"Frequency at waypoint {chosen_idx + 1}?"
      solution = chosen_waypoint.split()[3].replace('MHz', '')
    else:  # contact
      prompt = f"Contact at waypoint {chosen_idx + 1}?"
      solution = chosen_waypoint.split()[4]
    
    return Problem('flight plan', memorize, prompt, solution, 6000, 'multiline')


class RoadProblem(Problem):
  _street_names = None

  @classmethod
  def _load_street_names(cls):
      if cls._street_names is None:
          with open(_dict_path('street_names.txt')) as f:
              cls._street_names = [line.strip() for line in f]

  @staticmethod
  def create(**kwargs):
    """Generate a road itinerary with highway numbers, exits, and distances"""
    RoadProblem._load_street_names()
    
    # Highway types and numbers
    interstate_highways = ['I-5', 'I-10', 'I-95', 'I-75', 'I-40', 'I-80', 'I-90', 'I-35', 'I-15', 'I-25']
    us_highways = ['US-101', 'US-1', 'US-50', 'US-66', 'US-Route 9', 'US-202', 'US-395', 'US-87']
    state_routes = ['SR-1', 'SR-99', 'SR-85', 'CA-1', 'Route 128', 'SR-237', 'Route 2', 'SR-92']
    
    # Street/road names from file
    street_names = RoadProblem._street_names
    
    # Generate itinerary steps
    num_steps = random.randint(3, 5)
    itinerary = []
    
    for i in range(num_steps):
      if i == 0:  # First step - start on highway
        highway = random.choice(interstate_highways + us_highways + state_routes)
        direction = random.choice(['North', 'South', 'East', 'West'])
        distance = round(random.uniform(5.2, 45.8), 1)
        step = f"Take {highway} {direction} for {distance} km"
        itinerary.append({
          'type': 'highway',
          'highway': highway,
          'direction': direction,
          'distance': distance,
          'text': step
        })
        
      elif i == num_steps - 1:  # Last step - destination
        street = random.choice(street_names)
        distance = round(random.uniform(0.3, 2.1), 1)
        turn_direction = random.choice(['left', 'right'])
        step = f"Turn {turn_direction} on {street}, destination in {distance} km"
        itinerary.append({
          'type': 'destination',
          'street': street,
          'distance': distance,
          'turn': turn_direction,
          'text': step
        })
        
      else:  # Middle steps - exits and turns
        if random.random() < 0.6:  # Highway exit
          exit_num = random.randint(1, 99)
          street = random.choice(street_names)
          distance = round(random.uniform(1.2, 8.7), 1)
          step = f"Take Exit {exit_num} for {street}, continue {distance} km"
          itinerary.append({
            'type': 'exit',
            'exit': exit_num,
            'street': street,
            'distance': distance,
            'text': step
          })
        else:  # Street turn
          street = random.choice(street_names)
          turn_direction = random.choice(['left', 'right', 'straight'])
          distance = round(random.uniform(0.8, 6.3), 1)
          if turn_direction == 'straight':
            step = f"Continue straight on {street} for {distance} km"
          else:
            step = f"Turn {turn_direction} on {street}, continue {distance} km"
          itinerary.append({
            'type': 'turn',
            'street': street,
            'turn': turn_direction,
            'distance': distance,
            'text': step
          })
    
    # Create full itinerary text
    full_itinerary = '\n'.join([step['text'] for step in itinerary])
    
    # Choose what to ask for
    step_to_ask = random.choice(itinerary)
    step_index = itinerary.index(step_to_ask) + 1
    
    if step_to_ask['type'] == 'highway':
      questions = [
        ('highway', step_to_ask['highway'], f'Highway in step {step_index}?'),
        ('direction', step_to_ask['direction'], f'Direction in step {step_index}?'),
        ('distance', str(step_to_ask['distance']), f'Distance in step {step_index} (km)?')
      ]
    elif step_to_ask['type'] == 'exit':
      questions = [
        ('exit_number', str(step_to_ask['exit']), f'Exit number in step {step_index}?'),
        ('street', step_to_ask['street'], f'Street name in step {step_index}?'),
        ('distance', str(step_to_ask['distance']), f'Distance in step {step_index} (km)?')
      ]
    elif step_to_ask['type'] == 'turn':
      questions = [
        ('street', step_to_ask['street'], f'Street name in step {step_index}?'),
        ('turn_direction', step_to_ask['turn'], f'Turn direction in step {step_index}?'),
        ('distance', str(step_to_ask['distance']), f'Distance in step {step_index} (km)?')
      ]
    else:  # destination
      questions = [
        ('street', step_to_ask['street'], 'Final street name?'),
        ('turn_direction', step_to_ask['turn'], 'Final turn direction?'),
        ('distance', str(step_to_ask['distance']), 'Distance to destination (km)?')
      ]
    
    question_type, answer, prompt = random.choice(questions)
    
    return Problem('road', full_itinerary, prompt, answer, 6000, 'multiline')


class TimeDurationProblem(Problem):
  @staticmethod
  def create(**kwargs):
    """Generate time duration calculation problems"""
    
    # Generate random times
    start_hour = random.randint(0, 23)
    start_minute = random.randint(0, 59)
    end_hour = random.randint(0, 23)
    end_minute = random.randint(0, 59)
    
    # Ensure end time is after start time (within same day)
    if end_hour < start_hour or (end_hour == start_hour and end_minute <= start_minute):
      end_hour = start_hour + random.randint(1, 8)  # Add 1-8 hours
      if end_hour >= 24:
        end_hour = 23
        if start_minute >= 59:
          end_minute = 59
        else:
          end_minute = random.randint(start_minute + 1, 59)
    
    # Format times
    start_time = f"{start_hour:02d}:{start_minute:02d}"
    end_time = f"{end_hour:02d}:{end_minute:02d}"
    
    # Calculate duration
    start_total = start_hour * 60 + start_minute
    end_total = end_hour * 60 + end_minute
    duration_minutes = end_total - start_total
    duration_hours = duration_minutes // 60
    duration_mins = duration_minutes % 60
    
    # Choose what to ask for
    question_type = random.choice(['duration', 'start_time', 'end_time'])
    
    if question_type == 'duration':
      memorize = f"Start: {start_time} | End: {end_time}"
      prompt = "Duration (HH:MM)?"
      solution = f"{duration_hours:02d}:{duration_mins:02d}"
    elif question_type == 'start_time':
      memorize = f"Duration: {duration_hours:02d}:{duration_mins:02d} | End: {end_time}"
      prompt = "Start time (HH:MM)?"
      solution = start_time
    else:  # end_time
      memorize = f"Start: {start_time} | Duration: {duration_hours:02d}:{duration_mins:02d}"
      prompt = "End time (HH:MM)?"
      solution = end_time
    
    return Problem('time duration', memorize, prompt, solution, 4000, 'single line')


class ChemicalFormulaProblem(Problem):
  @staticmethod
  def create(**kwargs):
    """Generate chemical formula memorization problems"""
    
    # Common chemical formulas with names
    formulas = {
      'H2O': 'Water',
      'CO2': 'Carbon Dioxide',
      'NaCl': 'Sodium Chloride',
      'H2SO4': 'Sulfuric Acid',
      'NaOH': 'Sodium Hydroxide',
      'HCl': 'Hydrochloric Acid',
      'NH3': 'Ammonia',
      'CH4': 'Methane',
      'C6H12O6': 'Glucose',
      'CaCO3': 'Calcium Carbonate',
      'Fe2O3': 'Iron Oxide',
      'Al2O3': 'Aluminum Oxide',
      'HNO3': 'Nitric Acid',
      'H3PO4': 'Phosphoric Acid',
      'KOH': 'Potassium Hydroxide',
      'MgO': 'Magnesium Oxide',
      'CuSO4': 'Copper Sulfate',
      'AgNO3': 'Silver Nitrate',
      'ZnCl2': 'Zinc Chloride',
      'Pb(NO3)2': 'Lead Nitrate',
      'FeCl3': 'Iron Chloride',
      'CaCl2': 'Calcium Chloride',
      'Na2CO3': 'Sodium Carbonate',
      'K2CO3': 'Potassium Carbonate',
      'LiOH': 'Lithium Hydroxide',
      'BaSO4': 'Barium Sulfate',
      'SrCl2': 'Strontium Chloride',
      'CsF': 'Cesium Fluoride',
      'RbBr': 'Rubidium Bromide'
    }
    
    # Choose a formula
    formula, name = random.choice(list(formulas.items()))
    
    # Choose what to ask for
    question_type = random.choice(['formula', 'name', 'elements'])
    
    if question_type == 'formula':
      memorize = f"Chemical: {name}"
      prompt = "Formula?"
      solution = formula
    elif question_type == 'name':
      memorize = f"Formula: {formula}"
      prompt = "Chemical name?"
      solution = name
    else:  # elements
      # Extract elements from formula (simplified)
      elements = []
      current = ""
      for char in formula:
        if char.isupper():
          if current:
            elements.append(current)
          current = char
        elif char.islower():
          current += char
        elif char.isdigit() or char in '()':
          continue  # Skip numbers and parentheses for element count
      if current:
        elements.append(current)
      
      # Remove duplicates and sort
      elements = sorted(list(set(elements)))
      
      memorize = f"Formula: {formula}"
      prompt = "Elements (space separated)?"
      solution = " ".join(elements)
    
    return Problem('chemical formula', memorize, prompt, solution, 4000, 'single line')


class NBackProblem(Problem):
    """N-back: was the item at position P the same as P-N?"""

    @staticmethod
    def create(n_back=1, seq_length=8, **kwargs):
        alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
        seq = [random.choice(alphabet) for _ in range(seq_length)]
        
        # Balance matches to ~50%
        is_match = random.random() < 0.5
        ask_pos = random.randint(n_back + 1, seq_length)
        match_pos = ask_pos - n_back
        
        if is_match:
            seq[ask_pos - 1] = seq[match_pos - 1]
        else:
            # Ensure it's NOT a match
            while seq[ask_pos - 1] == seq[match_pos - 1]:
                seq[ask_pos - 1] = random.choice(alphabet)
        
        solution = 'yes' if is_match else 'no'
        memorize = ' '.join(f'{i+1}:{s}' for i, s in enumerate(seq))
        prompt = f"Position {ask_pos} matches position {match_pos} ({n_back}-back)? (yes/no)"
        return NBackProblem('n back', memorize, prompt, solution, 4000, 'single line')

    def evaluate_solution(self, user_input: str) -> float:
        if user_input is None:
            return 0.0
        normalized = str(user_input).strip().lower()
        if normalized in ('yes', 'y'):
            return 1.0 if self.solution.lower() == 'yes' else 0.0
        if normalized in ('no', 'n'):
            return 1.0 if self.solution.lower() == 'no' else 0.0
        return super().evaluate_solution(user_input)


class SternbergProblem(Problem):
    """Sternberg: was this item in the set?"""

    @staticmethod
    def create(set_size=5, **kwargs):
        alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
        pool = list(alphabet)
        set_size = min(set_size, len(pool) - 1)
        random.shuffle(pool)
        memory_set = pool[:set_size]
        non_members = pool[set_size:]
        probe = random.choice(memory_set) if random.random() < 0.5 else random.choice(non_members)
        in_set = probe in memory_set
        solution = 'yes' if in_set else 'no'

        memorize = ' '.join(memory_set)
        prompt = f"Was '{probe}' in the set? (yes/no)"
        return SternbergProblem('sternberg', memorize, prompt, solution, 3500, 'single line')

    def evaluate_solution(self, user_input: str) -> float:
        if user_input is None:
            return 0.0
        normalized = str(user_input).strip().lower()
        if normalized in ('yes', 'y'):
            return 1.0 if self.solution.lower() == 'yes' else 0.0
        if normalized in ('no', 'n'):
            return 1.0 if self.solution.lower() == 'no' else 0.0
        return super().evaluate_solution(user_input)


class MatrixMemoryProblem(Problem):
    """Spatial grid: which cell was marked?"""

    @staticmethod
    def create(grid_size=3, num_marked=1, **kwargs):
        cells = [(r, c) for r in range(grid_size) for c in range(grid_size)]
        # Mark only 1 cell to avoid ambiguity in "recall which cell was marked"
        marked_cell = random.choice(cells)

        rows = []
        for r in range(grid_size):
            row = []
            for c in range(grid_size):
                row.append('X' if (r, c) == marked_cell else '.')
            rows.append(' '.join(row))
        memorize = '\n'.join(rows)

        col_letter = chr(ord('A') + marked_cell[1])
        row_num = marked_cell[0] + 1
        prompt = "Which cell was marked? (e.g. A1)"
        solution = f"{col_letter}{row_num}"
        return MatrixMemoryProblem('matrix memory', memorize, prompt, solution, 3000, 'matrix')

    def evaluate_solution(self, user_input: str) -> float:
        if user_input is None:
            return 0.0
        normalized = unidecode(str(user_input).strip().upper().replace(' ', ''))
        sol = self.solution.upper()
        if normalized == sol:
            return 1.0
        if len(normalized) >= 2 and len(sol) >= 2:
            if normalized == sol or normalized == sol[1] + sol[0]:
                return 1.0
        return super().evaluate_solution(user_input)


class ShoppingListProblem(Problem):
    """Shopping list with quantities."""

    @staticmethod
    def create(num_items=4, **kwargs):
        wlist = _pick_word_list(num_items)
        sample = random.sample(wlist, num_items)
        # Ensure unique quantities to avoid ambiguity in reverse lookup
        quantities = random.sample(range(1, 10), num_items)
        pairs = list(zip(quantities, sample))
        memorize = '  '.join(f'{q} {w}' for q, w in pairs)
        chosen = random.randint(0, num_items - 1)
        if random.random() < 0.5:
            prompt = f"Quantity of {pairs[chosen][1]}?"
            solution = str(pairs[chosen][0])
        else:
            prompt = f"Item for quantity {pairs[chosen][0]}?"
            solution = pairs[chosen][1]
        return Problem('shopping list', memorize, prompt, solution, 4000, 'single line')


class ColorSequenceProblem(Problem):
    """Remember a sequence of colors (R=red, G=green, B=blue, Y=yellow)."""

    @staticmethod
    def create(seq_length=5, **kwargs):
        colors = ['R', 'G', 'B', 'Y']
        seq = [random.choice(colors) for _ in range(seq_length)]
        memorize = ' '.join(seq)
        if random.random() < 0.5:
            ask_pos = random.randint(1, seq_length)
            prompt = f"Color at position {ask_pos}?"
            solution = seq[ask_pos - 1]
        else:
            prompt = "Full sequence?"
            solution = ' '.join(seq)
        return ColorSequenceProblem('color sequence', memorize, prompt, solution, 3000, 'single line')

    def evaluate_solution(self, user_input: str) -> float:
        if user_input is None:
            return 0.0
        normalized = str(user_input).strip().lower()
        color_map = {'red': 'r', 'green': 'g', 'blue': 'b', 'yellow': 'y'}
        
        # If solution is a single color (like 'R'), allow full name
        if len(self.solution) == 1:
            sol_normalized = self.solution.lower()
            if normalized == sol_normalized or color_map.get(normalized) == sol_normalized:
                return 1.0
        
        return super().evaluate_solution(user_input)


class SentenceCompletionProblem(Problem):
    """Memorize a sentence, recall the missing word."""

    _templates = [
        ("The cat sat on the ___", "mat"),
        ("She went to the ___ to buy milk", "store"),
        ("He opened the ___ and looked inside", "box"),
        ("The sun rises in the ___", "east"),
        ("Birds fly south for the ___", "winter"),
        ("She drank a cup of ___", "tea"),
        ("The book was on the ___", "shelf"),
        ("They walked along the ___", "beach"),
        ("The key was under the ___", "rug"),
        ("He ran through the ___", "park"),
    ]

    @staticmethod
    def create(**kwargs):
        sentence_tpl, word = random.choice(SentenceCompletionProblem._templates)
        # Show full sentence in memorize phase
        memorize = sentence_tpl.replace("___", word)
        # Prompt shows the sentence with the blank
        prompt = sentence_tpl
        return Problem('sentence completion', memorize, prompt, word, 4000, 'single line')


class NumberBackwardProblem(Problem):
    """Digit span backward: recall digits in reverse order."""

    @staticmethod
    def create(number_length=6, **kwargs):
        memorize = rnd_number(number_length)
        solution = memorize[::-1]
        return Problem('number backward', memorize, '<', solution, 3500, 'single line')


class NameAttributePairsProblem(Problem):
    """Name:City or Name:Profession pairs."""

    @staticmethod
    def create(num_pairs=3, **kwargs):
        wlist = _pick_word_list(2 * num_pairs)
        words_pool = random.sample(wlist, 2 * num_pairs)
        names = words_pool[:num_pairs]
        attrs = words_pool[num_pairs:]
        pairs = list(zip(names, attrs))
        memorize = '  '.join(f'{n}:{a}' for n, a in pairs)
        chosen = random.randint(0, num_pairs - 1)
        prompt = f"? {pairs[chosen][0]}"
        solution = pairs[chosen][1]
        return Problem('name attribute pairs', memorize, prompt, solution, 4000, 'matrix')


def format_problem_name(class_name):
  """Format problem class name for display by parsing camelcase"""
  import re
  
  # Remove "Problem" suffix if present
  name = class_name
  if name.endswith("Problem"):
    name = name[:-7]  # Remove "Problem"
  
  # Split camelcase into separate words
  # Insert space before uppercase letters that follow lowercase letters or other uppercase letters
  name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)  # camelCase -> camel Case
  name = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', name)  # ABCDef -> ABC Def
  
  return name.strip()


def create_problems_dict():
  """Automatically discover all Problem subclasses and assign equal probability"""
  import inspect
  
  # Get current module (problems module)
  current_module = inspect.getmodule(inspect.currentframe())
  problem_classes = []
  
  for name in dir(current_module):
    obj = getattr(current_module, name)
    if (inspect.isclass(obj) and 
        issubclass(obj, Problem) and 
        obj != Problem and
        hasattr(obj, 'create')):
      problem_classes.append(obj)
  
  if problem_classes:
    equal_prob = 1.0 / len(problem_classes)
    return {cls: equal_prob for cls in problem_classes}
  else:
    return {}