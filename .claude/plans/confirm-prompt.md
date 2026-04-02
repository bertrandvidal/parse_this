# Plan: Confirmation Prompts

## Context

Destructive CLI operations often require user confirmation (e.g., "Are you sure?"). parse_this should support a `Confirm` type that generates a `--flag` to skip the prompt, and interactively asks for confirmation when the flag isn't passed.

## Tasks

### 1. Define Confirm type
- Add to `parse_this/types.py`:
  ```python
  class Confirm:
      def __init__(self, message: str = "Are you sure?", default: bool = False):
          self.message = message
          self.default = default
  ```
- Export from `parse_this/__init__.py`
- Support shorthand: `force: Confirm = False` (detect via annotation type)

### 2. Handle Confirm in parsing.py
- In `_add_optional_argument`, when `arg_type is Confirm` or `isinstance(default, Confirm)`:
  - Register as `store_true` flag: `parser.add_argument("--force", action="store_true", default=False)`
  - Store the Confirm metadata (message, default) for post-parse resolution
- File: `parse_this/parsing.py`

### 3. Resolve confirmation in call.py
- In `_call`, after building the arguments dict, for each Confirm-typed arg:
  - If the flag was passed (`True`), proceed
  - If not passed and stdin is a TTY, print the message and read y/n
  - If not passed and stdin is NOT a TTY, use the Confirm's default value
- File: `parse_this/call.py`

### 4. Add tests
- Flag passed — no prompt, proceeds
- Flag not passed + stdin mocked to "y" — proceeds
- Flag not passed + stdin mocked to "n" — does not proceed (returns False)
- Non-TTY fallback uses default
- File: `test/confirm_test.py`

## Verification
- `pytest`
- `pre-commit run --all-files`
