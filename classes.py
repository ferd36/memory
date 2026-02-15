from dataclasses import dataclass
from typing import Any
from unidecode import unidecode

from utils import levenshtein_distance


@dataclass
class Problem:
  name: str
  memorize: str
  prompt: str
  solution: str
  exposure_ms: int
  problem_type: str = "" # matrix or single line

  def create(**kwargs):
    pass

  def evaluate_solution(self, user_input):
    """
    Evaluate how close the user's input is to the correct solution.
    Returns a score between 0.0 (no match) and 1.0 (perfect match).
    """
    
    # Normalize both inputs using unidecode
    normalized_user = unidecode(user_input.strip().lower())
    normalized_solution = unidecode(self.solution.strip().lower())
    
    # Check for exact match first
    if normalized_user == normalized_solution:
      return 1.0
    
    # Calculate Levenshtein distance
    distance = levenshtein_distance(normalized_user, normalized_solution)
    
    # Use the maximum length as the denominator to ensure score is between 0 and 1
    max_length = max(len(normalized_user), len(normalized_solution))
    
    # Handle edge case where both strings are empty
    if max_length == 0:
      return 1.0
    
    # Calculate score: 1.0 for perfect match, approaching 0.0 for maximum distance
    score = max(0.0, 1.0 - (distance / max_length))
    
    return score

  def to_dict(self):
    return {
      'name': self.name,
      'memorize': self.memorize,
      'prompt': self.prompt,
      'solution': self.solution,
      'exposure_ms': self.exposure_ms,
      'problem_type': self.problem_type
    }

  def __repr__(self):
    return (f'name={self.name}, '
            f'memorize={self.memorize} '
            f'prompt={self.prompt} '
            f'solution={self.solution} '
            f'exposure_ms={self.exposure_ms} '
            f'problem_type={self.problem_type}')


@dataclass
class Record:
    problem: Any  # Problem object
    response: str
    response_ms: int
    score: float  # Score between 0.0 and 1.0

    def to_dict(self):
        return {
            'problem': self.problem.to_dict(),
            'response': self.response,
            'response_ms': self.response_ms,
            'score': self.score,
            'correct': self.score >= 1.0  # Keep for backward compatibility
        }

    @property
    def correct(self):
        """Backward compatibility property - returns True if score is perfect"""
        return self.score >= 1.0