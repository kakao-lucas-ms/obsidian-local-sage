#!/bin/bash
# Obsidian Wrapper: Interactive Search (Terminal Version)
# Opens Terminal and runs the interactive hybrid search

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get query if provided
QUERY="${1:-}"

if [[ -n "$QUERY" ]]; then
    osascript <<EOF
tell application "Terminal"
    activate
    do script "cd '$SCRIPT_DIR/..' && ./scripts/obsidian-search-interactive.sh '$QUERY'; read -p 'Press Enter to close...'"
end tell
EOF
else
    osascript <<EOF
tell application "Terminal"
    activate
    do script "cd '$SCRIPT_DIR/..' && ./scripts/obsidian-search-interactive.sh; read -p 'Press Enter to close...'"
end tell
EOF
fi
