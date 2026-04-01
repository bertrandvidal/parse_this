---
name: release
description: Bump version in pyproject.toml and open a release PR
argument-hint: "version (e.g. '4.1.0')"
---

# Release

You are preparing a release for the parse_this package. Follow these steps exactly:

## Step 1: Validate the version argument

- The argument is the new version string (e.g., `4.1.0`).
- Verify it follows semantic versioning (MAJOR.MINOR.PATCH).
- Read the current version from `pyproject.toml` and confirm the new version is higher.

## Step 2: Create a release branch

- Ensure you're starting from an up-to-date `main` branch: `git checkout main && git pull`.
- Create and switch to a new branch: `git checkout -b release/v<version>`.

## Step 3: Bump the version

- Update the `version` field in `pyproject.toml` to the new version.
- Search for any other references to the old version and update them if found.

## Step 4: Verify

- Activate the virtualenv and install the package: `pip install -e ".[dev]"`.
- Run the full test suite: `pytest`.
- Run pre-commit: `pre-commit run --all-files`.

## Step 5: Commit, push, and open PR

- Stage the changed files (do not use `git add -A`).
- Commit with message: `release: bump version to <version>`.
- Push the branch: `git push -u origin release/v<version>`.
- Open a PR targeting `main` with:
  - Title: `release: v<version>`
  - Body: summary of the version bump and a note that merging will trigger the publish workflow.
- Share the PR URL with the user.

## Important rules

- Do not make any code changes beyond the version bump.
- Do not tag the release — the publish workflow handles tagging on merge.
- If tests fail, stop and inform the user.
