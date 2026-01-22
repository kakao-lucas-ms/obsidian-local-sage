#!/bin/bash
# Obsidian Wrapper: Document Jump (Terminal Version)
# Opens Terminal and runs the interactive document jump

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

osascript <<EOF
tell application "Terminal"
    activate
    do script "cd '$SCRIPT_DIR/..' && ./scripts/obsidian-jump.sh; exit"
end tell
EOF
