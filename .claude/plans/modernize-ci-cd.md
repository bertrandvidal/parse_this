# Plan: Modernize CI/CD

## Context

The GitHub Actions workflows work but have room for improvement: missing concurrency controls, no dependency caching, hardcoded CLI flags that belong in config, and no automated dependency updates.

## Tasks

### 1. Add `concurrency` groups to PR workflows
- Add to `pr-pre-submit-queue.yml` and `claude-code-review.yml`:
  ```yaml
  concurrency:
    group: ${{ github.workflow }}-${{ github.ref }}
    cancel-in-progress: true
  ```
- Prevents wasted CI minutes when pushing multiple commits to the same PR branch

### 2. Cache pip dependencies in CI
- Add `cache: pip` to the `actions/setup-python` step in `pr-pre-submit-queue.yml`
- Optionally add `cache-dependency-path` pointing to `pyproject.toml` (or `requirements.txt` until migration)

### 3. Consolidate lint/format/type-check CI steps
- If ruff replaces black+flake8 (see codebase plan), combine the formatting and linting steps into a single `ruff check` + `ruff format --check` step
- Keep mypy as a separate step (ruff does not replace type checking)
- Keep pytest+coverage as a separate step

### 4. Move coverage threshold to config
- Move `--cov-fail-under` from the CI workflow command line into `pyproject.toml` under `[tool.pytest.ini_options]` or `[tool.coverage.report]`
- Raise threshold from 95% to 99% (current coverage is 100%)
- Simplifies the CI invocation and keeps the threshold in one authoritative place

### 5. Add Dependabot configuration
- Create `.github/dependabot.yml` with update schedules for:
  - `github-actions` (weekly)
  - `pip` (weekly)
- Keeps Actions versions and Python dependencies current automatically

### 6. Update publish workflow for `pyproject.toml`
- Once `setup.py` is migrated, update version extraction in `publish-package-to-pypi.yml`
- Replace the `awk` parsing of `setup.py` with a proper extraction from `pyproject.toml` (e.g., `python -c "import tomllib; ..."`)
- Verify `python -m build` still works with the new build backend
