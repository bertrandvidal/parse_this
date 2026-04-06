# Plan: Literal Type Support

## Context

When a function parameter is annotated with `typing.Literal["a", "b", "c"]`, parse_this should generate a `choices` argument in argparse, restricting CLI input to those values. Currently Literal annotations are treated as untyped.

## Design Decisions

- **No mixed types**: All Literal values must share the same type. Mixed types (e.g., `Literal[1, "auto"]`) raise `ParseThisException`.
- **Type preserved**: `type(values[0])` is used as the argparse type converter, so `Literal[1, 2, 3]` yields ints, not strings.
- **Defaults from signature**: Optional Literal args get their default from the function signature as usual. The default is validated against the Literal choices — if it's not a valid choice, raise `ParseThisException`.

## Tasks

### 1. Detect Literal types in helpers.py
- Add `_is_literal_type(arg_type)` that returns True when `get_origin(arg_type) is Literal`
- Add `_get_literal_values(arg_type)` that returns the tuple of allowed values via `get_args()`
- File: `parse_this/helpers.py`

### 2. Pass Literal annotations through type_check.py
- `_check_types` currently expects annotations to be callable. Literal annotations aren't callable — ensure they pass through without being rejected.
- File: `parse_this/type_check.py`

### 3. Handle Literal in _add_required_argument and _add_optional_argument
- In `parse_this/parsing.py`, add branches for `_is_literal_type(arg_type)` before the `_is_enum_type` check
- Infer element type from `type(values[0])`; validate all values share that type, raise `ParseThisException` if not
- Required: `parser.add_argument(arg, choices=values, type=element_type, help=help_msg)`
- Optional: `parser.add_argument("--" + arg, choices=values, default=default, type=element_type, help=help_msg)`
- For optional args, validate that the default is in the Literal choices; raise `ParseThisException` if not
- File: `parse_this/parsing.py`

### 4. Add tests
- Required positional Literal[str] arg — valid and invalid values
- Required positional Literal[int] arg — type is preserved
- Optional Literal arg with default
- Mixed Literal + regular args
- Mixed types in Literal raises ParseThisException
- Default value not in Literal choices raises ParseThisException
- File: `test/literal_test.py`

### 5. Export nothing new
- Literal is from `typing`, no new public API needed

## Verification
- `pytest`
- `pre-commit run --all-files`
