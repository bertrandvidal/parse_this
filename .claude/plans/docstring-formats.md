# docstring-formats: Support Google, NumPy, reST, and Epytext docstrings

## Context

Today `parse_this/help/description.py` ships a single homemade docstring
parser. It is a permissive line-based regex
(`(?P<arg_name>\w+)\s*<delim>\s*(?P<help_msg>.+)`) that effectively
recognises a Google-ish `Args:` block but with a configurable delimiter
(`delimiter_chars`, default `:`). It does **not** understand:

- Section headers as boundaries (a stray blank line breaks parsing — see
  the existing `blank_line_in_wrong_place` fixture, which intentionally
  loses an arg).
- NumPy-style underlined `Parameters\n----------` sections.
- reST/Sphinx `:param name:` directives.
- Epytext `@param name:` directives.
- Type fields (`name (int):` Google, `name : int` NumPy, `:type x:` reST).

The user wants `parse_this` to be friendly to projects already documented
in any of the four mainstream Python docstring styles, without forcing
authors to rewrite their docstrings just to get a CLI.

The decision (locked via AskUserQuestion in plan mode):

1. **Implementation:** depend on the MIT-licensed `docstring-parser`
   library — it already handles all four formats and is actively
   maintained. This becomes the library's first runtime dependency.
2. **Formats:** support all four — Google, NumPy, reST, Epytext.
3. **Selection:** auto-detect by default; allow explicit override via a
   new `docstring_style=` kwarg on the public decorators.
4. **Backward compat:** fold the legacy custom-delimiter parser into the
   Google-style parser. The `delimiter_chars=` parameter is removed
   entirely. **This is a breaking change** for anyone passing a non-`:`
   delimiter; release as a major version bump.

## Goals

- `parse_this`, `create_parser`, and `parse_class` work out-of-the-box on
  functions documented in any of the four supported styles.
- Users can pin a style explicitly with `docstring_style="google"` (or
  `"numpy"`, `"rest"`, `"epytext"`, `"auto"`) when auto-detection guesses
  wrong.
- The argparse `description` and per-argument `help` text are populated
  from the parsed docstring exactly as today (same return shape from
  `prepare_doc`).
- Existing tests for missing/partial docstrings, multiline help, and
  no-docstring fallback still pass.

## Non-goals

- Type extraction from docstrings — annotations are still the source of
  truth for converters; we only consume `description` and `arg_name` from
  the parsed result.
- Returns / Raises / Yields rendering — argparse has nowhere to put them.
- Preserving `delimiter_chars` for one release as a deprecation. Per the
  user's choice, it goes immediately.

## Public API changes

