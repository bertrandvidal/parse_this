# Extract parsing helpers, split `_get_arg_parser`

### Context
`parsing.py` is growing long by hosting utility functions that are not directly about the core parsing orchestration logic. Keeping `_is_enum_type`, `_make_enum_converter`, `_add_log_level_argument`, and `_get_args_name_from_parser` in the same file as the high-level `_get_arg_parser` and `_get_parseable_methods` makes the file harder to scan and maintain. Separately, `_get_arg_parser` contains a large inline `if default is _NO_DEFAULT` block whose two branches handle logically distinct cases (required vs optional arguments); inlining them makes the function hard to read and test in isolation.

### Architecture
- **New module `parse_this/helpers.py`** — receives the four helper functions (`_is_enum_type`, `_make_enum_converter`, `_add_log_level_argument`, `_get_args_name_from_parser`). A dedicated module is chosen over extending `args.py` (which is already focused on argument/default introspection) or `types.py` (which is about type-checking). `helpers.py` is a neutral home for small, reusable utilities that support the argument-building machinery without owning the orchestration.
- **Two new private functions in `parsing.py`**: `_add_required_argument(parser, func, arg, arg_type, help_msg)` and `_add_optional_argument(parser, func, arg, arg_type, default, help_msg)` — each absorbs one branch of the current `if default is _NO_DEFAULT` block inside `_get_arg_parser`. This keeps `_get_arg_parser` itself as the orchestrator and makes each branch independently readable.
- Import paths in `parsers.py` and `call.py` are updated to pull helpers from `parse_this.helpers`. The test file (`test/parsing_test.py`) imports from `parse_this.parsing` and must continue to resolve — so the moved symbols must remain importable from `parse_this.parsing` (re-exported via `from parse_this.helpers import …` at the top of `parsing.py`). This avoids any test changes while keeping the physical code in `helpers.py`.

### Files
| File | Action |
|---|---|
| `parse_this/helpers.py` | **Create** — new module holding the four extracted helper functions |
| `parse_this/parsing.py` | **Modify** — remove the four helper function bodies, add `from parse_this.helpers import …` re-export, extract two new private functions from `_get_arg_parser` |
| `parse_this/parsers.py` | **Modify** — replace `from parse_this.parsing import _add_log_level_argument` with `from parse_this.helpers import _add_log_level_argument` |
| `parse_this/call.py` | **Modify** — replace `from parse_this.parsing import _get_args_name_from_parser` with `from parse_this.helpers import _get_args_name_from_parser` |
| `.claude/plans/extract-parsing-helpers.md` | **Create** — plan document |

### Steps

1. **Create branch** — run `git checkout -b extract-parsing-helpers` from `main`.

2. **Write the plan file** — create `.claude/plans/extract-parsing-helpers.md` with the full plan content. Commit using the template at `~/.git-template.txt` with a message describing the plan addition.

3. **Create `parse_this/helpers.py`** — move the bodies of `_is_enum_type`, `_make_enum_converter`, `_add_log_level_argument`, and `_get_args_name_from_parser` verbatim from `parsing.py` into the new file. Add the necessary imports (`enum`, `logging`, `ArgumentParser`, `_HelpAction`, `ArgumentTypeError`, `Any`, `Callable`, `List`, `Type`). No logic changes — copy exactly.

4. **Update `parse_this/parsing.py`** — delete the four function bodies that were moved. Add `from parse_this.helpers import _add_log_level_argument, _get_args_name_from_parser, _is_enum_type, _make_enum_converter` so callers that import those names from `parse_this.parsing` (including `test/parsing_test.py`) continue to resolve without any change. Remove any imports in `parsing.py` that are no longer needed after the move (e.g. `ArgumentTypeError`, `_HelpAction` if not used elsewhere in the file). Verify the re-exports cover every name the test imports from `parse_this.parsing`.

5. **Commit step 3–4** — commit `parse_this/helpers.py` and `parse_this/parsing.py` together with a message: "Extract helper functions from parsing.py into helpers.py".

6. **Update `parse_this/parsers.py`** — replace `_add_log_level_argument` in the `from parse_this.parsing import …` line with an import directly from `parse_this.helpers`. Keep `_get_arg_parser` and `_get_parseable_methods` imported from `parse_this.parsing`. Commit with message: "Update parsers.py to import _add_log_level_argument from helpers".

7. **Update `parse_this/call.py`** — replace `from parse_this.parsing import _get_args_name_from_parser` with `from parse_this.helpers import _get_args_name_from_parser`. Commit with message: "Update call.py to import _get_args_name_from_parser from helpers".

8. **Extract `_add_required_argument` in `parsing.py`** — create a new private function with signature `_add_required_argument(parser: ArgumentParser, func: Callable, arg: str, arg_type: Any, help_msg: str) -> None`. Its body is the current `if default is _NO_DEFAULT:` branch verbatim (lines covering the `bool`, `_is_enum_type`, and plain-positional cases). In `_get_arg_parser`, replace that branch body with a call to `_add_required_argument(parser, func, arg, arg_type, help_msg)`.

9. **Extract `_add_optional_argument` in `parsing.py`** — create a new private function with signature `_add_optional_argument(parser: ArgumentParser, func: Callable, arg: str, arg_type: Any, default: Any, help_msg: str) -> None`. Its body is the current `else:` branch verbatim (lines covering the `None`-default guard, `bool`, `_is_enum_type`, and plain-optional cases). In `_get_arg_parser`, replace that branch body with a call to `_add_optional_argument(parser, func, arg, arg_type, default, help_msg)`. Commit steps 8–9 together with message: "Extract _add_required_argument and _add_optional_argument from _get_arg_parser".

10. **Open PR** — push the branch (`git push -u origin extract-parsing-helpers`) and open a pull request targeting `main` with title "Extract parsing helpers and split _get_arg_parser branches". Show the PR URL.

11. **Verify** — run the full test suite:
    ```
    python -m pytest
    ```
    All tests must pass with no import errors. Additionally confirm:
    ```
    python -c "from parse_this.parsing import _add_log_level_argument, _get_args_name_from_parser, _is_enum_type, _make_enum_converter"
    python -c "from parse_this.helpers import _add_log_level_argument, _get_args_name_from_parser, _is_enum_type, _make_enum_converter"
    ```
    Both must succeed without error.
