# Plan: Literal Type Support

## Context

When a function parameter is annotated with `typing.Literal["a", "b", "c"]`, parse_this should generate a `choices` argument in argparse, restricting CLI input to those values. Currently Literal annotations are treated as untyped.

## Tasks

### 1. Detect Literal types in helpers.py
- Add `_is_literal_type(arg_type)` that returns True when `get_origin(arg_type) is Literal`
- Add `_get_literal_values(arg_type)` that returns the tuple of allowed values via `get_args()`
- File: `parse_this/helpers.py`

### 2. Handle Literal in _add_required_argument and _add_optional_argument
- In `parse_this/parsing.py`, add branches for `_is_literal_type(arg_type)` before the generic fallback
- Required: `parser.add_argument(arg, choices=values, type=str, help=help_msg)`
- Optional: `parser.add_argument("--" + arg, choices=values, default=default, type=str, help=help_msg)`
- Infer the element type from the first literal value (all must be same type for argparse choices)
- File: `parse_this/parsing.py`

### 3. Add tests
- Required positional Literal arg — valid and invalid values
- Optional Literal arg with default
- Mixed Literal + regular args
- File: `test/literal_test.py`

### 4. Export nothing new
- Literal is from `typing`, no new public API needed

## Verification
- `pytest`
- `pre-commit run --all-files`
