---
name: implement-plan
description: Read a plan file, create a branch, implement changes with atomic commits, iterate on feedback, then push and open a PR
argument-hint: "plan file name (e.g. 'modernize-codebase.md')"
---

# Implement Plan

You are implementing a plan from a plan file. Follow these steps exactly:

## Step 1: Read and understand the plan

- Read the plan file at `.claude/plans/<argument>`. If the argument doesn't include the `.claude/plans/` prefix, prepend it. If it doesn't end in `.md`, append it.
- Understand all tasks and their dependencies.
- Summarize the plan to the user and confirm they want to proceed.

## Step 2: Set up the branch

- Derive a branch name from the plan file name (e.g., `modernize-codebase.md` becomes `modernize-codebase`).
- Ensure you're starting from an up-to-date `main` branch: `git checkout main && git pull`.
- Create and switch to the new branch: `git checkout -b <branch-name>`.
- Activate the virtualenv and install dependencies.

## Step 3: Implement each task with atomic commits

For each task in the plan, in order:

1. **Announce** which task you're starting.
2. **Implement** the code changes for that task.
3. **Write or update tests** to cover the changes.
4. **Run the full test suite** (`pytest`) and fix any failures.
5. **Run pre-commit** (`pre-commit run --all-files`) and fix any issues.
6. **Stage only the relevant files** for this task (no `git add -A`).
7. **Commit** with a clear message describing what was done and why, following the user's git template (~/.git-template.txt if it exists). Include `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`.
8. **Mark the task as done** in your tracking before moving to the next.

Do NOT bundle multiple tasks into a single commit unless they are genuinely inseparable.

## Step 4: User review

After all tasks are committed:

- Show the user a summary of all commits made (`git log --oneline main..<branch>`).
- Ask the user to review the changes.
- Wait for the user's feedback.

## Step 5: Iterate on feedback

If the user requests changes:

1. Make the requested modifications.
2. Run tests and pre-commit again.
3. Create a **new commit** for the fixes (do not amend previous commits unless explicitly asked).
4. Show the updated commit log.
5. Ask the user to review again.

Repeat until the user approves.

## Step 6: Push and open PR

Once the user approves:

1. Commit the plan used and include it in the PR
2. Push the branch: `git push -u origin <branch-name>`.
3. Open a PR using `gh pr create`:
   - Title: short description derived from the plan name (under 70 chars).
   - Body: summary of what was done, with a checklist of completed tasks from the plan.
   - Test: list all tests that have been run.
   - Target: `main`.
4. Share the PR URL with the user.

## Important rules

- Always work inside the virtualenv.
- Never force-push or amend commits unless the user explicitly asks.
- Never skip pre-commit hooks.
- If a pre-commit hook fails, fix the issue and create a new commit — do not amend.
- Keep the user informed of progress at each task boundary.
- If a task is blocked or unclear, ask the user before proceeding.
- When writing commit message be concise, sacrifice grammar/syntax for concision but still follow the commit template.
