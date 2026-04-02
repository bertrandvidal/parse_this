# Plan: --version Flag Support

## Context

Many CLI tools support `--version`. parse_this should make it easy to add a version flag to parsers, using argparse's built-in `"version"` action.

## Tasks

### 1. Add version parameter to FunctionParser
- Add `version: str = None` parameter to `FunctionParser.__call__`
- When provided, add `parser.add_argument("--version", action="version", version=version)` before parsing
- File: `parse_this/parsers.py`

### 2. Add version parameter to MethodParser
- Add `version: str = None` to `MethodParser.__init__`
- When provided, add the version argument to the method's parser
- File: `parse_this/parsers.py`

### 3. Add version parameter to ClassParser
- Add `version: str = None` to `ClassParser.__init__`
- When provided, add to the top-level parser in `_set_class_parser`
- File: `parse_this/parsers.py`

### 4. Add tests
- Function with version flag — `--version` prints version and exits
- Class parser with version on top-level
- Method parser with version
- File: `test/version_test.py`

## Verification
- `pytest`
- `pre-commit run --all-files`
