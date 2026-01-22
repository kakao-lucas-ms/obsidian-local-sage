#!/bin/bash
#
# Obsidian Local Sage - Installation Script
#
# This script will:
# 1. Detect your Obsidian vault
# 2. Install required dependencies
# 3. Start Qdrant vector database (via Docker)
# 4. Pull Ollama BGE-M3 model
# 5. Create configuration file
# 6. Initialize database and build index
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Emoji support
CHECK="✅"
CROSS="❌"
WARN="⚠️"
INFO="ℹ️"
ROCKET="🚀"
SEARCH="🔍"
FOLDER="📁"
DATABASE="🗄️"
BRAIN="🧠"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${HOME}/.obsidian-local-sage"
CONFIG_DIR="${INSTALL_DIR}/config"
DB_DIR="${INSTALL_DIR}/db"
LOG_DIR="${INSTALL_DIR}/logs"

# Default values
OLLAMA_MODEL="bge-m3"
QDRANT_PORT=6333
QDRANT_CONTAINER="qdrant-obsidian"

#
# Helper Functions
#

print_header() {
    echo ""
    echo -e "${PURPLE}${BOLD}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}${BOLD}║              🧙 Obsidian Local Sage Installer              ║${NC}"
    echo -e "${PURPLE}${BOLD}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo ""
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}${BOLD}  $1${NC}"
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

log_info() {
    echo -e "${BLUE}${INFO}${NC}  $1"
}

log_success() {
    echo -e "${GREEN}${CHECK}${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}${WARN}${NC}  $1"
}

log_error() {
    echo -e "${RED}${CROSS}${NC} $1"
}

ask_yes_no() {
    local prompt="$1"
    local default="${2:-y}"

    if [[ "$default" == "y" ]]; then
        prompt="${prompt} [Y/n]: "
    else
        prompt="${prompt} [y/N]: "
    fi

    read -p "$(echo -e ${CYAN}$prompt${NC})" answer
    answer="${answer:-$default}"

    [[ "${answer,,}" == "y" || "${answer,,}" == "yes" ]]
}

check_command() {
    command -v "$1" &> /dev/null
}

#
# Dependency Checks
#

check_dependencies() {
    print_step "Step 1: Checking Dependencies"

    local missing=()

    # Check Python 3.8+
    if check_command python3; then
        local py_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        local py_major=$(echo "$py_version" | cut -d. -f1)
        local py_minor=$(echo "$py_version" | cut -d. -f2)

        if [[ "$py_major" -ge 3 && "$py_minor" -ge 8 ]]; then
            log_success "Python $py_version"
        else
            log_error "Python $py_version (need 3.8+)"
            missing+=("python3.8+")
        fi
    else
        log_error "Python 3 not found"
        missing+=("python3")
    fi

    # Check pip
    if check_command pip3; then
        log_success "pip3 $(pip3 --version | awk '{print $2}')"
    else
        log_error "pip3 not found"
        missing+=("pip3")
    fi

    # Check Docker
    if check_command docker; then
        if docker info &> /dev/null; then
            log_success "Docker $(docker --version | awk '{print $3}' | tr -d ',')"
        else
            log_warning "Docker installed but not running"
            missing+=("docker-running")
        fi
    else
        log_error "Docker not found"
        missing+=("docker")
    fi

    # Check Ollama
    if check_command ollama; then
        log_success "Ollama $(ollama --version 2>/dev/null | awk '{print $NF}' || echo 'installed')"
    else
        log_warning "Ollama not found (will try to install)"
    fi

    # Check fzf
    if check_command fzf; then
        log_success "fzf $(fzf --version | awk '{print $1}')"
    else
        log_warning "fzf not found (will install)"
    fi

    # Check sqlite3
    if check_command sqlite3; then
        log_success "sqlite3 $(sqlite3 --version | awk '{print $1}')"
    else
        log_error "sqlite3 not found"
        missing+=("sqlite3")
    fi

    # Check bat (optional, for preview)
    if check_command bat; then
        log_success "bat $(bat --version | head -1 | awk '{print $2}')"
    else
        log_info "bat not found (optional, for file previews)"
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo ""
        log_error "Missing required dependencies: ${missing[*]}"
        echo ""
        echo "Please install the missing dependencies and run this script again."
        echo ""
        echo "Installation hints:"
        echo "  - Python 3.8+: https://www.python.org/downloads/"
        echo "  - Docker: https://www.docker.com/get-started"
        echo "  - Ollama: https://ollama.ai/"
        echo "  - macOS: brew install python docker ollama fzf sqlite"
        exit 1
    fi

    echo ""
    log_success "All required dependencies found!"
}

