# Plan: Support stacking `@create_parser` under signature-changing decorators

## Context

The README's "Caveats and limitations" section states that `@create_parser`
cannot be stacked with decorators that alter the wrapped callable's
signature (e.g. any decorator that wraps the function with `*args, **kwargs`
via `functools.wraps`). This is a soft limitation: `getfullargspec` does not
follow `__wrapped__`, so when a signature-preserving wrapper sits above
`@create_parser`, the real parameters disappear from the parser. Today the
library silently produces a parser with zero arguments in this case, which
is a nasty footgun.

The stdlib function `inspect.unwrap()` — or equivalently
`inspect.signature(follow_wrapped=True)`, which is the default — recovers
the original function through any number of `functools.wraps`-using
decorators. Calling `inspect.unwrap(func)` *once* at the top of each
signature-inspection site is enough to make stacking work.

## Root cause

- `parse_this/parsers.py:78` (`FunctionParser.__call__`)
- `parse_this/parsers.py:136` (`MethodParser.__call__`)

Both call:
```python
func_args, _, _, defaults, _, _, annotations = getfullargspec(func)
```

`getfullargspec` does not follow `__wrapped__`. A decorator of the form:
```python
def log_calls(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        print(f"calling {f.__name__}")
        return f(*args, **kwargs)
    return wrapper

@log_calls
@create_parser()
def add(a: int, b: int):
    ...
```
causes `getfullargspec(wrapper)` to return `[]` for `func_args`, `None` for
`defaults`, and `{}` for `annotations`. The parser is built from nothing.

## Change

Introduce `inspect.unwrap(func)` once at the top of each call site, *before*
`getfullargspec`. Use the unwrapped function for signature inspection only
— keep attaching `.parser` to the outer `func` so the user's decorator
semantics are preserved. Keep the existing `functools.wraps(func)` wrapper
returned by `MethodParser.__call__` unchanged.

## Files

- `parse_this/parsers.py` — add `import inspect` (already imported via
  `inspect.getfullargspec` indirectly — verify) and call
  `inspect.unwrap(func)` at both call sites. Store the result in a local
  like `wrapped = inspect.unwrap(func)` and pass `wrapped` to
  `getfullargspec` and to `_check_types` / `_get_arg_parser` so that help
  text and error messages still name the right function (whichever is most
  correct — verify during implementation).
- `test/parsers_test.py` — new tests covering:
  - `@functools.wraps`-based decorator stacked above `@create_parser` on a
    top-level function, invoked via `.parser.call()` — verify the parser
    sees the real parameters and the wrapper still executes.
  - Same stacking on a method inside a class, invoked via a
    `@parse_class` subcommand dispatch.
- `README.md` — remove the "decorator stacking" bullet from the
  "Caveats and limitations" section.

## Verification

- `pytest`
- `pre-commit run --all-files`
- Manual: define a `@functools.wraps`-using decorator, stack it above
  `@create_parser`, run `--help` and confirm the real arguments are listed
  and the function is dispatched correctly.

## Risk

Very low. `inspect.unwrap` is a no-op on functions without `__wrapped__`,
so all existing behaviour is preserved.
