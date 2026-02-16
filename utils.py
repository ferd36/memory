import random
from pathlib import Path

_UTILS_DIR = Path(__file__).resolve().parent


def rnd_number(number_length):
  """Generate a random number of a given length"""
  return ''.join([random.choice('0123456789') for _ in range(number_length)])


def load_frequencies():
  """Load frequencies from dicts/frequencies.txt and return a dictionary with approach, tower, and ground frequencies"""
  with open(_UTILS_DIR / 'dicts/frequencies.txt') as f:
    lines = f.readlines()
  
  frequencies = {'approach': [], 'tower': [], 'ground': []}
  current_section = None
  
  for line in lines:
    line = line.strip()
    if line.startswith('# Approach frequencies'):
      current_section = 'approach'
    elif line.startswith('# Tower frequencies'):
      current_section = 'tower'
    elif line.startswith('# Ground frequencies'):
      current_section = 'ground'
    elif line and current_section and not line.startswith('#'):
      frequencies[current_section].append(line)
  
  return frequencies


def levenshtein_distance(s1, s2):
    """Calculate the Levenshtein distance between two strings"""
    if len(s1) < len(s2):
      return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
      return len(s1)
    
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
      current_row = [i + 1]
      for j, c2 in enumerate(s2):
        insertions = previous_row[j + 1] + 1
        deletions = current_row[j] + 1
        substitutions = previous_row[j] + (c1 != c2)
        current_row.append(min(insertions, deletions, substitutions))
      previous_row = current_row
    
    return previous_row[-1]
