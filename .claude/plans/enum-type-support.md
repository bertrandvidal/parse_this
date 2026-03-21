# Plan: Enum Type Support with `choices`

## Context
`parse_this` already handles `bool` parameters as a special case, transforming them into argparse flags rather than plain typed arguments. Python `enum.Enum` subclasses deserve equivalent treatment: when a parameter is annotated with an Enum type, argparse should restrict input to the valid member names via `choices` and convert the string back to the enum member automatically. Without this, users who annotate a parameter with an Enum type get a runtime error or silent mismatch because `argparse` receives a string and passes it straight through without conversion or validation.

## Architecture
**New helper `_is_enum_type(arg_type)`** — a single predicate extracted into `parse_this/parsing.py` that checks `inspect.isclass(arg_type) and arg_type is not enum.Enum and issubclass(arg_type, enum.Enum)`. The `arg_type is not enum.Enum` guard is necessary because the base class has no members; registering it would produce an argument that can never be satisfied. Isolating the predicate keeps the branching inside `_get_arg_parser` readable and mirrors the implicit `arg_type == bool` check already in place.

**Enum converter** — `_make_enum_converter(enum_class)` returns a named inner function that does `enum_class[s]` (name-based lookup) and raises `argparse.ArgumentTypeError` on unknown names. `ArgumentTypeError` (not `ValueError`) is used because argparse silently discards the `ValueError` message and substitutes a generic diagnostic using the converter's `__name__`; `ArgumentTypeError` preserves the message verbatim so users see the intended "invalid choice: … (choose from …)" output.

**`choices` and `metavar`** — `choices` is set to `list(enum_class)` (the enum *members*, not their names). This is required because argparse validates the *post-conversion* value against `choices`; after the `type` converter runs, the value is an enum member, so the membership check `Color.RED in ["RED", "GREEN", "BLUE"]` would fail if strings were used. `metavar` is set to `{RED,GREEN,BLUE}` (the symbolic names) so the help text and usage line remain human-readable.

No new modules, no changes to the public API, no changes to `parsers.py`, `call.py`, `args.py`, or `types.py`.

## Files
| File | Action |
|---|---|
| `parse_this/parsing.py` | Modify — add `import enum`, add `_is_enum_type` helper, add enum branches inside `_get_arg_parser` |
| `test/helpers.py` | Modify — add `Color` enum fixture and two decorated helper functions (`has_enum_argument`, `has_enum_default`) |
| `test/parsing_test.py` | Modify — add test methods to `TestParsing` covering positional enum, optional enum with default, invalid enum value, and round-trip via `.parser.call()` |
| `README.md` | Modify — add "Enum arguments" section after "Using None as a default value and bool as flags" section |
| `.claude/plans/enum-type-support.md` | Create — plan file |

## Steps

### Step 1 — Create the plan file and git branch
- Create `.claude/plans/enum-type-support.md` with the content of this plan.
- Run `git checkout -b enum-type-support` from the repo root.
- Commit: `Add plan for enum type support`.

### Step 2 — Add enum detection and argument registration in `parse_this/parsing.py`
- Add `import enum`, `import inspect`, and `from argparse import ArgumentTypeError` at the top of `parse_this/parsing.py` alongside existing imports.
- Add `_is_enum_type` module-level helper directly above `_get_arg_parser`:
  ```python
  def _is_enum_type(arg_type) -> bool:
      return (
          inspect.isclass(arg_type)
          and arg_type is not enum.Enum
          and issubclass(arg_type, enum.Enum)
      )
  ```
- Add `_make_enum_converter(enum_class)` helper that returns a converter raising `ArgumentTypeError` (not `ValueError`) on unknown names.
- Inside `_get_arg_parser`, insert `elif _is_enum_type(arg_type):` in both the positional and optional branches. Use `choices=list(enum_class)` (enum members) and `metavar="{name1,name2,...}"` (symbolic names for display).
- Commit: `Add enum type support with automatic choices in _get_arg_parser`.

### Step 3 — Add enum test fixtures to `test/helpers.py`
- Add `import enum` at the top of `test/helpers.py`.
- Define a simple `Color(enum.Enum)` with members `RED`, `GREEN`, `BLUE`.
- Add two `@create_parser()`-decorated helper functions:
  - `has_enum_argument(color: Color)` — positional enum, no default.
  - `has_enum_default(a: int, color: Color = Color.RED)` — optional enum with a default member.
- Commit: `Add Color enum fixtures to test helpers`.

### Step 4 — Add tests to `test/parsing_test.py`
- Add `from test.helpers import has_enum_argument, has_enum_default, Color` to the imports.
- Add the following test methods to `TestParsing`:
  - `test_get_arg_parser_enum_positional_argument` — assert `has_enum_argument.parser.call(args=["RED"])` returns `Color.RED`.
  - `test_get_arg_parser_enum_positional_invalid` — assert that parsing an invalid name raises `SystemExit`.
  - `test_get_arg_parser_enum_default_value` — assert `has_enum_default.parser.call(args=["1"])` returns `(1, Color.RED)`.
  - `test_get_arg_parser_enum_override_default` — assert `has_enum_default.parser.call(args=["1", "--color", "GREEN"])` returns `(1, Color.GREEN)`.
  - `test_get_arg_parser_enum_choices_registered` — use `_get_arg_parser` directly and assert that the `choices` list on the resulting action equals `list(Color)` (enum members, not strings).
- Commit: `Add tests for enum type support`.

### Step 5 — Document enum support in `README.md`
- Insert a new section **"Enum arguments"** immediately after the "Using None as a default value and bool as flags" section.
- Show a minimal annotated example using `Color(enum.Enum)`, demonstrate the CLI choices restriction, and note that the member **name** (not value) is used on the command line.
- Commit: `Document enum argument support in README`.

### Step 6 — Final Verify
```bash
cd /Users/bert/github/parse_this
source venv/bin/activate
pytest test/parsing_test.py -v
pytest --tb=short
black --check parse_this/ test/
```
