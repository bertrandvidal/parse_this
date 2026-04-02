# Plan: Path/File Type Arguments

## Context

CLI tools frequently accept file paths. parse_this should recognize `pathlib.Path` annotations and `argparse.FileType` to provide automatic path conversion and file-exists validation.

## Tasks

### 1. Detect Path annotations in helpers.py
- Add `_is_path_type(arg_type)` that returns True for `pathlib.Path` and its subclasses
- File: `parse_this/helpers.py`

### 2. Handle Path in parsing.py
- In `_add_required_argument` and `_add_optional_argument`, when `_is_path_type(arg_type)`:
  - Use `type=Path` so argparse auto-converts strings to Path objects
- File: `parse_this/parsing.py`

### 3. Support FileType via Annotated
- Add `InputFile` and `OutputFile` helpers in `parse_this/types.py`:
  ```python
  InputFile = Annotated[str, _FileMode("r")]
  OutputFile = Annotated[str, _FileMode("w")]
  ```
- When detected, use `argparse.FileType(mode)` as the type converter
- Export from `parse_this/__init__.py`

### 4. Add tests
- `Path` annotation — receives Path object, not str
- `InputFile` — opens existing file for reading
- `OutputFile` — opens file for writing
- Path with default value
- File: `test/path_file_test.py`

## Verification
- `pytest`
- `pre-commit run --all-files`
