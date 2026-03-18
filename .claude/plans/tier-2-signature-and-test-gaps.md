# Plan: Tier 2 — Bug Fix and Test Coverage

## Context

The existing plan (`modernize-tooling-and-ci.md`) identifies Tier 2 work: fixing `_get_parser_call_method` wiping out method signatures, and covering test gaps in `parsers.py`/`parsing.py`. The major untested feature is `log_level=True` across all three parser classes.

**First step**: Rename branch `update-claude-settings` → `tier-2-signature-and-test-gaps` via `git branch -m tier-2-signature-and-test-gaps`. Existing CLAUDE.md/settings commits stay in the branch and will be part of the PR.

## Commit 1: Fix signature preservation in `_get_parser_call_method`

**`parse_this/call.py`**:
- Add `from functools import wraps`
- Add `@wraps(func)` decorator on `inner_call` (line 25)

**`test/call_test.py`**:
- `test_get_parser_call_method_preserves_name` — verify `__name__` matches original func
- `test_get_parser_call_method_preserves_doc` — verify `__doc__` matches original func
- `test_get_parser_call_method_preserves_wrapped` — verify `__wrapped__` is set

Uses existing `concatenate_string` from `test.helpers` (already imported).

**`README.md`**:
- Remove TODO line: "The `_get_parser_call_method` method wipes out the signature of the original method"

### Status: DONE

## Commit 2: Add tests for `log_level=True` across all parser classes

**`test/helpers.py`** — add fixtures:
- `function_with_log_level`: standalone function decorated with `create_parser(log_level=True)`
- `ParseableWithLogLevel`: class decorated with `parse_class(log_level=True)`

**`test/parsers_test.py`** — add tests:
- `test_function_parser_log_level` — FunctionParser with `log_level=True` parses `--log-level`
- `test_create_parser_with_log_level` — MethodParser `parser.call` works with `--log-level`
- `test_parse_class_with_log_level` — ClassParser works with `--log-level` in top-level args

Note: `--log-level` is added to the top-level parser only, so for ClassParser it must appear before the subcommand. Patch `logging.basicConfig` to avoid global state side effects.

### Status: DONE

## Commit 3: Direct tests for `_add_log_level_argument` and `_get_args_name_from_parser`

**`test/parsing_test.py`** — add to existing `TestParsing`:
- `test_add_log_level_argument` — verify `--log-level DEBUG` parses correctly
- `test_add_log_level_argument_not_required` — verify omitting it gives `None`
- `test_add_log_level_argument_invalid` — verify invalid choice raises `SystemExit`
- `test_get_args_name_from_parser` — verify returned names match expected args
- `test_get_args_name_from_parser_excludes_help` — verify help action excluded
- `test_get_args_name_from_parser_excludes_log_level` — verify `log_level` dest filtered out

Import `_add_log_level_argument` and `_get_args_name_from_parser` from `parse_this.parsing`.

### Status: DONE

## Files modified

- `parse_this/call.py` — wraps fix
- `test/call_test.py` — signature preservation tests
- `README.md` — remove TODO
- `test/helpers.py` — log_level fixtures
- `test/parsers_test.py` — log_level integration tests
- `test/parsing_test.py` — unit tests for parsing helpers

## Verification

```sh
source venv/bin/activate
pytest                          # 75 passed
pytest --cov=parse_this         # 100% coverage
pre-commit run --all-files      # all passed
```
