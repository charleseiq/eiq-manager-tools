#!/usr/bin/env bash
set -e
cd "$(git rev-parse --show-toplevel)"
uv run ruff check --fix --exit-non-zero-on-fix "$@"
