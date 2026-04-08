# Plan: Restructure README for top-down clarity, full feature coverage, and accuracy

## Context

The current README at `/Users/bert/github/parse_this/README.md` (~720 lines) has grown organically as features were added (Literal, version flag, log level, etc.). It works but is bottom-up: it dives into a complex `parse_class` example before establishing high-level concepts, configuration options are scattered, and a few statements no longer match the code. The goal is to restructure it top-down — concept first, then progressively more detail — while ensuring every user-facing feature is documented and every claim is accurate.

## Audit findings

**Inaccuracies to fix:**
1. **Private method name stripping** (line 95–97): says "stripped of all `_`s" — code uses `.strip("_")` which only removes *leading and trailing* underscores. Reword and add an `__str__` → `str` example alongside an `_inner` → `inner` example.
2. **Docstring delimiter whitespace tolerance** (line 196): the regex `(?P<arg_name>\w+)\s*<delim>\s*(?P<help>.+)` allows whitespace around the delimiter; README implies it must be tight. Mention the tolerance.
3. **Bool-without-default example** (line 249–260): the example return value is misleading — clean it up so the `(value, True)` shape is unambiguous.

**Features in code but missing or under-documented in README:**
1. **`instance=` parameter on `<Class>.parser.call()`** — lets users pass a pre-built instance instead of letting parse_this construct one from CLI args. Currently undocumented.
2. **`name=` on `@create_parser`** — briefly mentioned (line 98) but no example. Add one showing the rename.
3. **Bare `list`/`tuple` annotations** — README mentions strings are used as elements but provides no example.
4. **`ParseThisException`** — referenced in three places but never centralized. Add a short "Errors" section listing exactly when it's raised: missing required type annotations, `None` default without type, mixed-type Literal, default not in Literal choices, decorating `__init__` outside `parse_class`.
5. **Method-name `_` → `-` transformation** — only mentioned in passing; show a clear example (`do_stuff` → `do-stuff`).

**Sections that need to be added (currently missing entirely):**
1. **"What is parse_this?"** — a short, conceptual intro that frames the problem before any code.
2. **"Quick start"** — the smallest possible runnable example (single decorated function), separate from the full `parse_class` example.
3. **"Three entry points"** — a brief comparison table or list explaining when to use `parse_this` vs `create_parser` vs `parse_class`. Currently the user has to read the whole doc to figure this out.
4. **"Errors"** — centralized list of `ParseThisException` triggers.

**Things I am explicitly NOT adding:**
- API reference section — the library is small enough that the per-feature sections cover it; an API reference would duplicate content.
- Documentation of `SubcommandAwareArgumentParser` or `FullHelpAction` — internal classes, not part of the public API.
- FAQ — premature.

## Target structure

The rewritten README will follow this top-down ordering. Existing content is preserved where accurate; new content is added where noted. Section names are final.

1. **Title + badges + tagline** (existing, keep)
2. **What is parse_this?** *(new, ~10 lines)* — the problem (writing argparse boilerplate), the solution (signature + docstring → CLI), and the three entry points named in one sentence.
3. **Installation** *(moved up from bottom)* — `pip install parse_this`.
4. **Quick start** *(new)* — a single-function `@create_parser` example, ~15 lines, runnable end-to-end. The "smallest thing that works."
5. **The three entry points** *(new, brief)* — a short table or bulleted list:
   - `parse_this(func)` — one-shot, no decoration
   - `@create_parser` — decorator, attaches `.parser` to a function/method
   - `@parse_class` — class decorator, builds a multi-subcommand CLI
6. **Using `@create_parser` on a function** *(reworked from current "Decorator" section)*
7. **Using `parse_this` as a function** *(reworked from current "Function" section)*
8. **Building a class-based CLI with `@parse_class`** *(reworked from current "Usage" — this is the most involved entry point and now lives later, after the simple cases)*
   - Includes the existing `ParseMePlease` example
   - Subsection: **Method names** — `_` → `-` transformation, private method exposure with `parse_private`, `name=` rename, `__str__` → `str` (with corrected wording)
   - Subsection: **Custom top-level description** (`description=`)
   - Subsection: **Pre-built instances** (`instance=` on `.parser.call()`)
9. **Classmethods** *(existing, keep with minor edits)*
10. **Writing docstrings for help messages** *(reworked from current "Help message")*
    - Format spec
    - `delimiter_chars` (with whitespace tolerance noted)
11. **Argument types** *(consolidated from "Arguments and types", "Using None as default and bool as flags", "Enum arguments", "Literal arguments", "List and tuple arguments")*
    - Basic types (int, str, float, …)
    - `None` defaults (must be annotated)
    - `bool` flags (with-default and without-default behavior)
    - `enum.Enum`
    - `typing.Literal`
    - `list[T]` / `tuple[T, ...]` (and bare `list`/`tuple`)
12. **Optional features** *(new umbrella section grouping the keyword args)*
    - **`--log-level`** (existing "Log level" section, keep)
    - **`--version`** (existing "Version flag" section, keep)
13. **Errors** *(new)* — single section listing every condition that raises `ParseThisException`, with short code snippets where useful.
14. **Caveats and limitations** *(existing "CAVEATS", keep, possibly expand wording)*
15. **Development** *(merged from "RUNNING TESTS" and "Contributing and dev")* — venv setup, pre-commit, pytest, release process.
16. **License** *(existing, keep)*

## Critical files to modify

- `/Users/bert/github/parse_this/README.md` — the only file changed.

## Reference points (no changes needed, but to be cited for accuracy while writing)

- `parse_this/__init__.py` — public exports
- `parse_this/parsers.py` lines 50–92 (`FunctionParser`), 95–158 (`MethodParser`), 161–347 (`ClassParser`) — for keyword args and behavior
- `parse_this/parsing.py` — supported types and how each is wired
- `parse_this/help/description.py` lines 36–87 — docstring parsing and delimiter regex
- `parse_this/exception.py` — `ParseThisException`
- `parse_this/call.py` — `.parser.call()` semantics, `instance=` handling

## Approach to writing

- **Preserve existing examples where they're already correct** — most of the current code samples work. Reuse them rather than inventing new ones.
- **Run every example mentally against the actual signatures** before committing — no copy-paste from memory. The audit found three accuracy issues; we don't want to introduce more.
- **Aim for similar overall length** (~700 lines is fine). The goal is clarity and accuracy, not brevity for its own sake. Some sections shrink (consolidation), some grow (new content); net change should be modest.
- **One feature, one place** — no duplicating the version flag explanation across multiple sections.

## Verification

1. **Manual readthrough** — read the new README from top to bottom and confirm the top-down flow makes sense to a first-time reader.
2. **Cross-check every code sample against the source**:
   - For each example, verify the function signature matches what `parse_this`/`create_parser`/`parse_class` actually accept (kwargs, types, defaults).
   - For each described behavior, locate the corresponding code path in `parsers.py`/`parsing.py`/`call.py` and confirm it matches.
3. **Run a sample**: pick one non-trivial example from each major section and execute it in the venv (`source venv/bin/activate && python -c '...'`) to verify the documented output matches reality.
4. **Pre-commit**: `pre-commit run --all-files` (covers trailing whitespace, EOF, markdown sanity).
5. **Spot-check links**: ensure all link references at the bottom (`[pypi_link]`, `[python_version]`, etc.) still resolve and aren't orphaned.
