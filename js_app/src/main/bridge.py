import json
import os
import sys

# Append py_app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../py_app')))
import problems
from classes import Problem

# --- Invariant layer -------------------------------------------------------
#
# Mirrors src/main/invariants.js: `requires` is a hard precondition and always
# raises (correct callers never trip it), while `checks` records a soft
# violation on stderr without changing behaviour. stdout stays pure JSON so the
# Node side is unaffected.

STRICT = os.environ.get('MEMORY_TRAINER_STRICT') == '1'

# Fields Problem declares as a dataclass. Anything else on an instance was put
# there by create() and is part of the problem's state.
DATACLASS_FIELDS = frozenset(Problem.__dataclass_fields__)


class PreconditionError(ValueError):
    pass


class InvariantViolation(AssertionError):
    pass


def requires(condition, message, **details):
    if not condition:
        raise PreconditionError(f"{message} {details}" if details else message)


def checks(condition, code, message, **details):
    if condition:
        return True
    line = f"INVARIANT[{code}] {message}"
    if details:
        line += f" {json.dumps(details, default=str, ensure_ascii=False)}"
    print(line, file=sys.stderr)
    if STRICT:
        raise InvariantViolation(line)
    return False


def _problem_class(type_name):
    """Resolve a problem type id to its class, with a precondition."""
    requires(isinstance(type_name, str) and type_name.strip(),
             "type_name must be a non-blank string", type_name=type_name)
    cls = getattr(problems, type_name, None)
    requires(isinstance(cls, type) and issubclass(cls, Problem) and cls is not Problem,
             "type_name must name a Problem subclass", type_name=type_name)
    return cls


def _extra_state(p):
    """
    Everything create() attached to the instance beyond the dataclass fields.

    Evaluation happens in a separate process, so this state has to travel with
    the payload or custom evaluate_solution implementations silently degrade —
    Anagram._dict_index is the concrete case.
    """
    state = {}
    for key, value in vars(p).items():
        if key in DATACLASS_FIELDS:
            continue
        if isinstance(value, (str, int, float, bool, type(None))):
            state[key] = value
        else:
            checks(False, 'PAYLOAD_SHAPE',
                   'problem state is not JSON-serialisable and will not survive evaluation',
                   attribute=key, type=type(value).__name__)
    return state


def _input_type(p):
    """The input that the answer needs.

    problem_type 'multiline' can describe only the memorize text. A one-line answer
    needs a one-line input, where Enter submits.
    """
    if p.problem_type == 'multiline' and '\n' not in p.solution:
        return 'single line'
    return p.problem_type


def get_types():
    types = []
    for name, obj in problems.__dict__.items():
        if isinstance(obj, type) and issubclass(obj, Problem) and obj is not Problem:
            display_name = obj.display_name()
            # Fix ATC capitalization without modifying the source python files
            if display_name == 'Atc':
                display_name = 'ATC'
            types.append({'id': name, 'name': display_name})

    checks(len(types) > 0, 'PAYLOAD_SHAPE', 'no problem types were discovered')
    ids = [t['id'] for t in types]
    checks(len(ids) == len(set(ids)), 'PAYLOAD_SHAPE', 'duplicate problem type ids', ids=ids)

    # Sort alphabetically by display name
    types.sort(key=lambda x: x['name'])
    return types


def create_problem(type_name, round_num=1):
    cls = _problem_class(type_name)
    requires(int(round_num) >= 1, "round_num must be >= 1", round_num=round_num)

    p = cls.create(round_num=int(round_num))

    requires(isinstance(p, Problem), "create must return a Problem", type_name=type_name)

    payload = {
        'display_name': p.name,
        'memorize': p.memorize,
        'prompt': p.prompt,
        'solution': p.solution,
        'exposure_ms': p.exposure_ms,
        'input_type': _input_type(p),
        # Warm-up rounds (TwoBackRecall) are unscored; everything else is.
        'is_scored': bool(getattr(p, 'is_scored', True)),
        # Carried opaquely by the renderer and handed back at evaluation time.
        'state': _extra_state(p),
    }

    checks('\n' not in payload['solution'] or payload['input_type'] == 'multiline',
           'UNANSWERABLE_SOLUTION',
           'solution spans multiple lines but input_type does not ask for a multiline input',
           type_name=type_name, input_type=payload['input_type'])

    checks(payload['input_type'] in ('single line', 'multiline', 'matrix'),
           'PAYLOAD_SHAPE', 'unrecognised input_type',
           type_name=type_name, input_type=payload['input_type'])

    return payload


def evaluate_problem(type_name, solution, user_input, state=None):
    cls = _problem_class(type_name)
    requires(isinstance(solution, str), "solution must be a str", solution=solution)
    requires(isinstance(user_input, str), "user_input must be a str", user_input=user_input)

    p = cls("Dummy", "Dummy", "Dummy", solution, 1000)

    # Restore whatever create() attached, so a custom evaluate_solution sees the
    # same instance it would have seen in-process.
    for key, value in (state or {}).items():
        requires(key not in DATACLASS_FIELDS,
                 "state may not overwrite a dataclass field", key=key)
        setattr(p, key, value)

    score = p.evaluate_solution(user_input)

    checks(isinstance(score, (int, float)) and 0.0 <= score <= 1.0,
           'PAYLOAD_SHAPE', 'score must be a number in [0, 1]',
           type_name=type_name, score=score)

    return {
        'score': score,
        'correct': score >= 1.0
    }


def _parse_state(raw):
    if raw is None or raw == '':
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PreconditionError(f"state must be valid JSON: {exc}") from exc
    requires(isinstance(parsed, dict), "state must be a JSON object", state=parsed)
    return parsed


if __name__ == '__main__':
    requires(len(sys.argv) >= 2, "a command argument is required", argv=sys.argv[1:])
    command = sys.argv[1]
    requires(command in ('get_types', 'create', 'evaluate'),
             "unknown command", command=command)

    if command == 'get_types':
        print(json.dumps(get_types()))
    elif command == 'create':
        requires(len(sys.argv) >= 3, "create requires a problem type", argv=sys.argv[1:])
        round_num = sys.argv[3] if len(sys.argv) > 3 else 1
        print(json.dumps(create_problem(sys.argv[2], round_num)))
    elif command == 'evaluate':
        requires(len(sys.argv) >= 5,
                 "evaluate requires type, solution and user_input", argv=sys.argv[1:])
        state = _parse_state(sys.argv[5] if len(sys.argv) > 5 else None)
        print(json.dumps(evaluate_problem(sys.argv[2], sys.argv[3], sys.argv[4], state)))
