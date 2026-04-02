# Plan: Repo Quality Improvements

## Context

After a modernization pass (pyproject.toml, ruff, CI/CD), a review surfaced documentation drift, minor code quality issues, and config gaps. All functional code is solid (100% coverage, clean architecture) — these are polish items.

## Tasks

### 1. Fix CLAUDE.md and pyproject.toml metadata
- `.claude/CLAUDE.md` line 9: change "black, flake8, mypy" to "ruff, mypy"
- `pyproject.toml`: fix double period in description (`"...classmethod.."` → `"...classmethod."`)
- `pyproject.toml`: add missing URLs (`Repository`, `Bug Tracker`)
- `pyproject.toml`: add `target-version = "py310"` to `[tool.ruff]`

### 2. Fix publish workflow tagging
- `.github/workflows/publish-package-to-pypi.yml`: the `git tag` command uses `${{ github.event.pull_request.base.ref }}` but the workflow triggers on `push` to main (no PR context) — change to `${{ github.sha }}`

### 3. Modernize string formatting to f-strings
- ~7 `.format()` calls across: `parse_this/help/action.py`, `parse_this/type_check.py`, `parse_this/parsers.py`, `parse_this/parsing.py`
- Convert to f-strings (Python >=3.10 is required)

### 4. Add return type annotations
- Missing in ~7 functions across: `parse_this/call.py`, `parse_this/parsing.py`, `parse_this/help/description.py`
- Add `@typing.no_type_check` comments explaining why suppression is needed in `parse_this/parsers.py` (3 occurrences)

### 5. Update Claude workflow action versions
- `.github/workflows/claude-code-review.yml`: `actions/checkout@v4` → `@v6`
- `.github/workflows/claude.yml`: `actions/checkout@v4` → `@v6`

### 6. Improve dependabot and gitignore
- `.github/dependabot.yml`: add PR grouping and commit message prefix
- `.gitignore`: add `.DS_Store`, `.vscode/`, `*.swp`, `*.orig`

## Verification
- `pytest` — all 91 tests pass
- `pre-commit run --all-files` — all hooks pass
- `ruff check parse_this test && ruff format --check parse_this test`
- `mypy parse_this test`
