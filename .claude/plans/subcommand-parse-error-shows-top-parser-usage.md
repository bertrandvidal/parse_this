# subcommand-parse-error-shows-top-parser-usage

## Issue Description

When using `parse_class`, parsing errors in a subcommand do not consistently show
the subcommand's own usage. The behaviour differs depending on the type of error.

---

### Case 1: Wrong type or missing required argument — subcommand usage shown ✅

When a subcommand receives a value of the wrong type or is missing a required
argument, `argparse` routes the error to the subparser directly. The output
correctly identifies the subcommand:

```
usage: myprog top_arg sub-cmd [-h] sub_arg
myprog top_arg sub-cmd: error: argument sub_arg: invalid int value: 'not_an_int'
```

```
usage: myprog top_arg sub-cmd [-h] sub_arg
myprog top_arg sub-cmd: error: the following arguments are required: sub_arg
```

---

### Case 2: Unrecognized argument — top-level parser usage shown ⚠️

When a subcommand receives an unrecognized flag or extra positional argument,
the error message shows the **top-level parser's usage** instead of the
subcommand's:

```
usage: myprog [-h] top_arg {sub-cmd} ...
myprog: error: unrecognized arguments: --unknown-flag
```

The user is given no indication of which subcommand caused the error, and the
usage shown lists all available subcommands rather than the signature of the
one they were trying to invoke.

This is because `argparse` processes unrecognized tokens via `parse_known_args`
at the subparser level, accumulates them, and then has the **top-level parser**
call `error()` at the end. The top parser owns the final validation pass, so it
is the one that reports the failure.

---

### Contrast with Click

Click consistently shows the **subcommand's usage** for every class of error —
wrong type, missing argument, and unrecognized option alike:

```
Usage: cli TOP_ARG sub-cmd [OPTIONS] SUB_ARG
Try 'cli TOP_ARG sub-cmd --help' for help.

Error: No such option: --unknown-flag
```

```
Usage: cli TOP_ARG sub-cmd [OPTIONS] SUB_ARG
Try 'cli TOP_ARG sub-cmd --help' for help.

Error: Invalid value for 'SUB_ARG': 'not_an_int' is not a valid integer.
```

```
Usage: cli TOP_ARG sub-cmd [OPTIONS] SUB_ARG
Try 'cli TOP_ARG sub-cmd --help' for help.

Error: Missing argument 'SUB_ARG'.
```

---

## Fix

The inconsistency is fixed by introducing `SubcommandAwareArgumentParser`, a
subclass of `ArgumentParser`, that intercepts the unrecognized-argument code
path and re-routes the error to the correct subparser.

---

## Implementation

### `SubcommandAwareArgumentParser` — `parse_this/parsers.py`

A new class `SubcommandAwareArgumentParser(ArgumentParser)` is defined at
module level in `parse_this/parsers.py`.

**`__init__`** adds a single extra instance attribute:

```python
self._subparsers_action = None
```

This attribute is populated by `ClassParser._set_class_parser` after the
subparsers are registered (see below).

**`parse_args(args, namespace)`** overrides the standard implementation:

1. Calls `self.parse_known_args(args, namespace)` to collect both the parsed
   namespace and any remainder tokens that were not recognised.
2. If `remainder` is non-empty, checks whether a subcommand was selected by
   reading `namespace.method`.
3. If `self._subparsers_action` is set and `namespace.method` names a known
   choice, it retrieves `subparser = self._subparsers_action.choices[method]`
   and calls `subparser.error("unrecognized arguments: …")` — so the
   subcommand's usage is shown instead of the top-level usage.
4. Falls back to `self.error(…)` when no active subcommand can be identified
   (preserving the original behaviour for top-level unrecognized tokens).

### `ClassParser._add_sub_parsers` return value change — `parse_this/parsers.py`

Previously returned only `parser_to_method` (a `dict`). Now returns a 2-tuple:

```python
return parser_to_method, sub_parsers
```

The docstring is updated accordingly. This exposes the `subparsers` action
object to the caller so it can be stored on the top-level parser.

### `ClassParser._set_class_parser` — `parse_this/parsers.py`

Two changes:

1. **Parser instantiation** — replaces `ArgumentParser(…)` with
   `SubcommandAwareArgumentParser(…)` so the top-level parser gains the
   unrecognized-argument interception behaviour.

2. **Wiring the subparsers action** — unpacks the 2-tuple from
   `_add_sub_parsers` and assigns the action:

```python
parser_to_method, sub_parsers_action = self._add_sub_parsers(…)
top_level_parser._subparsers_action = sub_parsers_action
```

---

## Testing

### Fixture — `test/helpers.py`

`SubCmdParseError` is a `@parse_class()`-decorated class with:

- `__init__(self, top_arg: int)` — accepts one integer at the top level.
- `sub_cmd(self, sub_arg: int)` — a subcommand that accepts one integer.

This mirrors the minimal structure needed to reproduce the unrecognized-argument
error path.

### Regression test — `test/parsers_test.py`

`test_subcommand_parse_error_shows_subcommand_usage_not_top_parser` in
`TestClassParser`:

- Invokes `SubCmdParseError.parser.call("1 sub-cmd 2 --unknown-flag".split())`.
- Captures stderr via `captured_output()`.
- Asserts `"sub-cmd"` appears in the error output — confirming the subcommand's
  usage line was printed.
- Asserts `"{sub-cmd}"` does **not** appear — confirming the top-level parser's
  usage (which lists subcommands inside braces) was not printed.

This test serves as a permanent regression anchor: if the fix is ever reverted
or broken, the test will fail immediately.
