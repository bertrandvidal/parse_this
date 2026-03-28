# Plan: Document `--log-level` argument

## Branch
`document-log-level`

## Context

The `--log-level` feature is fully implemented and tested but not documented in
the README. The README explicitly lists "Add documentation in README on auto
`--log-level` argument" as a TODO item.

## Changes

| File | Change |
|---|---|
| `README.md` | Add "Log level" section after "Enum arguments"; remove TODO bullet |
| `.claude/plans/document-log-level.md` | This file |

## Commit Strategy

1. `docs: add plan file for document-log-level`
2. `docs: document --log-level argument and remove TODO`

## Verification

Documentation-only change. Verify README renders correctly.
