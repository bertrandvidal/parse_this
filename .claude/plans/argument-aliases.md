# Plan: Argument Aliases / Short Flags

## Context

CLI tools conventionally support short flags (e.g., `-v` for `--verbose`). parse_this currently only generates long-form `--arg` flags for optional arguments. Users should be able to specify aliases.

## Tasks

### 1. Support Annotated metadata for aliases
- Use `typing.Annotated` to carry alias info:
  ```python
  from parse_this import Alias
  def deploy(verbose: Annotated[bool, Alias("-v")] = False): ...
  ```
- Add `Alias` class in `parse_this/types.py`:
  ```python
  class Alias:
      def __init__(self, *flags: str):
          self.flags = flags
  ```
- Export from `parse_this/__init__.py`

### 2. Extract alias from Annotated in parsing.py
- Add `_get_alias(arg_type)` helper in `parse_this/helpers.py` that inspects `Annotated` metadata for `Alias` instances
- Unwrap the actual type from `Annotated` for normal type handling
- In `_add_optional_argument`, prepend alias flags to the `add_argument` call
- Files: `parse_this/helpers.py`, `parse_this/parsing.py`

### 3. Add tests
- Short flag alias works (`-v` sets `--verbose`)
- Multiple aliases (`-v`, `-V`)
- Alias on non-bool optional arg
- No alias — existing behavior unchanged
- File: `test/alias_test.py`

## Verification
- `pytest`
- `pre-commit run --all-files`
