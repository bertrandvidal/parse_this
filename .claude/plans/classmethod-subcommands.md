# Plan: Expose classmethods (and staticmethods) as subcommands in `@parse_class`

## Context

The README's "Caveats and limitations" currently states:

> Inside a `@parse_class`, classmethods decorated with `@create_parser`
> are **not** exposed as subcommands.

The limitation isn't a deep design problem — it's how
`_get_parseable_methods` inspects `vars(cls)`:

```python
for name, obj in vars(cls).items():
    if callable(obj) and hasattr(obj, "parser"):
        ...
```

When `@classmethod` is stacked on top of `@create_parser` (the only
correct order, since `classmethod` wraps the already-decorated function),
`vars(cls)[name]` is a `classmethod` **descriptor**, not a regular
function. The descriptor itself:

- is *not* callable (`callable(classmethod(...))` is `False`)
- does not expose `.parser` directly — `.parser` lives on `obj.__func__`

So the existing check excludes classmethods silently, and two existing
tests actively assert the exclusion:

- `test/parsing_test.py:56` — `test_get_parseable_methods_do_not_include_classmethod`
- `test/parsers_test.py:143` (approx) — `test_parse_class_classmethod_are_not_sub_command`

`staticmethod` has the same problem for the same reason: `vars(cls)[name]`
returns a `staticmethod` descriptor, which in Python 3.10+ is callable
but still hides `.parser` behind `.__func__`.

Dispatch at `call.py` uses `getattr(instance, method_name)`, which
resolves a classmethod descriptor to a bound method on `type(instance)`
and a staticmethod descriptor to the underlying function — so the
**call path needs no changes** once discovery is fixed.

## Root cause

- `parse_this/parsing.py:_get_parseable_methods` filters entries in
  `vars(cls)` with `callable(obj) and hasattr(obj, "parser")`, which
  rejects classmethod/staticmethod descriptors.

## Change

1. In `_get_parseable_methods`, recognise `classmethod` and
   `staticmethod` descriptors explicitly: when the entry is one of
   those and `hasattr(obj.__func__, "parser")`, include it using
   `obj.__func__` as the parser-bearing object.
2. Flip the two existing exclusion tests into inclusion tests.
3. Add fixtures in `test/helpers.py` for a classmethod and a
   staticmethod that each produce verifiable output.
4. Add end-to-end test that calls each through the `@parse_class`
   top-level parser and verifies the result.
5. Edge case: a `@parse_class` whose only parseable methods are
   classmethods/staticmethods (no decorated `__init__`). The dispatch
   path in `parsers.py` instantiates the class when
   `"__init__" in parser_to_method` and otherwise falls through to
   `_call_method_from_namespace(instance, ...)` with `instance=None`.
   For classmethods, descriptor resolution on the class should still
   work via `getattr(cls, method_name)` — but verify with a test
   using the *class* as the instance.
6. Update README: remove the classmethods caveat bullet and update the
   corresponding section.

## Files

- `parse_this/parsing.py` — descriptor unwrapping in
  `_get_parseable_methods`.
- `parse_this/parsers.py` and/or `parse_this/call.py` — only if the
  classmethod-only class edge case needs a small fix.
- `test/parsing_test.py` — flip the exclusion assertion to inclusion.
- `test/parsers_test.py` — flip the exclusion assertion, add
  end-to-end tests for classmethod/staticmethod dispatch.
- `test/helpers.py` — may need new classmethod/staticmethod fixtures
  if existing ones aren't sufficient.
- `README.md` — remove caveat bullet; update the Classmethods
  section.

## Verification

- `pytest`
- `pre-commit run --all-files`
- Manual:
  - A `@parse_class` with a classmethod subcommand invoked from CLI.
  - Same with a staticmethod.
  - `--help` lists both as subcommands.

## Risk

Medium. Two existing tests change meaning (easy to review). Edge case
(classmethod-only class) may need a small dispatch fix.
