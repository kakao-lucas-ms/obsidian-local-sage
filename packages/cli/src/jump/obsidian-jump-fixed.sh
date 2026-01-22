#!/bin/bash
# obsidian-jump-fixed.sh - Fixed delimiter issue
# Usage: ./obsidian-jump-fixed.sh [search query]

set -euo pipefail

# Script and project directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Load configuration from Python config system
load_config() {
    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from src.core.config import config
print(config.db_path)
print(config.vault_path)
print(config.vault_name)
" 2>/dev/null
}

# Read config values
CONFIG_OUTPUT=$(load_config)
if [[ -n "$CONFIG_OUTPUT" ]]; then
    DB_PATH=$(echo "$CONFIG_OUTPUT" | sed -n '1p')
    VAULT_PATH=$(echo "$CONFIG_OUTPUT" | sed -n '2p')
    VAULT_NAME=$(echo "$CONFIG_OUTPUT" | sed -n '3p')
else
    # Fallback to defaults
    DB_PATH="${HOME}/.obsidian-local-sage/db/automation.db"
    VAULT_PATH="${HOME}/Documents/Obsidian"
    VAULT_NAME="Obsidian"
fi

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

error_exit() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

check_dependencies() {
    if ! command -v fzf &> /dev/null; then
        error_exit "fzf is not installed. Install with: brew install fzf"
    fi

    if ! command -v sqlite3 &> /dev/null; then
        error_exit "sqlite3 is not installed"
    fi

    if [[ ! -f "$DB_PATH" ]]; then
        error_exit "Database not found at: $DB_PATH"
    fi
}

track_recent_access() {
    local file_path="$1"
    local title="$2"

    local safe_path="${file_path//\'/\'\'}"
    local safe_title="${title//\'/\'\'}"

    sqlite3 "$DB_PATH" <<SQL
        INSERT INTO recent_documents (file_path, title, accessed_at, access_count)
        VALUES ('$safe_path', '$safe_title', CURRENT_TIMESTAMP, 1)
        ON CONFLICT(file_path) DO UPDATE SET
            accessed_at = CURRENT_TIMESTAMP,
            access_count = access_count + 1;
SQL
}

search_documents() {
    local query="$1"

    if [[ -n "$query" ]]; then
        local safe_query="${query//\'/\'\'}"

        sqlite3 -separator $'\t' "$DB_PATH" <<SQL
            SELECT
                d.title,
                d.file_name,
                d.file_path,
                d.category,
                d.aliases,
                d.modified_at
            FROM document_index d
            JOIN document_fts fts ON fts.rowid = d.id
            WHERE document_fts MATCH '$safe_query*'
            ORDER BY rank;
SQL
    else
        sqlite3 -separator $'\t' "$DB_PATH" <<SQL
            SELECT
                title,
                file_name,
                file_path,
                category,
                aliases,
                modified_at
            FROM document_index
            ORDER BY modified_at DESC;
SQL
    fi
}

format_for_fzf() {
    # Use TAB as hidden delimiter instead of |
    while IFS=$'\t' read -r title file_name file_path category aliases modified_at; do
        local display="$title"

        if [[ "$title" != "$file_name" ]]; then
            display="$display | $file_name"
        fi

        if [[ -n "$category" ]]; then
            display="$display | [$category]"
        fi

        if [[ -n "$aliases" ]]; then
            display="$display | 別名: $aliases"
        fi

        # Use TAB to separate display from hidden data
        echo -e "$display\t$file_path\t$title"
    done
}

open_in_obsidian() {
    local file_path="$1"
    local title="$2"

    local encoded_path=$(python3 "${SCRIPT_DIR}/obsidian-uri-encode.py" "$file_path")

    if [[ -z "$encoded_path" ]]; then
        error_exit "Failed to encode file path"
    fi

    track_recent_access "$file_path" "$title"

    # URL encode vault name
    local vault_encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$VAULT_NAME'))")

    echo -e "${GREEN}Opening:${NC} $title"
    open "obsidian://open?vault=${vault_encoded}&file=${encoded_path}"
}

main() {
    check_dependencies

    local search_query="${1:-}"

    echo -e "${BLUE}🔍 Obsidian Document Jump${NC}"
    echo ""

    local results
    results=$(search_documents "$search_query")

    if [[ -z "$results" ]]; then
        if [[ -n "$search_query" ]]; then
            echo -e "${YELLOW}No documents found matching: $search_query${NC}"
        else
            echo -e "${YELLOW}No documents in index. Run ingest-direct.py first.${NC}"
        fi
        exit 0
    fi

    local formatted
    formatted=$(echo "$results" | format_for_fzf)

    local selected
    selected=$(echo "$formatted" | fzf \
        --height=60% \
        --layout=reverse \
        --border \
        --prompt="📄 Jump to document > " \
        --header="Enter: Open | Esc: Cancel | Ctrl-C: Quit" \
        --preview='
            # Extract file_path (field 2, TAB separated)
            path=$(echo {} | cut -f2)
            if [[ -f "$path" ]]; then
                head -n 50 "$path" | bat --style=numbers --color=always --language=markdown 2>/dev/null || cat
            else
                echo "File not found: $path"
            fi
        ' \
        --preview-window=right:50%:wrap \
        --delimiter=$'\t' \
        --with-nth=1)

    if [[ -z "$selected" ]]; then
        echo "Cancelled."
        exit 0
    fi

    # Debug log
    DEBUG_LOG="/tmp/obsidian-jump-debug.log"
    echo "=== Debug $(date) ===" >> "$DEBUG_LOG"
    echo "Selected line:" >> "$DEBUG_LOG"
    echo "$selected" >> "$DEBUG_LOG"
    echo "" >> "$DEBUG_LOG"
    echo "Selected line (hex):" >> "$DEBUG_LOG"
    echo "$selected" | hexdump -C >> "$DEBUG_LOG"
    echo "" >> "$DEBUG_LOG"

    # Extract file path and title (TAB separated)
    # Field 1: display, Field 2: file_path, Field 3: title
    local file_path=$(echo "$selected" | cut -f2)
    local title=$(echo "$selected" | cut -f3)

    echo "Extracted file_path (raw): '$file_path'" >> "$DEBUG_LOG"
    echo "Extracted title (raw): '$title'" >> "$DEBUG_LOG"

    # Trim whitespace
    file_path=$(echo "$file_path" | xargs)
    title=$(echo "$title" | xargs)

    echo "After trim file_path: '$file_path'" >> "$DEBUG_LOG"
    echo "After trim title: '$title'" >> "$DEBUG_LOG"
    echo "File exists: $([ -f "$file_path" ] && echo 'YES' || echo 'NO')" >> "$DEBUG_LOG"
    echo "" >> "$DEBUG_LOG"

    # Check if file exists
    if [[ ! -f "$file_path" ]]; then
        echo -e "${RED}파일을 찾지 못했습니다${NC}"
        echo "디버그 로그를 확인하세요: $DEBUG_LOG"
        echo ""
        cat "$DEBUG_LOG"
        echo ""
        read -p "Press Enter to continue..."
        exit 1
    fi

    open_in_obsidian "$file_path" "$title"
}

main "$@"
