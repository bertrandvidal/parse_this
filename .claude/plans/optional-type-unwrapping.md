# Plan: Unwrap `Optional[T]` annotations and soften the None-default caveat

## Context

Two closely related issues:

1. The README's "Caveats and limitations" section says any argument whose
   default value is `None` must be explicitly type-annotated or a
   `ParseThisException` is raised. That hard check is correct — `None`
   conveys zero type information — but the error message is terse and the
   idiomatic Python fix (annotate as `Optional[int]`) doesn't actually
   work today.
2. `parse_this` nowhere calls `typing.get_origin`/`typing.get_args` on
   `Union` types, so a parameter annotated as `Optional[int]` (which is
   `Union[int, None]`) reaches argparse unchanged. argparse then tries to
   use `Optional[int]` as the `type=` converter, which blows up at parse
   time because it isn't callable in that way.

Fixing the second issue makes the first self-documenting: the natural
reaction to "annotate it" becomes a correct, working fix, and the hard
check only ever fires when the user really does have zero signal.

## Root cause

- `parse_this/parsing.py:199-204` raises when `default is None and
  arg_type is None`.
- Nothing in `parse_this/helpers.py`, `parse_this/parsing.py`, or
  `parse_this/type_check.py` unwraps `Union`/`Optional` annotations
  before passing them to argparse.

## Change

1. Add `_unwrap_optional(arg_type)` in `parse_this/helpers.py`. Semantics:
   - If `get_origin(arg_type)` is `typing.Union` (this also covers PEP
     604 `int | None`, which has the same origin under the hood) and
     `type(None)` is among `get_args(arg_type)`, return the single
     non-`None` argument.
   - If there is more than one non-`None` argument (e.g. `Union[int, str]`),
     raise `ParseThisException` with a clear message — parse_this cannot
     pick which converter to use.
   - For anything else, return `arg_type` unchanged.
2. Call the helper at the top of both `_add_required_argument` and
   `_add_optional_argument` in `parse_this/parsing.py`, *before* any
   type dispatch (bool / enum / literal / sequence). The `None`-default
   check still runs, just after unwrapping, so `Optional[int]` now
   reaches the check as `int` and the argument is registered
   successfully with `default=None`.
3. Polish the "None default without annotation" error message to name
   the offending parameter and suggest a concrete fix, e.g.
   `add an annotation, for example: spam: int | None = None`.
4. Update `_check_types` in `parse_this/type_check.py` if necessary —
   today it only counts annotations against arg names, so it should
   still work unchanged, but verify.

## Files

- `parse_this/helpers.py` — new `_unwrap_optional` helper.
- `parse_this/parsing.py` — invoke the helper; polish error message.
- `test/optional_test.py` (new) — cases:
  - `Optional[int]` required (no default) → rejected as required with a
    clear message *or* accepted with None as sentinel — pick one
    behaviour and justify. (Required arguments with `Optional[T]` are
    an odd shape: the user probably meant optional-with-default-None,
    so we accept and treat as optional-with-default-None.)
  - `Optional[int] = None` optional → CLI `--x 5` → int; omitted → None.
  - `Optional[str] = None` optional → CLI `--x hello` → str.
  - PEP 604 `int | None = None` → same as `Optional[int]`.
  - `Union[int, None]` → same as `Optional[int]`.
  - `Union[int, str]` (two non-None arms) → `ParseThisException` at
    decoration time.
  - `x = None` without annotation → improved error message, still
    raised.
- `test/parsing_test.py` — update the assertion for the improved
  error-message text if a test already covers it.
- `README.md` — rewrite the corresponding bullet in the caveats section
  as an errors-section-style rule; add a brief note under the `None`
  default subsection about `Optional[T]` and PEP 604 support.

## Verification

- `pytest`
- `pre-commit run --all-files`
- Manual:
  - `def f(x: Optional[int] = None)` → `python script.py --x 5`
    returns `5`; omitting `--x` returns `None`.
  - `def f(x=None)` → decoration-time error mentions the idiomatic
    fix.
  - `def f(x: Union[int, str] = 1)` → decoration-time error
    indicating ambiguous Union.

## Risk

Low. Strictly additive — no existing test exercises `Optional[T]`
support today, so no behaviour regresses.
