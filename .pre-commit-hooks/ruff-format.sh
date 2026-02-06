#!/usr/bin/env bash
set -e
cd "$(git rev-parse --show-toplevel)"

# Run ruff format
uv run ruff format "$@"

# Auto-stage any files that were formatted
git add -u