#
# Install Optional Tools
#

install_optional_tools() {
    print_step "Step 2: Installing Optional Tools"

    # Install fzf if not present
    if ! check_command fzf; then
        log_info "Installing fzf..."
        if check_command brew; then
            brew install fzf
            log_success "fzf installed via Homebrew"
        else
            log_warning "Please install fzf manually: https://github.com/junegunn/fzf#installation"
        fi
    fi

    # Install bat if not present
    if ! check_command bat; then
        if ask_yes_no "Install bat for better file previews?" "y"; then
            if check_command brew; then
                brew install bat
                log_success "bat installed via Homebrew"
            else
                log_warning "Please install bat manually: https://github.com/sharkdp/bat#installation"
            fi
        fi
    fi
}

#
# Install Python Dependencies
#

install_python_deps() {
    print_step "Step 3: Installing Python Dependencies"

    log_info "Installing Python packages..."

    # Install from requirements.txt
    if [[ -f "${SCRIPT_DIR}/requirements.txt" ]]; then
        pip3 install -r "${SCRIPT_DIR}/requirements.txt" --quiet
        log_success "Core dependencies installed"
    else
        # Fallback to manual install
        pip3 install pyyaml requests rank-bm25 --quiet
        log_success "Core dependencies installed (fallback)"
    fi

    # Install package in development mode (optional)
    if [[ -f "${SCRIPT_DIR}/pyproject.toml" ]]; then
        if ask_yes_no "Install obsidian-local-sage as CLI tool?" "y"; then
            pip3 install -e "${SCRIPT_DIR}" --quiet
            log_success "CLI tools installed (sage-search, sage-jump, etc.)"
        fi
    fi
}

#
# Setup Qdrant
#

setup_qdrant() {
    print_step "Step 4: Setting Up Qdrant Vector Database"

    # Check if Qdrant is already running
    if curl -s "http://127.0.0.1:${QDRANT_PORT}/health" &> /dev/null; then
        log_success "Qdrant is already running on port ${QDRANT_PORT}"
        return 0
    fi

    # Check if container exists but stopped
    if docker ps -a --format '{{.Names}}' | grep -q "^${QDRANT_CONTAINER}$"; then
        log_info "Starting existing Qdrant container..."
        docker start "${QDRANT_CONTAINER}"
        sleep 3

        if curl -s "http://127.0.0.1:${QDRANT_PORT}/health" &> /dev/null; then
            log_success "Qdrant started successfully"
            return 0
        fi
    fi

    # Pull and run new container
    log_info "Pulling Qdrant Docker image..."
    docker pull qdrant/qdrant:latest

    log_info "Starting Qdrant container..."
    docker run -d \
        --name "${QDRANT_CONTAINER}" \
        -p ${QDRANT_PORT}:6333 \
        -v qdrant_obsidian_data:/qdrant/storage \
        --restart unless-stopped \
        qdrant/qdrant

    # Wait for Qdrant to start
    log_info "Waiting for Qdrant to start..."
    local retries=30
    while [[ $retries -gt 0 ]]; do
        if curl -s "http://127.0.0.1:${QDRANT_PORT}/health" &> /dev/null; then
            log_success "Qdrant is running on port ${QDRANT_PORT}"
            return 0
        fi
        sleep 1
        ((retries--))
    done

    log_error "Qdrant failed to start. Please check Docker logs:"
    echo "  docker logs ${QDRANT_CONTAINER}"
    exit 1
}

#
# Setup Ollama
#