| Symbol | Before | After |
|---|---|---|
| `parse_this(func, args=None, delimiter_chars=":", log_level=False, version=None)` | — | `parse_this(func, args=None, docstring_style="auto", log_level=False, version=None)` |
| `@create_parser(delimiter_chars=":", name=None, log_level=False)` | — | `@create_parser(docstring_style="auto", name=None, log_level=False)` |
| `@parse_class(...)` | — | unchanged (each method's `@create_parser` carries its own `docstring_style`) |
| `prepare_doc(func, args, delimiter_chars)` | — | `prepare_doc(func, args, style="auto")` |
| `_get_arg_parser(..., delimiter_chars, ...)` | — | `_get_arg_parser(..., style, ...)` |

`delimiter_chars` disappears from every signature. Users currently
relying on a non-`:` delimiter must either rewrite their docstrings to
use `:` (Google) or migrate to one of the other now-supported styles.

## Style auto-detection

`docstring-parser`'s `parse(docstring)` already auto-detects when called
without an explicit `style=`. We delegate detection to it. The `"auto"`
sentinel in our public API maps to `docstring_parser.DocstringStyle.AUTO`.

When `docstring-parser` raises `ParseError` (malformed input that no
style matches), we fall back to `_get_default_help_message`, the same
behaviour as today for an empty docstring.

## Implementation tasks (5 atomic commits)

Each commit on the `docstring-formats` branch off a fresh `main`. Stop,
test, pre-commit, commit between each.

### Commit 1 — `chore: add docstring-parser runtime dependency`

- `pyproject.toml`: add a new top-level `dependencies = ["docstring-parser>=0.16"]`
  list under `[project]`. The version floor matches the `DocstringStyle`
  enum spelling we will reference.
- No code changes; just verifies the dep installs cleanly under
  `pip install -e .[dev]`.

### Commit 2 — `refactor!: rewrite prepare_doc on docstring-parser, drop delimiter_chars`

This is the load-bearing commit. The legacy regex parser and the
`delimiter_chars` parameter both disappear in the same change because
keeping one without the other would leave a phantom argument.

**`parse_this/help/description.py`**
- Replace the body of `prepare_doc` with a call into `docstring_parser`:
  ```python
  from docstring_parser import parse, DocstringStyle, ParseError

  _STYLE_MAP = {
      "auto":    DocstringStyle.AUTO,
      "google":  DocstringStyle.GOOGLE,
      "numpy":   DocstringStyle.NUMPYDOC,
      "rest":    DocstringStyle.REST,
      "epytext": DocstringStyle.EPYDOC,
  }

  def prepare_doc(func, args, style="auto"):
      if not func.__doc__:
          return _get_default_help_message(func, args)
      try:
          ds_style = _STYLE_MAP[style]
      except KeyError:
          raise ParseThisException(
              f"Unknown docstring_style {style!r}. "
              f"Expected one of {sorted(_STYLE_MAP)}."
          )
      try:
          parsed = parse(func.__doc__, style=ds_style)
      except ParseError:
          return _get_default_help_message(func, args)
      description = " ".join(
          p for p in (parsed.short_description, parsed.long_description) if p
      ) or None
      args_help = {
          p.arg_name: p.description
          for p in parsed.params
          if p.description
      }
      return _get_default_help_message(func, args, description, args_help)
  ```
- Keep `_get_default_help_message` exactly as-is — same return shape, same
  fallback semantics.
- Drop the `re` import and the regex.

**`parse_this/parsing.py`**
- `_get_arg_parser`: rename `delimiter_chars: str` to `style: str`, pass it
  through to `prepare_doc(func, all_arg_names, style)`. Update the
  docstring.

**`parse_this/parsers.py`**
- `FunctionParser.__call__`: replace `delimiter_chars: str = ":"` with
  `docstring_style: str = "auto"`. Pass it to `_get_arg_parser`.
- `MethodParser.__init__`: replace `delimiter_chars: str = ":"` with
  `docstring_style: str = "auto"`. Store as `self._docstring_style`.
- `MethodParser.__call__`: pass `self._docstring_style` to
  `_get_arg_parser`.
- `ClassParser`: no signature change — methods carry their own style.

**`test/helpers.py`**
- Delete `different_delimiter_chars` (the only fixture exercising the
  removed delimiter behaviour).
- Delete `blank_line_in_wrong_place` OR rewrite its docstring as a clean
  Google block — `docstring-parser` will not reproduce the legacy
  half-broken behaviour the existing test asserts. (Plan: delete it; the
  test it backs is testing a misfeature.)
- Keep `parse_me_full_docstring`, `multiline_docstring`, `parse_me`,
  `parse_me_no_docstring`, `no_docstring`, `with_args` — all are valid
  Google style and should round-trip cleanly.

**`test/help_test.py`**
- Delete `test_prepare_doc_blank_line_in_wrong_place` and
  `test_prepare_doc_delimiter_chars`.
- Update `test_prepare_doc_full_docstring`,
  `test_prepare_doc_will_you_dare`, `test_prepare_doc_no_docstring`,
  and the two `_get_default_help_message` tests to drop the
  `delimiter_chars` positional argument.

**Other test files**
- `grep -rn delimiter_chars test/` to find any other call sites and
  update them.

### Commit 3 — `feat: add docstring_style override and per-format tests`

This commit is purely additive on top of commit 2 — it ships the
override kwarg's behaviour and the new format support tests. (Commit 2
already wired the kwarg through; commit 3 proves it works for each
format end-to-end.)

**`test/docstring_styles_test.py`** (new) — one test class per format,
each verifying:

- Auto-detection picks the correct style when the docstring uses it.
- Explicit `docstring_style="<format>"` round-trips description and per-
  arg help.
- A function with no docstring still falls back to defaults.
- A function with a docstring whose `Args`/`Parameters`/`:param` block
  omits one of the parameters falls back to the default help message
  for that parameter only.

Per-format fixtures (define inline in the test file, no need to pollute
`test/helpers.py`):

```python
def google(one: int, two: str):
    """Google-style demo.

    Args:
        one: first value
        two: second value
    """

def numpy_(one: int, two: str):
    """NumPy-style demo.

    Parameters
    ----------
    one : int
        first value
    two : str
        second value
    """

def rest(one: int, two: str):
    """reST-style demo.

    :param one: first value
    :param two: second value
    """

def epytext(one: int, two: str):
    """Epytext-style demo.

    @param one: first value
    @param two: second value
    """
```

Plus:
- `test_unknown_style_raises_parse_this_exception` — passing
  `docstring_style="klingon"` raises `ParseThisException` listing the
  valid choices.
- `test_malformed_docstring_falls_back_to_defaults` — feed a docstring
  that no parser can match (e.g. just a heading underline with no
  body) and assert default help text is used.
