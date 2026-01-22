#!/bin/bash
# Obsidian Wrapper: Document Jump v2 (Fixed)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Create wrapper script
TEMP_SCRIPT="/tmp/obsidian-jump-wrapper-$$.sh"

cat > "$TEMP_SCRIPT" <<EOF
#!/bin/bash
cd "$PROJECT_ROOT"

echo "📍 Obsidian Document Jump"
echo "================================"
echo ""

# Run document jump
"$SCRIPT_DIR/obsidian-jump.sh"

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