setup_ollama() {
    print_step "Step 5: Setting Up Ollama"

    # Check if Ollama is installed
    if ! check_command ollama; then
        log_info "Ollama not found. Please install from https://ollama.ai/"
        if check_command brew; then
            if ask_yes_no "Install Ollama via Homebrew?" "y"; then
                brew install ollama
                log_success "Ollama installed"
            else
                log_warning "Skipping Ollama installation"
                return 0
            fi
        else
            log_warning "Please install Ollama manually from https://ollama.ai/"
            return 0
        fi
    fi

    # Check if Ollama is running
    if ! curl -s "http://127.0.0.1:11434/api/version" &> /dev/null; then
        log_info "Starting Ollama service..."
        # Try to start Ollama in the background
        ollama serve &> /dev/null &
        sleep 5

        if ! curl -s "http://127.0.0.1:11434/api/version" &> /dev/null; then
            log_warning "Ollama service not responding. Please start it manually: ollama serve"
        fi
    fi

    # Pull BGE-M3 model
    log_info "Checking for ${OLLAMA_MODEL} model..."
    if ollama list 2>/dev/null | grep -q "${OLLAMA_MODEL}"; then
        log_success "${OLLAMA_MODEL} model is available"
    else
        log_info "Pulling ${OLLAMA_MODEL} model (this may take a while)..."
        ollama pull "${OLLAMA_MODEL}"
        log_success "${OLLAMA_MODEL} model pulled successfully"
    fi
}

#
# Detect Obsidian Vault
#

