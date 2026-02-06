#!/usr/bin/env bash
set -e

# Setup just command completion for zsh or bash
# This script is idempotent - it won't duplicate entries if run multiple times

if ! command -v just > /dev/null 2>&1; then
    echo "⚠️  just not found - skipping completion setup"
    exit 0
fi

SHELL_NAME=$(basename "$SHELL")
COMPLETION_DIR=""
COMPLETION_FILE=""
RC_FILE=""
MARKER="# just command completion"

# Determine shell-specific paths
if [ "$SHELL_NAME" = "zsh" ]; then
    COMPLETION_DIR="$HOME/.zsh_completion.d"
    COMPLETION_FILE="$COMPLETION_DIR/_just"
    RC_FILE="$HOME/.zshrc"
    COMPLETION_SETUP="$MARKER
fpath=($COMPLETION_DIR \$fpath)
autoload -U compinit && compinit"
elif [ "$SHELL_NAME" = "bash" ]; then
    COMPLETION_DIR="$HOME/.bash_completion.d"
    COMPLETION_FILE="$COMPLETION_DIR/just"
    RC_FILE="$HOME/.bashrc"
    COMPLETION_SETUP="$MARKER
source $COMPLETION_FILE"
else
    echo "⚠️  Unsupported shell: $SHELL_NAME (supported: zsh, bash)"
    exit 0
fi

# Create completion directory
mkdir -p "$COMPLETION_DIR"

# Generate completion script
if just --completions "$SHELL_NAME" > "$COMPLETION_FILE" 2>/dev/null; then
    echo "✓ Generated completion script"
else
    echo "⚠️  Failed to generate completion script"
    exit 1
fi

# Add to shell config file (idempotent - check if marker already exists)
if [ -f "$RC_FILE" ]; then
    if grep -qF "$MARKER" "$RC_FILE" 2>/dev/null; then
        echo "✓ Completion already configured in $RC_FILE"
    else
        echo "" >> "$RC_FILE"
        echo "$COMPLETION_SETUP" >> "$RC_FILE"
        echo "✓ Added completion setup to $RC_FILE"
    fi
else
    echo "$COMPLETION_SETUP" >> "$RC_FILE"
    echo "✓ Created $RC_FILE with completion setup"
fi
