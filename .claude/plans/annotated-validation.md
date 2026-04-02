# Plan: Annotated-Based Validation

## Context

`typing.Annotated` (Python 3.10+) can carry metadata for argument constraints. parse_this should support validators like range checks, regex patterns, and custom predicates attached via Annotated metadata.

## Tasks

### 1. Define constraint classes
- Add to `parse_this/types.py`:
  ```python
  class Range:
      def __init__(self, min=None, max=None): ...

  class Pattern:
      def __init__(self, regex: str): ...

  class Constraint:
      def __init__(self, predicate: Callable, description: str): ...
  ```
- Export from `parse_this/__init__.py`

### 2. Extract constraints from Annotated in helpers.py
- Add `_get_constraints(arg_type)` that returns a list of constraint objects from Annotated metadata
- Add `_unwrap_annotated(arg_type)` that returns the base type stripped of Annotated wrapper
- File: `parse_this/helpers.py`

### 3. Build validating type wrapper in parsing.py
- When constraints are present, wrap the `type` callable passed to `add_argument` with a function that:
  - Converts the value using the base type
  - Runs each constraint's check
  - Raises `argparse.ArgumentTypeError` on failure with a clear message
- File: `parse_this/parsing.py`

### 4. Add tests
- `Range(min=0, max=100)` — valid and out-of-range values
- `Pattern(r"^\d{3}-\d{4}$")` — matching and non-matching
- `Constraint(lambda x: x % 2 == 0, "must be even")` — custom predicate
- Stacked constraints (Range + Constraint)
- File: `test/annotated_validation_test.py`

## Verification
- `pytest`
- `pre-commit run --all-files`
