# Plan: Support `*args` and reject `**kwargs` with a clear error

## Context

The README's "Caveats and limitations" says:

> `parse_this` and `@create_parser` cannot be used on functions or methods
> with `*args` or `**kwargs` — the parser is built from the explicit
> parameters of the signature.

What actually happens today: `getfullargspec` returns `args`, `varargs`,
`varkw`, `defaults`, ... The `parse_this` code ignores positions 1 and 2,
so a function like `def sum(*nums: int)` silently becomes a parser with
zero arguments and always gets called as `sum()`. No error is raised;
the user's varargs simply vanish. This is a silent footgun.

Two independent fixes:

1. **`*args`** — genuinely supportable via argparse's `nargs="*"`.
2. **`**kwargs`** — not supportable, because argparse has no notion of
   arbitrary key/value flags. Raise `ParseThisException` at decoration
   time with a clear error naming the parameter.

## Root cause

- `parse_this/parsers.py` calls `getfullargspec(wrapped)` in both
  `FunctionParser.__call__` and `MethodParser.__call__` and discards
  `varargs` and `varkw` via the `_, _` unpacking pattern:
  ```python
  func_args, _, _, defaults, _, _, annotations = getfullargspec(wrapped)
  ```
- Nothing downstream ever sees the varargs/varkw names.

## Change

### 1. `**kwargs` rejection

In both `FunctionParser.__call__` and `MethodParser.__call__`, after
calling `getfullargspec`, bind the `varkw` slot. If it is not `None`,
raise:

```
ParseThisException: parameter '**<name>' of '<func>' is not supported:
parse_this cannot build argparse flags from arbitrary keyword arguments.
Remove the **<name> parameter or pass keyword options through explicit
parameters.
```

### 2. `*args` support

Bind the `varargs` slot from `getfullargspec`. When non-None:

- Treat it as an additional positional argument to the argparse parser.
- Use `nargs="*"` so the user can supply zero or more values.
- Use the annotation `annotations.get(varargs_name, str)` as the element
  type.
- Register it **after** the explicit positional arguments and **after**
  the optional flags so argparse's positional ordering is consistent.

Dispatch changes:

- `_call` in `parse_this/call.py` builds a `{name: value}` dict and
  calls `callable_obj(**arguments)`. For varargs the value is a list
  that must be splatted, not passed as a keyword. Change `_call` to
  accept a `varargs_name` parameter (optional, defaults None). When set,
  pop that key from the dict and call
  `callable_obj(*values, **arguments)`.
- `_get_args_name_from_parser` already reads parser actions to find
  arg names; verify that a `nargs="*"` positional shows up in the
  list and is passed to `_call`. The varargs name must be known at
  dispatch time — the cleanest path is to stash it on the parser as
  a custom attribute (`parser._parse_this_varargs = varargs_name`) and
  read it back in the dispatch functions (`_get_parser_call_method`
  inner `inner_call`, `_call_method_from_namespace`, and the
  `FunctionParser.__call__` direct call).

### 3. `_check_types` arity

`_check_types` in `parse_this/type_check.py` compares
`len(annotations) > len(func_args)` and similar. With varargs present,
the `annotations` dict may include the varargs name but `func_args`
won't contain it. Strip the varargs name from the annotations dict
before the check, and also pass `varargs_name` through so `_check_types`
knows about it.

Alternatively, handle this in the calling site: pass a filtered
annotations dict to `_check_types` that excludes the varargs key, and
let `_check_types` stay ignorant of varargs. Lower churn — prefer this.

### 4. `_get_arg_parser` and `_add_required_argument`

Add a new code path in `_get_arg_parser` (or a new `_add_varargs`
helper) that registers the varargs argument. `nargs="*"` with a
concrete type is standard argparse — no new complexity.

The varargs argument must be registered **after** every other explicit
argument, because argparse's positional matching is left-to-right and
a `nargs="*"` in the middle would swallow everything.

### 5. README

- Remove the combined `*args`/`**kwargs` bullet from
  "Caveats and limitations".
- Add a short "Variadic positional arguments (`*args`)" subsection
  under "Argument types" with a runnable example.
- Add `**kwargs` to the errors section.

## Files

- `parse_this/parsers.py` — detect `varargs`/`varkw` in both call sites;
  thread `varargs_name` into the parser construction and dispatch.
- `parse_this/parsing.py` — new `_add_varargs_argument` helper or new
  branch in `_get_arg_parser`; register `nargs="*"` positional.
- `parse_this/call.py` — `_call` accepts optional `varargs_name` and
  splats the corresponding list.
- `parse_this/type_check.py` — unchanged if the caller filters out
  the varargs key before passing `annotations`.
- `test/varargs_test.py` (new) — cases:
  - `*args` with int annotation, supplied values
  - `*args` with int annotation, no supplied values (empty tuple)
  - `*args` without annotation → defaults to `str`
  - `*args` combined with a required positional and an optional flag
  - `*args` inside a `@parse_class` method
  - `**kwargs` → `ParseThisException` at decoration time
  - Function with both `*args` and `**kwargs` → same kwargs error
    (kwargs fails fast, varargs support never reached)
- `README.md` — new `*args` subsection; caveats bullet removed;
  errors section bullet added.

## Verification

- `pytest`
- `pre-commit run --all-files`
- Manual: `def total(*nums: int)` with `python script.py 1 2 3` → `6`.
- Manual: `def f(**opts)` → decoration-time error naming `opts`.

## Risk

Medium. Touches the dispatch path (`call.py`) which is core. Mitigated
by: the change to `_call` is additive (new optional parameter); the
existing call paths keep working unchanged; new tests exercise varargs
end-to-end.
