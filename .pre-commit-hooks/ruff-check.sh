#!/usr/bin/env bash
set -e
cd "$(git rev-parse --show-toplevel)"

# Run ruff check with auto-fix
# Without --exit-non-zero-on-fix, ruff returns:
# - 0 if all issues are fixed or fixable
# - non-zero only if there are unfixable errors
uv run ruff check --fix "$@"

# Auto-stage any files that were modified by ruff
# This makes the workflow smoother - fixes are automatically staged
git add -u
