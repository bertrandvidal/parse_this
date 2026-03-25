# Plan: Handle list/tuple arguments (`argparse` nargs)

## Branch
`handle-list-tuple-arguments`

## Context

`parse_this` currently has no awareness of sequence type annotations like
`list[int]` or `tuple[str, ...]`. The README explicitly lists "Handle list/tuple
arguments i.e. argparse's nargs" as a TODO item. Adding support maps these
annotations to argparse's `nargs='+'` parameter.

## Architecture

- **New helpers `_is_sequence_type` and `_get_element_type`** in
  `parse_this/helpers.py` — detect `list`, `tuple`, `List[T]`, `tuple[T, ...]`
  and extract the element type using `typing.get_origin`/`typing.get_args`.
- **New branches in `_add_required_argument` and `_add_optional_argument`** in
  `parse_this/parsing.py` — detect sequence types and pass `nargs='+'` with the
  element type to argparse.
- **Test fixtures** in `test/helpers.py` + **unit tests** in
  `test/parsing_test.py` following the established enum pattern.
- **README** updated: TODO removed, new "List and tuple arguments" section added.

## Files Modified

| File | Change |
|---|---|
| `parse_this/helpers.py` | Add `_is_sequence_type`, `_get_element_type` helpers |
| `parse_this/parsing.py` | Import new helpers; add sequence branches after enum checks |
| `test/helpers.py` | Add sequence type test fixtures |
| `test/parsing_test.py` | Add `TestSequenceType` test class |
| `README.md` | Remove TODO bullet; add "List and tuple arguments" section |
| `.claude/plans/handle-list-tuple-arguments.md` | This file |

## Commit Strategy

1. `docs: add plan file for handle-list-tuple-arguments`
2. `feat: add list and tuple argument support with tests`
3. `docs: document list/tuple arguments, remove TODO`

## Verification

```bash
source venv/bin/activate
pytest --cov=parse_this
```
All tests pass; coverage does not decrease.
