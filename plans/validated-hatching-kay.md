# Plan: Move Type Checking from mypy to ty

## Context

The project currently uses mypy for static type checking, integrated via pre-commit. Ty is a new Rust-based type checker from Astral (makers of ruff and uv), designed to be significantly faster. This migration swaps mypy for ty in both the pre-commit hooks and dev dependencies, and aligns the few type-ignore comments with ty's error code naming.

## Files to Modify

1. **`pyproject.toml`** — remove `[tool.mypy]` section, replace `mypy` with `ty` in dev deps
2. **`.pre-commit-config.yaml`** — replace the mypy hook with ty's hook
3. **`parse_this/call.py`** — update `# type: ignore[attr-defined]` → `# type: ignore[attribute-access]`
4. **`parse_this/parsers.py`** — update the two `# type: ignore[attr-defined]` occurrences

## Changes

### 1. `pyproject.toml`

Remove the `[tool.mypy]` section entirely:
```toml
# DELETE:
[tool.mypy]
no_strict_optional = true
show_error_codes = true
```

Replace `mypy` with `ty` in dev dependencies:
```toml
[project.optional-dependencies]
dev = [
    "ipython",
    "ty",          # was: mypy
    "pre-commit",
    "pytest",
    "pytest-cov",
    "ruff",
]
```

No `[tool.ty]` section is needed: ty has no equivalent of `no_strict_optional`
(it's always strict about None), and the codebase already uses explicit
`Optional[...]` everywhere, so no config is required.

### 2. `.pre-commit-config.yaml`

Replace the mirrors-mypy repo block with ty's pre-commit hook:
```yaml
# DELETE:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.19.1
    hooks:
      - id: mypy
        additional_dependencies: [tokenize-rt==6.1.0]

# ADD:
  - repo: https://github.com/astral-sh/ty
    rev: 0.0.0-alpha.6
    hooks:
      - id: ty
```

> **Note**: verify the latest ty release tag before committing by checking
> https://github.com/astral-sh/ty/releases.

### 3. `parse_this/call.py` line 24

```python
# Before:
parser = func.parser  # type: ignore[attr-defined]
# After:
parser = func.parser  # type: ignore[attribute-access]
```

### 4. `parse_this/parsers.py`

Line 158:
```python
# Before:
parser.get_name = lambda: self._name or func.__name__  # type: ignore[attr-defined]
# After:
parser.get_name = lambda: self._name or func.__name__  # type: ignore[attribute-access]
```

Line 250:
```python
# Before:
parser_name = parser.get_name()  # type: ignore[attr-defined]
# After:
parser_name = parser.get_name()  # type: ignore[attribute-access]
```

> The `@typing.no_type_check` decorators in `parsers.py` require no changes —
> ty respects this standard decorator.

## Verification

1. Run `ty check` to confirm no errors on the codebase
2. Run `pre-commit run --all-files` to verify the hook works end-to-end
3. Run `pytest` to confirm tests still pass with no regressions
4. Commit changes (pyproject.toml + .pre-commit-config.yaml changes in one commit;
   source code ignore-comment updates in another, or all together)
