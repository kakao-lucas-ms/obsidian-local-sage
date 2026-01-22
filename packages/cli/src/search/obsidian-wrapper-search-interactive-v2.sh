#!/bin/bash
# Obsidian Wrapper: Interactive Search v2 (Fixed)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
QUERY="${1:-}"

# Create wrapper script
TEMP_SCRIPT="/tmp/obsidian-search-wrapper-$$.sh"

cat > "$TEMP_SCRIPT" <<EOF
#!/bin/bash
cd "$PROJECT_ROOT"

echo "🔍 Obsidian Interactive Search"
echo "================================"
echo ""

# Run search script
if [ -n "$QUERY" ]; then
    python3 "$SCRIPT_DIR/obsidian-wrapper-search-v4.py" "$QUERY"
else
    echo "Usage: obsidian-search <query>"
    echo "Please provide a search query."
fi

# Keep terminal open if error
if [ \$? -ne 0 ]; then
    echo ""
    echo "================================"
    read -p "Press Enter to close..."
fi
EOF

chmod +x "$TEMP_SCRIPT"

# Open in Terminal
osascript <<APPLESCRIPT
tell application "Terminal"
    activate
    do script "$TEMP_SCRIPT"
end tell
APPLESCRIPT
