# Plan: Handle File Arguments (`pathlib.Path`)

## Branch
`handle-file-arguments`

## Context

`parse_this` currently has no awareness of file path types. The README explicitly
lists "Handle file arguments" as a TODO item. Rather than requiring users to know
about `argparse.FileType`, parameters annotated with `pathlib.Path` (or any
`PurePath` subclass) are detected and passed through to argparse, which calls
`Path(string_arg)` to convert CLI strings to Path objects automatically.

## Revision History

The initial implementation used `argparse.FileType` instances as type annotations.
This was reverted in favour of `pathlib.Path` detection, which is more Pythonic
and doesn't require users to know about argparse internals.

## Architecture

- **New helper `_is_path_type(arg_type)`** in `parse_this/helpers.py` — mirrors the
  existing `_is_enum_type` pattern, checking `issubclass(arg_type, PurePath)`.
- **Guard fix in `_add_optional_argument`** (`parse_this/parsing.py`) — the
  `arg_type = arg_type or type(default)` line replaced with an explicit
  `if arg_type is None` check to prevent type fallback when an annotation is
  provided.
- **Test fixtures** in `test/helpers.py` + **unit tests** in `test/parsing_test.py`
  following the established enum pattern.
- **README** updated: "Handle file arguments" TODO removed, new "File path
  arguments" section added after "Enum arguments".

## Files Modified

| File | Change |
|---|---|
| `parse_this/helpers.py` | Add `_is_path_type` helper; add `PurePath` import |
| `parse_this/parsing.py` | Fix `or type(default)` guard to `if arg_type is None` |
| `test/helpers.py` | Add `has_path_argument` and `has_optional_path_argument` fixtures |
| `test/parsing_test.py` | Add `TestPathType` test class |
| `README.md` | Remove TODO bullet; add "File path arguments" section |
| `.claude/plans/handle-file-arguments.md` | This file |

## Commit Strategy

1. `docs: add plan file for handle-file-arguments` (already committed)
2. Revert of `docs: document FileType file arguments, remove TODO`
3. Revert of `feat: add FileType argument support with tests`
4. `feat: add pathlib.Path argument support with tests`
5. `docs: document Path file arguments, remove TODO`

## Verification

```bash
source venv/bin/activate
pytest --cov=parse_this
```
All tests pass; coverage does not decrease.
