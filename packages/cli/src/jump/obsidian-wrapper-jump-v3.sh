#!/bin/bash
# Obsidian Wrapper: Document Jump v3 (Fixed delimiter)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

TEMP_SCRIPT="/tmp/obsidian-jump-wrapper-$$.sh"

cat > "$TEMP_SCRIPT" <<EOF
#!/bin/bash
cd "$PROJECT_ROOT"

echo "📍 Obsidian Document Jump"
echo "================================"
echo ""

# Run fixed document jump
"$SCRIPT_DIR/obsidian-jump-fixed.sh"

if [ \$? -ne 0 ]; then
    echo ""
    echo "================================"
    read -p "Press Enter to close..."
fi
EOF

chmod +x "$TEMP_SCRIPT"

osascript <<APPLESCRIPT
tell application "Terminal"
    activate
    do script "$TEMP_SCRIPT"
end tell
APPLESCRIPT
