# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

* Read the README and follow its instructions
* All work requiring dependencies must be done inside a virtualenv, source once and maintain that context
* This repo uses `pre-commit` (black, flake8, mypy) - you don't need to lint, format, or type-check manually

## Commands

* **Run all tests:** `pytest`
* **Single test file:** `pytest test/parsers_test.py`
* **Single test:** `pytest test/parsers_test.py::TestClassName::test_name`
* **With coverage:** `pytest --cov=parse_this`

## Architecture

The public API (`parse_this/__init__.py`) exposes three entry points backed by classes in `parsers.py`:
- `parse_this` (FunctionParser) - parses CLI args and calls a function directly
- `create_parser` (MethodParser) - decorator adding `.parser` attribute to methods
- `parse_class` (ClassParser) - class decorator creating a top-level parser with subcommands from decorated methods

Processing pipeline: **signature inspection (`types.py`) -> arg/default extraction (`args.py`) -> parser construction (`parsing.py`) -> call dispatch (`call.py`)**. Docstring parsing for help messages lives in `help/`.

Key pattern: `MethodParser` attaches a `.parser` to decorated functions. `ClassParser` collects these and assembles them into a parent parser with subcommands (method names with `_` replaced by `-`).

## Workflow Rules

* All code changes must be tested
* All tools permissions should be in `.claude/settings.json`
* When `.claude/settings.json` is modified, add changes to a separate commit
* All work must be conducted on a branch named after the main objective of the work being done
* Plan files should be named after the branch name
* If more work is needed after the original plan, add to the plan file
* Plan files should be checked in and added to commits and PR
