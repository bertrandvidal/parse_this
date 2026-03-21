# Plan: Enum Type Support with `choices`

## Context
`parse_this` already handles `bool` parameters as a special case, transforming them into argparse flags rather than plain typed arguments. Python `enum.Enum` subclasses deserve equivalent treatment: when a parameter is annotated with an Enum type, argparse should restrict input to the valid member names via `choices` and convert the string back to the enum member automatically. Without this, users who annotate a parameter with an Enum type get a runtime error or silent mismatch because `argparse` receives a string and passes it straight through without conversion or validation.

## Architecture
**New helper `_is_enum_type(arg_type)`** — a single predicate extracted into `parse_this/parsing.py` that checks `inspect.isclass(arg_type) and issubclass(arg_type, enum.Enum)`. Isolating it keeps the branching inside `_get_arg_parser` readable and mirrors the implicit `arg_type == bool` check already in place.

**Enum converter** — rather than passing the Enum class directly as `type=` (which would try to call `MyEnum("value")` and fail for name-based lookup), a small lambda `lambda s: arg_type[s]` is constructed inline at argument-registration time. This gives correct name→member conversion. `choices` is set to `[e.name for e in arg_type]` so the CLI shows and validates the symbolic names, which are more user-readable than values.

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
- Add `import enum` and `import inspect` at the top of `parse_this/parsing.py` alongside existing imports.
- Add a module-level helper directly above `_get_arg_parser`:
  ```python
  def _is_enum_type(arg_type) -> bool
  ```
  Body: `return inspect.isclass(arg_type) and issubclass(arg_type, enum.Enum)`.
- Inside `_get_arg_parser`, in the `default is _NO_DEFAULT` branch, insert an `elif _is_enum_type(arg_type):` check **before** the existing `else` (positional add):
  - Call `parser.add_argument(arg, help=help_msg, type=lambda s: arg_type[s], choices=[e.name for e in arg_type])`.
  - Add a `_LOG.debug(...)` call matching the pattern of the `bool` branch.
- In the `else` (has-default) branch, insert an `elif _is_enum_type(arg_type):` check **before** the existing `else` (optional add):
  - Call `parser.add_argument("--" + arg, help=help_msg, default=default, type=lambda s: arg_type[s], choices=[e.name for e in arg_type])`.
  - Add a matching `_LOG.debug(...)` call.
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
  - `test_get_arg_parser_enum_choices_registered` — use `_get_arg_parser` directly and assert that the `choices` list on the resulting action equals `["RED", "GREEN", "BLUE"]`.
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