detect_vault() {
    print_step "Step 6: Detecting Obsidian Vault"

    local vault_path=""
    local vault_name=""

    # Common Obsidian vault locations
    local search_paths=(
        "${HOME}/Documents"
        "${HOME}/Obsidian"
        "${HOME}/Desktop"
        "${HOME}/Library/Mobile Documents/iCloud~md~obsidian/Documents"
        "${HOME}/Dropbox"
        "${HOME}/OneDrive"
    )

    log_info "Searching for Obsidian vaults..."

    # Find directories with .obsidian folder
    local found_vaults=()
    for search_path in "${search_paths[@]}"; do
        if [[ -d "$search_path" ]]; then
            while IFS= read -r -d '' obsidian_dir; do
                local v_path=$(dirname "$obsidian_dir")
                found_vaults+=("$v_path")
            done < <(find "$search_path" -maxdepth 3 -type d -name ".obsidian" -print0 2>/dev/null)
        fi
    done

    if [[ ${#found_vaults[@]} -eq 0 ]]; then
        log_warning "No Obsidian vaults found automatically"
        read -p "$(echo -e ${CYAN}Enter your Obsidian vault path: ${NC})" vault_path
    elif [[ ${#found_vaults[@]} -eq 1 ]]; then
        vault_path="${found_vaults[0]}"
        log_success "Found vault: $vault_path"
        if ! ask_yes_no "Use this vault?" "y"; then
            read -p "$(echo -e ${CYAN}Enter your Obsidian vault path: ${NC})" vault_path
        fi
    else
        echo ""
        log_info "Found multiple vaults:"
        for i in "${!found_vaults[@]}"; do
            echo "  $((i+1)). ${found_vaults[i]}"
        done
        echo ""
        read -p "$(echo -e ${CYAN}Select vault number [1-${#found_vaults[@]}]: ${NC})" choice
        vault_path="${found_vaults[$((choice-1))]}"
    fi

    # Validate vault path
    if [[ ! -d "$vault_path" ]]; then
        log_error "Vault path does not exist: $vault_path"
        exit 1
    fi

    if [[ ! -d "$vault_path/.obsidian" ]]; then
        log_warning "No .obsidian folder found in: $vault_path"
        if ! ask_yes_no "Continue anyway?" "n"; then
            exit 1
        fi
    fi

    vault_name=$(basename "$vault_path")

    # Export for later use
    export VAULT_PATH="$vault_path"
    export VAULT_NAME="$vault_name"

    log_success "Using vault: $vault_name"
    log_info "Path: $vault_path"
}

#
# Create Configuration
#

create_config() {
    print_step "Step 7: Creating Configuration"

    # Create directories
    mkdir -p "${CONFIG_DIR}"
    mkdir -p "${DB_DIR}"
    mkdir -p "${LOG_DIR}"

    log_info "Creating configuration file..."

    local config_file="${CONFIG_DIR}/settings.yaml"

    # Generate config from template
    cat > "$config_file" << YAML
# Obsidian Local Sage Configuration
# Generated by install.sh on $(date)

# Obsidian Vault Configuration
vault:
  path: ${VAULT_PATH}
  name: ${VAULT_NAME}

# Project Paths
project:
  root: ${INSTALL_DIR}
  db_path: ${DB_DIR}/automation.db
  search_results_dir: 검색결과

# External Services
services:
  ollama:
    api_base: http://127.0.0.1:11434
    model: ${OLLAMA_MODEL}
    timeout: 120
    embedding_dim: 1024

  qdrant:
    host: 127.0.0.1
    port: ${QDRANT_PORT}
    collection: obsidian_docs
    timeout: 30
    top_k: 10
    score_threshold: 0.3

# Feature Settings
features:
  search:
    max_results: 8
    min_score: 0.3
    create_notes: true
    vector_weight: 0.7
    fts_weight: 0.3

  jump:
    enable_recent_tracking: true
    fzf_height: 60%
    fzf_preview_window: right:50%:wrap
    max_recent_items: 50

  health_check:
    old_document_days: 365
    large_document_kb: 100
    show_max_items: 20

  link_suggestions:
    max_suggestions: 8
    min_similarity: 0.4

# Advanced Settings
advanced:
  debug: false
  log_path: ${LOG_DIR}
  backup_before_batch: true
YAML

    log_success "Configuration created: $config_file"

    # Also copy example config to project
    cp "${SCRIPT_DIR}/config/settings.example.yaml" "${CONFIG_DIR}/settings.example.yaml" 2>/dev/null || true
}

#
# Initialize Database
#

init_database() {
    print_step "Step 8: Initializing Database"

    log_info "Creating SQLite database..."

    local db_file="${DB_DIR}/automation.db"

    # Create database schema
    sqlite3 "$db_file" << SQL
-- Document index for FTS search
CREATE TABLE IF NOT EXISTS document_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    title TEXT,
    category TEXT,
    aliases TEXT,
    tags TEXT,
    content TEXT,
    modified_at DATETIME,
    indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
    title,
    content,
    tags,
    aliases,
    content='document_index',
    content_rowid='id'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS document_ai AFTER INSERT ON document_index BEGIN
    INSERT INTO document_fts(rowid, title, content, tags, aliases)
    VALUES (new.id, new.title, new.content, new.tags, new.aliases);
END;

CREATE TRIGGER IF NOT EXISTS document_ad AFTER DELETE ON document_index BEGIN
    INSERT INTO document_fts(document_fts, rowid, title, content, tags, aliases)
    VALUES ('delete', old.id, old.title, old.content, old.tags, old.aliases);
END;

CREATE TRIGGER IF NOT EXISTS document_au AFTER UPDATE ON document_index BEGIN
    INSERT INTO document_fts(document_fts, rowid, title, content, tags, aliases)
    VALUES ('delete', old.id, old.title, old.content, old.tags, old.aliases);
    INSERT INTO document_fts(rowid, title, content, tags, aliases)
    VALUES (new.id, new.title, new.content, new.tags, new.aliases);
END;

-- Recent documents tracking
CREATE TABLE IF NOT EXISTS recent_documents (
    file_path TEXT PRIMARY KEY,
    title TEXT,
    accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 1
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_document_modified ON document_index(modified_at);
CREATE INDEX IF NOT EXISTS idx_document_category ON document_index(category);
SQL

    log_success "Database created: $db_file"
}

#
# Build Index
#

build_index() {
    print_step "Step 9: Building Search Index"

    if ask_yes_no "Build search index now? (This may take a while for large vaults)" "y"; then
        log_info "Building document index..."

        # Check if ingest script exists
        if [[ -f "${SCRIPT_DIR}/src/core/ingest-direct.py" ]]; then
            python3 "${SCRIPT_DIR}/src/core/ingest-direct.py" --full
            log_success "Search index built successfully"
        else
            log_warning "Ingest script not found. Run manually:"
            echo "  python3 ${SCRIPT_DIR}/src/core/ingest-direct.py --full"
        fi
    else
        log_info "Skipping index build. Run later with:"
        echo "  python3 ${SCRIPT_DIR}/src/core/ingest-direct.py --full"
    fi
}

#
# Make Scripts Executable
#

setup_permissions() {
    print_step "Step 10: Setting Up Permissions"

    log_info "Making scripts executable..."

    # Find all .sh files and make them executable
    find "${SCRIPT_DIR}/src" -name "*.sh" -type f -exec chmod +x {} \;

    log_success "All shell scripts are now executable"
}

#
# Print Summary
#

print_summary() {
    echo ""
    echo -e "${GREEN}${BOLD}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║              🎉 Installation Complete!                     ║${NC}"
    echo -e "${GREEN}${BOLD}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BOLD}Configuration:${NC}"
    echo "  Vault:     ${VAULT_PATH}"
    echo "  Config:    ${CONFIG_DIR}/settings.yaml"
    echo "  Database:  ${DB_DIR}/automation.db"
    echo "  Logs:      ${LOG_DIR}"
    echo ""
    echo -e "${BOLD}Services:${NC}"
    echo "  Qdrant:    http://127.0.0.1:${QDRANT_PORT}"
    echo "  Ollama:    http://127.0.0.1:11434 (model: ${OLLAMA_MODEL})"
    echo ""
    echo -e "${BOLD}Next Steps:${NC}"
    echo ""
    echo "  1. ${SEARCH} Test AI Search:"
    echo "     python3 ${SCRIPT_DIR}/src/search/obsidian-wrapper-search-v4.py \"test query\""
    echo ""
    echo "  2. ${FOLDER} Test Document Jump:"
    echo "     bash ${SCRIPT_DIR}/src/jump/obsidian-jump-fixed.sh"
    echo ""
    echo "  3. Configure Obsidian Shell Commands plugin:"
    echo "     - Install: https://github.com/Taitava/obsidian-shellcommands"
    echo "     - Import: ${SCRIPT_DIR}/obsidian-config/shell-commands.json"
    echo ""
    echo -e "${BOLD}CLI Commands (if installed):${NC}"
    echo "  sage-search \"query\"    - AI semantic search"
    echo "  sage-jump              - Interactive document jump"
    echo "  sage-ingest --full     - Rebuild search index"
    echo "  sage-health            - Vault health check"
    echo ""
    echo -e "${CYAN}For more information, see: ${SCRIPT_DIR}/README.md${NC}"
    echo ""
}

#
# Main Installation Flow
#

main() {
    print_header

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --vault)
                VAULT_PATH="$2"
                VAULT_NAME=$(basename "$VAULT_PATH")
                shift 2
                ;;
            --skip-docker)
                SKIP_DOCKER=true
                shift
                ;;
            --skip-ollama)
                SKIP_OLLAMA=true
                shift
                ;;
            --help|-h)
                echo "Usage: ./install.sh [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --vault PATH     Specify vault path (skip detection)"
                echo "  --skip-docker    Skip Qdrant Docker setup"
                echo "  --skip-ollama    Skip Ollama setup"
                echo "  --help           Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Run installation steps
    check_dependencies
    install_optional_tools
    install_python_deps

    if [[ "${SKIP_DOCKER}" != "true" ]]; then
        setup_qdrant
    fi

    if [[ "${SKIP_OLLAMA}" != "true" ]]; then
        setup_ollama
    fi

    if [[ -z "${VAULT_PATH}" ]]; then
        detect_vault
    else
        export VAULT_PATH
        export VAULT_NAME
    fi

    create_config
    init_database
    build_index
    setup_permissions
    print_summary
}

# Run main function
main "$@"
