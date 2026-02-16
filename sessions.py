import gzip
import json
import statistics
import time
from collections import defaultdict
from pathlib import Path

_GZIP_MAGIC = b'\x1f\x8b'


def _read_file_content(path: Path) -> str:
    """Read file; if gzip magic, decompress then decode, else decode as utf-8."""
    raw = path.read_bytes()
    if not raw:
        return ''
    if raw[:2] == _GZIP_MAGIC:
        return gzip.decompress(raw).decode('utf-8')
    return raw.decode('utf-8')


def _write_file_gzipped(path: Path, content: str) -> None:
    """Write content as gzip-compressed bytes to path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(content.encode('utf-8'), compresslevel=9))

_SESSIONS_DIR = Path(__file__).resolve().parent
_SESSIONS_FILE = _SESSIONS_DIR / 'data' / 'training_sessions.json.gzip'


def format_score(total_questions, total_perfect, records, total_score=None, final_percentage=None):
  """Format final score and statistics by problem type as a string"""
  lines = []
  
  lines.append("Training session completed!")
  
  if total_questions == 0:
    lines.append("No questions answered.")
    return "\n".join(lines)

  if total_score is not None and final_percentage is not None:
    lines.append(f"Final score: {final_percentage:.1f}% average (total: {total_score:.2f}/{total_questions})")
    lines.append(f"Perfect answers: {total_perfect}/{total_questions} ({total_perfect/total_questions*100:.1f}%)")
  else:
    lines.append(f"Final score: {total_perfect}/{total_questions} correct answers ({total_perfect/total_questions*100:.1f}%)")
  
  # Group results by problem type
  problem_stats = {}
  for record in records:
    problem_name = record.problem.name
    if problem_name not in problem_stats:
      problem_stats[problem_name] = {'correct': 0, 'total': 0}
    
    problem_stats[problem_name]['total'] += 1
    if record.correct:
      problem_stats[problem_name]['correct'] += 1
  
  # Format stats by problem type with aligned formatting
  # Only show if there's more than 1 problem type
  if problem_stats and len(problem_stats) > 1:
    lines.append("")  # Empty line
    lines.append("Results by problem type:")
    
    # Find the longest problem type name for alignment
    max_name_length = max(len(problem_name) for problem_name in problem_stats.keys())
    
    for problem_name in sorted(problem_stats.keys()):
      stats = problem_stats[problem_name]
      correct = stats['correct']
      total = stats['total']
      percentage = (correct / total * 100) if total > 0 else 0
      
      # Format with right-aligned counts and percentage
      lines.append(f"  {problem_name:<{max_name_length}} : {correct:2d}/{total:2d} ({percentage:5.1f}%)")
  
  return "\n".join(lines)


def _read_sessions(path: Path) -> list:
    """Read sessions from file: gzip-compressed JSONL (one JSON object per line)."""
    if not path.exists():
        return []
    content = _read_file_content(path)
    if not content:
        return []
    sessions = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        sessions.append(json.loads(line))
    return sessions


def save_session_data(test_date, start_time, total_questions, correct_answers, records):
    """Append one session as a JSON line; file is stored gzip(JSONL)."""
    session_data = {
        'date': test_date.strftime('%Y-%m-%d %H:%M:%S'),
        'duration_seconds': int(time.time() - start_time),
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'score_percentage': round(correct_answers/total_questions*100, 1) if total_questions > 0 else 0,
        'records': [
            {
                'problem': r.problem.to_dict(),
                'response': r.response,
                'response_ms': r.response_ms,
                'score': r.score,
                'correct': r.score >= 1.0,
            }
            for r in records
        ],
    }
    existing = _read_file_content(_SESSIONS_FILE) if _SESSIONS_FILE.exists() else ''
    line = json.dumps(session_data, ensure_ascii=False)
    new_content = (existing.rstrip() + '\n' + line + '\n') if existing.strip() else (line + '\n')
    _write_file_gzipped(_SESSIONS_FILE, new_content)


def load_session_statistics(sessions_file=None):
    """
    Load and aggregate statistics from previous training sessions.
    
    Returns:
        dict: Aggregated statistics including overall performance, 
              problem type breakdown, and recent trends
    """
    path = Path(sessions_file) if sessions_file else _SESSIONS_FILE
    if not path.exists():
        return {
            'total_sessions': 0,
            'total_questions': 0,
            'total_correct_answers': 0,
            'overall_average_score': 0.0,
            'problem_name_stats': {},
            'recent_sessions': [],
            'best_session': None,
            'session_dates': [],
            'recent_average': 0.0
        }
    
    empty_stats = {
        'total_sessions': 0,
        'total_questions': 0,
        'total_correct_answers': 0,
        'overall_average_score': 0.0,
        'problem_name_stats': {},
        'recent_sessions': [],
        'best_session': None,
        'session_dates': [],
        'recent_average': 0.0
    }

    try:
        sessions = _read_sessions(path)
    except (json.JSONDecodeError, FileNotFoundError):
        return empty_stats  # Return empty stats if file is corrupted
    
    if not sessions:
        return empty_stats  # Return empty stats if no sessions
    
    # Overall statistics
    total_sessions = len(sessions)
    total_questions = sum(session.get('total_questions', 0) for session in sessions)
    total_correct = sum(session.get('correct_answers', 0) for session in sessions)
    
    # Calculate weighted average score (by questions answered)
    total_score_weighted = 0
    total_weight = 0
    for session in sessions:
        questions = session.get('total_questions', 0)
        score_pct = session.get('score_percentage', 0)
        if questions > 0:
            total_score_weighted += score_pct * questions
            total_weight += questions
    
    overall_average_score = (total_score_weighted / total_weight) if total_weight > 0 else 0.0
    
    # Problem type statistics
    problem_name_stats = defaultdict(lambda: {
        'total': 0, 
        'correct': 0, 
        'scores': [], 
        'response_times': [],
        'individual_accuracies': []  # For calculating accuracy std dev
    })
    
    for session in sessions:
        for record in session.get('records', []):
            problem_data = record.get('problem', {}) or {}
            problem_name = problem_data.get('name', 'unknown')
            
            problem_name_stats[problem_name]['total'] += 1
            
            # Track individual accuracy (1.0 for correct, 0.0 for incorrect)
            is_correct = record.get('correct', False)
            problem_name_stats[problem_name]['individual_accuracies'].append(1.0 if is_correct else 0.0)
            
            if is_correct:
                problem_name_stats[problem_name]['correct'] += 1
            
            # Store individual scores if available
            if 'score' in record:
                problem_name_stats[problem_name]['scores'].append(record['score'])
            
            # Store response times (convert to seconds if in milliseconds)
            response_time = record.get('response_ms', 0)
            if response_time > 0:
                # Convert milliseconds to seconds for more readable output
                problem_name_stats[problem_name]['response_times'].append(response_time / 1000.0)
    
    # Calculate averages and standard deviations for each problem type
    for problem_name, stats in problem_name_stats.items():
        if stats['total'] > 0:
            stats['accuracy_percentage'] = (stats['correct'] / stats['total']) * 100
        else:
            stats['accuracy_percentage'] = 0.0
        
        if stats['scores']:
            stats['average_score'] = sum(stats['scores']) / len(stats['scores']) * 100
        else:
            stats['average_score'] = stats['accuracy_percentage']
        
        # Calculate accuracy standard deviation
        if len(stats['individual_accuracies']) > 1:
            # Convert to percentages for std dev calculation
            accuracy_percentages = [acc * 100 for acc in stats['individual_accuracies']]
            stats['accuracy_std_dev'] = statistics.stdev(accuracy_percentages)
        else:
            stats['accuracy_std_dev'] = 0.0
        
        # Calculate response time statistics
        if stats['response_times']:
            stats['avg_response_time'] = statistics.mean(stats['response_times'])
            if len(stats['response_times']) > 1:
                stats['response_time_std_dev'] = statistics.stdev(stats['response_times'])
            else:
                stats['response_time_std_dev'] = 0.0
        else:
            stats['avg_response_time'] = 0.0
            stats['response_time_std_dev'] = 0.0
    
    # Recent sessions (last 5)
    recent_sessions = sessions[-5:] if len(sessions) >= 5 else sessions
    
    # Best session (highest score percentage)
    best_session = max(sessions, key=lambda s: s.get('score_percentage', 0)) if sessions else None
    
    # Session dates for trend analysis
    session_dates = []
    for session in sessions:
        try:
            date_str = session.get('date', '')
            if date_str:
                session_dates.append({
                    'date': date_str,
                    'score': session.get('score_percentage', 0),
                    'questions': session.get('total_questions', 0)
                })
        except (ValueError, TypeError):
            continue
    
    return {
        'total_sessions': total_sessions,
        'total_questions': total_questions,
        'total_correct_answers': total_correct,
        'overall_average_score': round(overall_average_score, 1),
        'problem_name_stats': dict(problem_name_stats),
        'recent_sessions': recent_sessions,
        'best_session': best_session,
        'session_dates': session_dates,
        'recent_average': round(sum(s.get('score_percentage', 0) for s in recent_sessions) / len(recent_sessions), 1) if recent_sessions else 0.0
    }