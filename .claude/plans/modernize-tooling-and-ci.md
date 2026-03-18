# Plan: Future parse_this Improvements

## Context

With PR #22 merged (escape bug fix, CI modernization, Python 3.10+, latest GitHub Actions and black), the next round of improvements can build on a solid foundation.

## Future Work (prioritized)

### Tier 1 — Modernization
1. **Migrate `setup.py` to `pyproject.toml`** — modern packaging standard, centralizes tool config (black, mypy, pytest, flake8), fixes fragile awk-based version extraction in publish workflow
2. **Document `--log-level` feature** in README — existing TODO in both README and commit 045d292

### Tier 2 — Bug fixes / code quality
3. **Fix `_get_parser_call_method` wiping out method signatures** — breaks introspection (README TODO)
4. **Cover remaining test gaps** in `parsers.py` and `parsing.py` (99% coverage, a few uncovered lines)

### Tier 3 — New features
5. **Handle file arguments** (`argparse.FileType`) — README TODO
6. **Handle list/tuple arguments** (`nargs`) — README TODO
7. **Enum type support** with automatic `choices`
