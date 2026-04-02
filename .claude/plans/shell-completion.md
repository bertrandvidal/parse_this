# Plan: Shell Completion

## Context

Shell completion (bash/zsh/fish) greatly improves CLI UX. parse_this should generate completion scripts from its parsers. The `argcomplete` library is the standard way to add this to argparse-based tools.

## Tasks

### 1. Add argcomplete as optional dependency
- Add `completion` extra in `pyproject.toml`: `completion = ["argcomplete>=3.0"]`
- File: `pyproject.toml`

### 2. Add completion activation to ClassParser
- In `_set_class_parser`, after building the top-level parser, call `argcomplete.autocomplete(parser)` if argcomplete is installed
- Guard with try/import so it's a no-op without the extra
- File: `parse_this/parsers.py`

### 3. Add completion activation to FunctionParser
- Same pattern in `FunctionParser.__call__` after building the parser
- File: `parse_this/parsers.py`

### 4. Add helper to generate completion script
- Add `parse_this.completion` module with `generate_completion(parser, shell="bash")` that outputs the activation script
- File: `parse_this/completion.py`

### 5. Add tests
- Test that argcomplete.autocomplete is called when available
- Test graceful fallback when argcomplete is not installed
- File: `test/completion_test.py`

### 6. Document in README
- Add shell completion section with install and activation instructions

## Verification
- `pytest`
- `pre-commit run --all-files`
