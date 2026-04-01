# Plan: Modernize Codebase

## Context

The codebase uses legacy packaging (`setup.py`) and separate config files for each tool (`.flake8`, `.mypy.ini`). Modernizing to current Python standards consolidates configuration, simplifies maintenance, and improves the experience for contributors and downstream consumers.

## Tasks

### 1. Migrate `setup.py` to `pyproject.toml`
- Convert all metadata, dependencies, and `python_requires` into `[project]` table
- Choose build backend (`hatchling` or `setuptools>=64` with `[build-system]`)
- Move flake8 config from `.flake8` into `pyproject.toml` (via ruff, see #4) or keep if staying with flake8
- Move mypy config from `.mypy.ini` into `[tool.mypy]`
- Add pytest config under `[tool.pytest.ini_options]` (coverage threshold, cache-clear, etc.)
- Remove `setup.py`, `.flake8`, `.mypy.ini` once consolidated
- Update README dev setup instructions

### 2. Move dev dependencies from `requirements.txt` to `pyproject.toml`
- Add `[project.optional-dependencies]` with a `dev` extra: `dev = ["black", "flake8", "mypy", ...]`
- Install via `pip install -e ".[dev]"` instead of `pip install -r requirements.txt`
- Remove `requirements.txt`
- Update README, CLAUDE.md, and CI workflows to use new install command

### 3. Replace `flake8` + `black` with `ruff`
- Add `[tool.ruff]` config in `pyproject.toml` matching current black (line-length=88) and flake8 (extend-ignore E203) settings
- Update `.pre-commit-config.yaml` to use `astral-sh/ruff-pre-commit` instead of separate black and flake8 hooks
- Update CI workflow to run `ruff check` and `ruff format --check` instead of separate black/flake8 steps
- Remove `.flake8` if not already removed in step 1

### 4. Add Python 3.14 to test matrix
- Add `"3.14"` to the CI matrix in `pr-pre-submit-queue.yml`
- Add classifier to `pyproject.toml`
- Mark as `allow-failure` initially since 3.14 is in beta

### 5. Add `py.typed` marker
- Create empty `parse_this/py.typed` file
- Include it in package data in `pyproject.toml`

### 6. Update pre-commit hook versions
- Run `pre-commit autoupdate` to bring all hooks to latest
- Verify hooks still pass
