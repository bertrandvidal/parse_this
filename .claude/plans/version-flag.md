# Plan: --version Flag Support

**Status:** Implemented (PR #46, merged).

## Context

Many CLI tools support `--version`. parse_this should make it easy to add a version flag to parsers, using argparse's built-in `"version"` action.

## Design Decisions

- **Opt-in via keyword arg**: `version` is `None` by default — no flag is added unless explicitly provided. Backward compatible.
- **String pass-through**: The library accepts a literal string and passes it verbatim to argparse. Users source the version themselves (recommended: `importlib.metadata.version("pkgname")`). No auto-discovery magic.
- **Format flexibility**: argparse's version action supports `%(prog)s` substitution, so users can write `version="%(prog)s 1.2.3"` to include the program name. Documented in README.
- **Not on `MethodParser`**: When a method is used as a subcommand inside `parse_class`, argparse's `parents=[parser]` mechanism would copy the `--version` action to every subcommand, producing weird CLI shapes like `python script.py 2 do-stuff --version`. Since the use case is fully covered by `parse_this(func, version=...)` for single-method CLIs and `parse_class(version=...)` for class-based CLIs, `MethodParser` does not get version support.
- **Type annotation**: `Optional[str]`, not bare `str = None` (mypy correctness).

## Tasks

### 1. Add version parameter to FunctionParser
- Add `version: Optional[str] = None` parameter to `FunctionParser.__call__`
- When provided, add `parser.add_argument("--version", action="version", version=version)` after parser construction, before `parse_args`
- File: `parse_this/parsers.py`

### 2. Add version parameter to ClassParser
- Add `version: Optional[str] = None` to `ClassParser.__init__` and store on `self`
- In `_set_class_parser`, when `self._version` is set, add `--version` to the top-level parser after `add_argument("-h", ...)`
- File: `parse_this/parsers.py`

### 3. Add tests
- `--version` on a `FunctionParser` prints the version and raises `SystemExit(0)` (capture stdout)
- `--version` on a `ClassParser` (top-level) prints version and exits
- Version string appears in `--help` output of the relevant parser
- Backward compat: omitting `version=` does NOT add a `--version` flag (passing `--version` errors as unrecognized)
- `%(prog)s` substitution works (verifies argparse pass-through)
- File: `test/version_test.py`

### 4. Update README
- Add a new section "Version flag" between "Log level" and "Decorator"
- Show the recommended `importlib.metadata.version("pkgname")` pattern as the primary example
- Show the `%(prog)s 1.2.3` formatting trick
- Show usage on both `parse_this(func, version=...)` and `@parse_class(version=...)`
- Note that `create_parser` does not accept `version` and explain why (subcommand interaction)

## Verification
- `pytest`
- `pre-commit run --all-files`
