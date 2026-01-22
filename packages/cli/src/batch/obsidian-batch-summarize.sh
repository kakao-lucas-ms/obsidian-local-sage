#!/bin/bash

# Obsidian Batch Document Summarization Script
# Usage: ./obsidian-batch-summarize.sh <folder_path> [options]

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
WEBHOOK_URL="${N8N_WEBHOOK_URL:-http://localhost:5678}/webhook/obe-batch-summarize"
FILE_PATTERN="*.md"
MAX_FILES=100
VERBOSE=0
OUTPUT_FORMAT="pretty"

# Function to display usage
usage() {
    cat << EOF
Usage: $0 <folder_path> [options]

Batch summarize all markdown files in a folder with AI-powered summarization.

Arguments:
    folder_path         Path to the folder containing markdown files

Options:
    -p, --pattern       File pattern (default: *.md)
    -m, --max           Maximum number of files (default: 100)
    -v, --verbose       Verbose output
    -j, --json          Output in JSON format
    -h, --help          Show this help message

Examples:
    # Summarize all markdown files in a folder
    $0 ~/Documents/Obsidian/Notes/Projects

    # Custom file pattern
    $0 ~/Documents/Obsidian/Notes -p "meeting-*.md"

    # Limit to 50 files
    $0 ~/Documents/Obsidian/Notes -m 50

    # Verbose JSON output
    $0 ~/Documents/Obsidian/Notes -v -j

Environment Variables:
    N8N_WEBHOOK_URL     Base URL for n8n webhooks (default: http://localhost:5678)

EOF
    exit 1
}

# Parse arguments
FOLDER_PATH=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--pattern)
            FILE_PATTERN="$2"
            shift 2
            ;;
        -m|--max)
            MAX_FILES="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -j|--json)
            OUTPUT_FORMAT="json"
            shift
            ;;
        -h|--help)
            usage
            ;;
        -*)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            ;;
        *)
            if [[ -z "$FOLDER_PATH" ]]; then
                FOLDER_PATH="$1"
            else
                echo -e "${RED}Error: Multiple folder paths provided${NC}"
                usage
            fi
            shift
            ;;
    esac
done

# Validate folder path
if [[ -z "$FOLDER_PATH" ]]; then
    echo -e "${RED}Error: Folder path is required${NC}"
    usage
fi

if [[ ! -d "$FOLDER_PATH" ]]; then
    echo -e "${RED}Error: Folder not found: $FOLDER_PATH${NC}"
    exit 1
fi

# Get absolute path
FOLDER_PATH=$(cd "$FOLDER_PATH" && pwd)

# Verbose output
if [[ $VERBOSE -eq 1 ]]; then
    echo -e "${BLUE}📁 Folder: $FOLDER_PATH${NC}"
    echo -e "${BLUE}🔍 Pattern: $FILE_PATTERN${NC}"
    echo -e "${BLUE}📊 Max Files: $MAX_FILES${NC}"
    echo -e "${BLUE}🔗 Webhook: $WEBHOOK_URL${NC}"
    echo ""
fi

# Count files first
FILE_COUNT=$(find "$FOLDER_PATH" -type f -name "$FILE_PATTERN" | wc -l | tr -d ' ')

if [[ $FILE_COUNT -eq 0 ]]; then
    echo -e "${YELLOW}⚠️  No files matching pattern '$FILE_PATTERN' found in $FOLDER_PATH${NC}"
    exit 0
fi

echo -e "${YELLOW}📁 Found $FILE_COUNT file(s) matching pattern '$FILE_PATTERN'${NC}"

if [[ $FILE_COUNT -gt $MAX_FILES ]]; then
    echo -e "${YELLOW}⚠️  Only the first $MAX_FILES files will be processed${NC}"
fi

echo -e "${YELLOW}🔄 Starting batch summarization...${NC}"
echo ""

# Call n8n webhook
RESPONSE=$(curl -s -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d "{\"folder_path\": \"$FOLDER_PATH\", \"file_pattern\": \"$FILE_PATTERN\", \"max_files\": $MAX_FILES}")

# Check if response is valid JSON
if ! echo "$RESPONSE" | jq empty 2>/dev/null; then
    echo -e "${RED}❌ Error: Invalid response from webhook${NC}"
    echo "$RESPONSE"
    exit 1
fi

# Check for error in response
STATUS=$(echo "$RESPONSE" | jq -r '.status // "unknown"')

if [[ "$STATUS" == "error" ]]; then
    echo -e "${RED}❌ Error: $(echo "$RESPONSE" | jq -r '.message // "Unknown error"')${NC}"
    exit 1
fi

# Output results
if [[ "$OUTPUT_FORMAT" == "json" ]]; then
    echo "$RESPONSE" | jq '.'
else
    JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id // 0')
    TOTAL=$(echo "$RESPONSE" | jq -r '.total // 0')
    PROCESSED=$(echo "$RESPONSE" | jq -r '.processed // 0')
    FAILED=$(echo "$RESPONSE" | jq -r '.failed // 0')

    echo -e "${GREEN}✅ Batch summarization complete!${NC}"
    echo ""
    echo -e "${BLUE}📊 Job Statistics${NC}"
    echo -e "   Job ID: ${GREEN}$JOB_ID${NC}"
    echo -e "   Total Files: ${GREEN}$TOTAL${NC}"
    echo -e "   Processed: ${GREEN}$PROCESSED${NC}"
    echo -e "   Failed: ${RED}$FAILED${NC}"
    echo -e "   Status: ${GREEN}$STATUS${NC}"
    echo ""

    SUCCESS_RATE=$(echo "scale=1; ($PROCESSED / $TOTAL) * 100" | bc 2>/dev/null || echo "0")
    echo -e "${BLUE}📈 Success Rate: ${GREEN}${SUCCESS_RATE}%${NC}"
    echo ""

    if [[ $VERBOSE -eq 1 ]]; then
        echo -e "${GREEN}✓ All summaries saved to database${NC}"
        echo -e "${BLUE}💡 Use the following command to query summaries:${NC}"
        echo -e "   sqlite3 ~/workspace/kakao-github/claude-help-me/db/automation.db \"SELECT * FROM document_summaries WHERE file_path LIKE '$FOLDER_PATH%'\""
    fi
fi
