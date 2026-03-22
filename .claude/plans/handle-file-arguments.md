# Plan: Handle File Arguments (`argparse.FileType`)

## Branch
`handle-file-arguments`

## Context

`parse_this` currently has no awareness of `argparse.FileType` as a type annotation.
The README explicitly lists "Handle file arguments" as a TODO item. Without explicit
support and documentation, users have no way to know the feature exists or how to use
it correctly, and edge cases (e.g. `FileType` as an optional argument with a `None`
default) are untested and potentially broken.

## Architecture

- **New helper `_is_file_type(arg_type)`** in `parse_this/helpers.py` — mirrors the
  existing `_is_enum_type` pattern.
- **Guard fix in `_add_optional_argument`** (`parse_this/parsing.py`) — the
  `arg_type = arg_type or type(default)` line would evaluate `type(None)` → `NoneType`
  if a `FileType` instance were falsy; replaced with an explicit `_is_file_type` guard
  to be unconditionally safe.
- **Test fixtures** in `test/helpers.py` + **unit tests** in `test/parsing_test.py`
  following the established enum pattern.
- **README** updated: "Handle file arguments" TODO removed, new "File arguments"
  section added after "Enum arguments".

## Files Modified

| File | Change |
|---|---|
| `parse_this/helpers.py` | Add `_is_file_type` helper; add `FileType` to argparse imports |
| `parse_this/parsing.py` | Import `_is_file_type`; fix `or type(default)` guard |
| `test/helpers.py` | Add `has_file_argument` and `has_optional_file_argument` fixtures |
| `test/parsing_test.py` | Add `TestFileType` test class |
| `README.md` | Remove TODO bullet; add "File arguments" section |
| `.claude/plans/handle-file-arguments.md` | This file |

## Commit Strategy

1. `docs: add plan file for handle-file-arguments`
2. `feat: add FileType argument support with tests`
3. `docs: document FileType file arguments, remove TODO`

## Verification

```bash
source venv/bin/activate
pytest --cov=parse_this
```
All tests pass; coverage does not decrease.
