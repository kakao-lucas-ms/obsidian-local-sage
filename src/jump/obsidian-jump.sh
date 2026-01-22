#!/bin/bash
# obsidian-jump.sh - Fuzzy jump to Obsidian document by title
# Usage: ./obsidian-jump.sh [search query]

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

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Error handling
error_exit() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

# Check dependencies
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

# Update recent documents tracking
track_recent_access() {
    local file_path="$1"
    local title="$2"

    # Use printf to safely escape single quotes
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

# Search documents with optional query
search_documents() {
    local query="$1"

    if [[ -n "$query" ]]; then
        # Escape single quotes for FTS search
        local safe_query="${query//\'/\'\'}"

        # FTS search with ranking
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
            ORDER BY rank
            LIMIT 100;
SQL
    else
        # List all documents, most recently modified first
        sqlite3 -separator $'\t' "$DB_PATH" <<SQL
            SELECT
                title,
                file_name,
                file_path,
                category,
                aliases,
                modified_at
            FROM document_index
            ORDER BY modified_at DESC
            LIMIT 100;
SQL
    fi
}

# Format document for fzf display
format_for_fzf() {
    while IFS=$'\t' read -r title file_name file_path category aliases modified_at; do
        # Format: "Title | filename.md | category | aliases"
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

        # Store file path in hidden field (after tab)
        echo "$display|$file_path|$title"
    done
}

# Open document in Obsidian
open_in_obsidian() {
    local file_path="$1"
    local title="$2"

    # Encode file path for URI
    local encoded_path=$(python3 "${SCRIPT_DIR}/obsidian-uri-encode.py" "$file_path")

    if [[ -z "$encoded_path" ]]; then
        error_exit "Failed to encode file path"
    fi

    # Track recent access
    track_recent_access "$file_path" "$title"

    # URL encode vault name
    local vault_encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$VAULT_NAME'))")

    # Open in Obsidian
    echo -e "${GREEN}Opening:${NC} $title"
    open "obsidian://open?vault=${vault_encoded}&file=${encoded_path}"
}

# Main function
main() {
    check_dependencies

    local search_query="${1:-}"

    echo -e "${BLUE}🔍 Obsidian Document Jump${NC}"
    echo ""

    # Search documents
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

    # Format and display with fzf
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
            path=$(echo {} | cut -d"|" -f2)
            if [[ -f "$path" ]]; then
                head -n 50 "$path" | bat --style=numbers --color=always --language=markdown 2>/dev/null || cat
            else
                echo "File not found: $path"
            fi
        ' \
        --preview-window=right:50%:wrap \
        --delimiter="|" \
        --with-nth=1)

    if [[ -z "$selected" ]]; then
        echo "Cancelled."
        exit 0
    fi

    # Extract file path and title
    local file_path=$(echo "$selected" | cut -d"|" -f2)
    local title=$(echo "$selected" | cut -d"|" -f3)

    # Verify file exists
    if [[ ! -f "$file_path" ]]; then
        error_exit "File not found: $file_path"
    fi

    # Open in Obsidian
    open_in_obsidian "$file_path" "$title"
}

# Run main function
main "$@"
