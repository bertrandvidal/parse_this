# Plan: Modernize Claude Settings & Skills

## Context

Claude Code is integrated via code review and issue/PR workflows, plus local `settings.json` for tool permissions. There are opportunities to add hooks for automated quality checks, expand permissions for common commands, and improve the GitHub Action configurations.

## Tasks

### 1. Add pre-commit hook to Claude Code settings
- Use `update-config` skill to add a hook that runs `pre-commit run --all-files` before Claude creates commits
- Prevents Claude from creating commits that would fail CI
- Configuration goes in `.claude/settings.json` under `hooks`

### 2. Expand allowed bash commands in `settings.json`
- Add missing commonly needed commands:
  - `source` (for activating virtualenv)
  - `pip install` / `pip3 install` (for installing dependencies)
  - `pre-commit run` (for running specific pre-commit checks)
  - `pip install -e` (for editable installs)
- Review and clean up existing allowed commands for consistency

### 3. Fix Claude GitHub Action workflow permissions
- `claude-code-review.yml` has `pull-requests: read` but needs `pull-requests: write` to post review comments
- `claude.yml` similarly needs `pull-requests: write` and `issues: write` to respond to mentions
- Verify `contents: read` is sufficient or if `contents: write` is needed for any operations

### 4. Add a custom `/release` skill
- Create a skill that automates the release process:
  - Bumps version in `pyproject.toml` (after migration)
  - Updates any version references
  - Creates a PR targeting main
- Reduces manual steps and potential for version string errors

### 5. Add post-edit test hook
- Configure a hook that automatically runs relevant tests when Claude modifies source files in `parse_this/`
- Maps source files to their corresponding test files (e.g., `parse_this/parsing.py` -> `test/parsing_test.py`)
- Catches regressions immediately during development rather than at commit time
