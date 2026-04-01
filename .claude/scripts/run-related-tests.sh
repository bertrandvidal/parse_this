#!/usr/bin/env bash
# Runs tests related to a modified source file in parse_this/.
# Called by Claude Code PostToolUse hook with tool input as JSON on stdin.
# Exit 0 = success (informational), exit 2 = blocking error.

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only act on parse_this/ source files
[[ "$FILE_PATH" == */parse_this/*.py ]] || exit 0
# Skip __init__.py and py.typed
BASENAME=$(basename "$FILE_PATH" .py)
[[ "$BASENAME" == "__init__" ]] && exit 0

# Map source -> test file
case "$BASENAME" in
  type_check) TEST_FILE="test/types_test.py" ;;
  help|action|description)
    # help/ submodule files all map to help_test
    TEST_FILE="test/help_test.py" ;;
  *) TEST_FILE="test/${BASENAME}_test.py" ;;
esac

if [[ -f "$TEST_FILE" ]]; then
  source venv/bin/activate 2>/dev/null || true
  pytest "$TEST_FILE" --no-header -q 2>&1
fi
