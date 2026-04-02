# Plan: Callable Defaults (Lazy/Dynamic Defaults)

## Context

Some CLI arguments need defaults computed at runtime (e.g., today's date, current working directory, generated UUIDs). parse_this should support callables as default values that are invoked when the argument isn't provided.

## Tasks

### 1. Define LazyDefault wrapper
- Add to `parse_this/types.py`:
  ```python
  class LazyDefault:
      def __init__(self, factory: Callable[[], Any], display: str = None):
          self.factory = factory
          self.display = display  # shown in help, e.g. "(default: today's date)"
  ```
- Export from `parse_this/__init__.py`

### 2. Detect LazyDefault in parsing.py
- In `_add_optional_argument`, when `default` is a `LazyDefault` instance:
  - Use `default=None` in `add_argument` (so we can detect "not provided")
  - Store the factory for post-parse resolution
  - Use `display` string in help text if provided
- File: `parse_this/parsing.py`

### 3. Resolve lazy defaults after parsing
- In `_call` (call.py), after building the arguments dict, resolve any `None` values that correspond to `LazyDefault` parameters by calling the factory
- Need to pass metadata about which args have lazy defaults through to `_call`
- File: `parse_this/call.py`

### 4. Add tests
- `LazyDefault(datetime.date.today)` — receives today's date when not provided
- `LazyDefault(os.getcwd, display="current directory")` — help text shows display
- Explicit value overrides the factory
- File: `test/callable_defaults_test.py`

## Verification
- `pytest`
- `pre-commit run --all-files`
