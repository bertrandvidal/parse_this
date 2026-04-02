# Plan: Environment Variable Fallback

## Context

CLI tools often allow setting defaults via environment variables (e.g., `--token` falls back to `$MY_TOKEN`). parse_this should support this via annotations or a helper, so argparse defaults are read from env vars when the CLI arg isn't provided.

## Tasks

### 1. Create Env helper
- Add a small descriptor/wrapper in `parse_this/types.py` (new file):
  ```python
  class Env:
      def __init__(self, var: str, type: Callable = str):
          self.var = var
          self.type = type
  ```
- Export from `parse_this/__init__.py`
- Usage: `def deploy(token: str = Env("DEPLOY_TOKEN"))`

### 2. Detect Env defaults in parsing.py
- In `_add_optional_argument`, when `default` is an `Env` instance:
  - Read `os.environ.get(default.var)`
  - If present, use it as the actual default (converted via `default.type`)
  - If absent, make the argument required (no default)
  - Include env var name in help text: `"(env: DEPLOY_TOKEN) ..."`
- File: `parse_this/parsing.py`

### 3. Add tests
- Env var set — used as default
- Env var unset — argument becomes required
- Env var with type conversion (e.g., `Env("PORT", int)`)
- File: `test/env_var_test.py`

## Verification
- `pytest`
- `pre-commit run --all-files`
