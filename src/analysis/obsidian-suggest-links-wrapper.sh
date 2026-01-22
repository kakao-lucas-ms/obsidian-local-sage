#!/bin/bash
# Bash wrapper for link suggestions

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

FILE_PATH="$1"

cd "$PROJECT_DIR"
python3 -u "$SCRIPT_DIR/obsidian-suggest-links.py" "$FILE_PATH" 2>&1