- `test_create_parser_passes_style_to_prepare_doc` — decorate a function
  with `@create_parser(docstring_style="numpy")` and assert the parser's
  per-argument `help` text matches the NumPy block.
- `test_parse_class_methods_use_their_own_style` — two methods on one
  `@parse_class`, each decorated with `@create_parser(docstring_style=…)`
  using a different format; assert both parse correctly.

### Commit 4 — `docs: document docstring format support`

**`README.md`**
- Replace any reference to `delimiter_chars` (search for the term) with
  documentation of `docstring_style`.
- Add a "Docstring formats" subsection under the existing help-text
  documentation listing the four supported formats with one short
  example each, and noting auto-detection plus the override kwarg.
- Add a clear "Breaking changes in v5" callout at the top of the
  README (or in CHANGELOG if one exists) describing the
  `delimiter_chars` removal and the migration path (rewrite to `:` or
  pick another style).

**`pyproject.toml`**
- Bump `version = "4.0.8"` to `version = "5.0.0"` to signal the breaking
  change.

### Commit 5 — `chore: add docstring-formats plan file`

- Copy `/Users/bert/.claude/plans/bright-hugging-penguin.md` (this file)
  to `.claude/plans/docstring-formats.md` in the repo, per the project's
  workflow rule that plan files are checked in alongside the work they
  describe.

## Critical files

| File | Change |
|---|---|
| `pyproject.toml` | Add `docstring-parser` runtime dep; bump major |
| `parse_this/help/description.py` | Body of `prepare_doc` rewritten on `docstring-parser`; legacy regex deleted |
| `parse_this/parsing.py` | `_get_arg_parser` signature: `delimiter_chars` → `style` |
| `parse_this/parsers.py` | `FunctionParser`, `MethodParser` signatures: `delimiter_chars` → `docstring_style` |
| `test/help_test.py` | Drop delimiter/blank-line tests; update other calls |
| `test/helpers.py` | Drop `different_delimiter_chars` and `blank_line_in_wrong_place` fixtures |
| `test/docstring_styles_test.py` (new) | Per-format coverage |
| `README.md` | Document `docstring_style`, breaking-change notice |
| `.claude/plans/docstring-formats.md` (new) | Checked-in plan file |

## Reused functions

- `_get_default_help_message` in `parse_this/help/description.py` — kept
  verbatim. New `prepare_doc` calls it for both the no-docstring and
  partial-docstring cases.
- `ParseThisException` in `parse_this/exception.py` — used for the
  unknown-style error.

## Verification

1. **Unit tests:** `pytest` — all tests, including the new
   `test/docstring_styles_test.py`, must pass; 99% coverage gate must
   stay green (currently set in `pyproject.toml`).
2. **Pre-commit:** `pre-commit run --all-files` — ruff and mypy clean.
3. **Manual smoke test:** in a scratch script, decorate the same
   function written in each of the four styles and confirm
   `script.py --help` shows the correct per-argument help in each case.
4. **Manual override test:** decorate a Google-style function with
   `@create_parser(docstring_style="numpy")` and confirm the help text
   falls back to `Help message for <arg>` defaults (mismatched style
   should not match args).
5. **Manual breaking-change test:** confirm that an old call like
   `@create_parser(delimiter_chars="--")` raises `TypeError: unexpected
   keyword argument 'delimiter_chars'` — i.e. the removal is loud, not
   silent.

## Risk

Medium-high. The breaking change is the biggest risk — anyone depending
on `delimiter_chars` will see decoration-time `TypeError`s. Mitigation:
the v5.0.0 bump in pyproject signals the break loudly, and the README
"Breaking changes" callout in commit 4 documents the migration. The
`docstring-parser` dependency is small, MIT-licensed, ~140M downloads/
month, but introduces a supply-chain surface that did not exist before;
acceptable trade for ~150 LOC of bespoke regex deleted.

## Workflow

This work **stacks** on top of `varargs-kwargs-handling` (the in-flight
varargs PR), not `main`. The four prior PRs (#49-52) were stacked and
this one continues that chain.

1. Fetch latest: `git fetch origin`.
2. From the tip of the stack: `git checkout varargs-kwargs-handling &&
   git pull`.
3. Branch off it: `git checkout -b docstring-formats`.
4. Activate venv, `pip install -e .[dev]`, then install
   `docstring-parser` (the new dep). Run `pytest` once before changes
   to confirm baseline green.
5. Implement commit 1 → test → commit. Repeat for commits 2-5.
6. Open PR with `--base varargs-kwargs-handling` so it targets the
   parent branch in the stack. Retarget to `main` once
   `varargs-kwargs-handling` merges. Link this plan in the PR body.
