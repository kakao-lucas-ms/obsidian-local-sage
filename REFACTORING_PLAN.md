# Obsidian Local Sage - Refactoring Plan

## Project Overview

**New Project Name:** obsidian-local-sage

**Purpose:** Transform the current Obsidian AI integration from a personal tool into a shareable, installable package that others can use with their own vaults.

---

## Current State Analysis

### ✅ What Works Well

1. **Core Features (All Tested & Working)**
   - AI-powered semantic search with clickable wikilink results
   - Document jump with fzf (1755+ documents, no limit)
   - Link suggestions using BGE-M3 embeddings
   - Document comparison with similarity analysis
   - Batch processing (MOC, tag management, link checking)
   - Vault health check (8 different issue types)
   - TIL auto-generation from daily notes
   - Smart templates with context awareness
   - Graph analysis and visualization
   - Voice note integration
   - AI chat interface

2. **Technical Architecture**
   - Bash wrapper pattern (solves Shell Commands escaping)
   - Ollama + BGE-M3 for local embeddings (no API costs)
   - Qdrant for vector search (5,534 indexed chunks)
   - SQLite FTS5 for full-text search
   - TAB-delimited output (reliable field separation)
   - Vault-relative paths (proper Obsidian URI encoding)

3. **Integration Method**
   - Obsidian Shell Commands plugin configuration
   - Modal/notification/ignore output handlers
   - Command Palette integration

### ❌ Critical Issues for Shareability

#### 1. Hardcoded Paths (60+ files)

**Files with hardcoded paths:**
```
scripts/obsidian-*.py (25+ files)
scripts/obsidian-*.sh (15+ files)
scripts/test-*.sh (8+ files)
scripts/fix-*.sh (5+ files)
scripts/ingest-*.py (3+ files)
db/schema.sql (1 file)
.obsidian/plugins/shellcommands/data.json (1 file)
```

**Hardcoded values:**
- `VAULT_PATH = "/Users/kakao/workspace/my-note/나의노트"`
- `DB_PATH = "/Users/kakao/workspace/kakao-github/claude-help-me/db/automation.db"`
- `PROJECT_ROOT = "/Users/kakao/workspace/kakao-github/claude-help-me"`
- `QDRANT_HOST = "127.0.0.1"`
- `OLLAMA_API_BASE = "http://127.0.0.1:11434"`

#### 2. No Installation Process

**Current barriers:**
- No automatic setup script
- Manual path editing in 60+ files
- No dependency installation guide
- No service detection (Ollama/Qdrant running?)
- No vault path detection

#### 3. No Configuration System

**Missing:**
- Central config file (YAML/JSON)
- Environment variable support
- User-specific settings
- Service connection validation

#### 4. Documentation Gaps

**Incomplete:**
- Installation instructions assume expert user
- No troubleshooting guide for common issues
- No architecture documentation for contributors
- No comparison with existing solutions

---

## Proposed Solution

### Phase 1: Project Structure Refactoring

**New directory structure:**
```
obsidian-local-sage/
├── README.md                    # User-facing documentation
├── INSTALL.md                   # Step-by-step installation
├── ARCHITECTURE.md              # Technical documentation
├── CONTRIBUTING.md              # For contributors
├── LICENSE                      # Open source license
│
├── install.sh                   # Automatic installation script
├── config/
│   ├── settings.yaml            # User configuration
│   ├── settings.example.yaml    # Template
│   └── validator.py             # Config validation
│
├── src/
│   ├── core/
│   │   ├── config.py           # Config loader
│   │   ├── paths.py            # Path resolution
│   │   └── services.py         # Service connection
│   │
│   ├── search/
│   │   ├── semantic.py         # Vector search
│   │   ├── full_text.py        # SQLite FTS
│   │   ├── hybrid.py           # Combined search
│   │   └── wrappers/           # Bash wrappers
│   │
│   ├── jump/
│   │   ├── document_jump.py
│   │   ├── uri_encode.py
│   │   └── wrappers/
│   │
│   ├── batch/
│   │   ├── moc_generator.py
│   │   ├── tag_manager.py
│   │   ├── link_checker.py
│   │   └── wrappers/
│   │
│   ├── health/
│   │   ├── vault_check.py
│   │   ├── scanners.py
│   │   └── wrappers/
│   │
│   ├── analysis/
│   │   ├── compare.py
│   │   ├── suggest_links.py
│   │   ├── graph.py
│   │   └── wrappers/
│   │
│   ├── automation/
│   │   ├── til_generator.py
│   │   ├── templates.py
│   │   └── wrappers/
│   │
│   └── chat/
│       ├── interface.py
│       ├── voice.py
│       └── wrappers/
│
├── db/
│   ├── schema.sql
│   ├── migrations/
│   └── init.py
│
├── obsidian-config/
│   ├── shell-commands.json     # Template for Shell Commands
│   └── hotkeys.json            # Recommended hotkeys
│
├── tests/
│   ├── test_config.py
│   ├── test_search.py
│   └── test_integration.py
│
└── docs/
    ├── FEATURES.md             # Feature documentation
    ├── TROUBLESHOOTING.md
    ├── COMPARISON.md           # vs Smart Connections, etc.
    └── ROADMAP.md
```

### Phase 2: Configuration System

**`config/settings.yaml`:**
```yaml
# Obsidian Vault Configuration
vault:
  path: ~/Documents/MyVault  # Will be auto-detected or prompted
  name: MyVault              # Auto-detected from path

# Project Paths
project:
  root: ~/.obsidian-local-sage  # Installation directory
  db_path: ~/.obsidian-local-sage/db/automation.db
  search_results_dir: 검색결과   # Relative to vault

# Services
services:
  ollama:
    api_base: http://127.0.0.1:11434
    model: bge-m3
    timeout: 120

  qdrant:
    host: 127.0.0.1
    port: 6333
    collection: obsidian_docs
    timeout: 30

# Feature Settings
features:
  search:
    max_results: 8
    min_score: 0.3
    create_notes: true

  jump:
    enable_recent_tracking: true
    fzf_height: 60%

  health_check:
    old_document_days: 365
    large_document_kb: 100
    show_max_items: 20

  batch:
    recursive_default: false
    moc_group_by: folder  # folder | tag | date

# Advanced
advanced:
  debug: false
  log_path: ~/.obsidian-local-sage/logs
  backup_before_batch: true
```

**`src/core/config.py`:**
```python
import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    """Central configuration manager"""

    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, config_path: str = None):
        """Load configuration from YAML"""
        if config_path is None:
            # Try standard locations
            locations = [
                Path.home() / ".obsidian-local-sage" / "config" / "settings.yaml",
                Path(__file__).parent.parent.parent / "config" / "settings.yaml"
            ]
            for loc in locations:
                if loc.exists():
                    config_path = str(loc)
                    break

        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        else:
            raise FileNotFoundError("Config file not found. Run install.sh first.")

    def get(self, key: str, default=None):
        """Get config value using dot notation"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    @property
    def vault_path(self) -> Path:
        return Path(self.get('vault.path')).expanduser()

    @property
    def db_path(self) -> Path:
        return Path(self.get('project.db_path')).expanduser()

    @property
    def project_root(self) -> Path:
        return Path(self.get('project.root')).expanduser()

# Global config instance
config = Config()
```

### Phase 3: Installation Automation

**`install.sh`:**
```bash
#!/bin/bash
# Obsidian Local Sage Installer
# Automatically detects vault, installs dependencies, sets up configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.obsidian-local-sage"
CONFIG_FILE="$INSTALL_DIR/config/settings.yaml"

echo "🚀 Obsidian Local Sage Installer"
echo "=================================="
echo ""

# 1. Detect Obsidian Vault
detect_vault() {
    echo "🔍 Detecting Obsidian vault..."

    # Common locations
    VAULTS=(
        "$HOME/Documents/Obsidian"
        "$HOME/Obsidian"
        "$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"
    )

    for vault in "${VAULTS[@]}"; do
        if [[ -d "$vault/.obsidian" ]]; then
            echo "✅ Found vault: $vault"
            VAULT_PATH="$vault"
            return 0
        fi
    done

    # Manual input
    echo "❌ Could not auto-detect vault."
    read -p "Enter your Obsidian vault path: " VAULT_PATH

    if [[ ! -d "$VAULT_PATH/.obsidian" ]]; then
        echo "❌ Invalid vault path. Must contain .obsidian directory."
        exit 1
    fi
}

# 2. Check Dependencies
check_dependencies() {
    echo ""
    echo "🔧 Checking dependencies..."

    # Python 3
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 not found. Install: brew install python3"
        exit 1
    fi

    # fzf
    if ! command -v fzf &> /dev/null; then
        echo "⚠️  fzf not found. Installing..."
        brew install fzf || {
            echo "❌ Failed to install fzf"
            exit 1
        }
    fi

    # Ollama
    if ! command -v ollama &> /dev/null; then
        echo "⚠️  Ollama not found."
        read -p "Install Ollama? (y/n): " install_ollama
        if [[ "$install_ollama" == "y" ]]; then
            brew install ollama
            ollama pull bge-m3
        fi
    else
        # Check if BGE-M3 model exists
        if ! ollama list | grep -q "bge-m3"; then
            echo "📦 Pulling BGE-M3 model..."
            ollama pull bge-m3
        fi
    fi

    # Qdrant (optional)
    if ! command -v docker &> /dev/null; then
        echo "⚠️  Docker not found. Qdrant requires Docker."
        echo "   Install: https://www.docker.com/products/docker-desktop"
    else
        # Check if Qdrant is running
        if ! curl -s http://127.0.0.1:6333 &> /dev/null; then
            echo "⚠️  Qdrant not running. Starting..."
            docker run -d -p 6333:6333 -v qdrant_data:/qdrant/storage qdrant/qdrant
        fi
    fi

    # Python packages
    echo "📦 Installing Python dependencies..."
    pip3 install -q qdrant-client requests pyyaml
}

# 3. Copy Files
install_files() {
    echo ""
    echo "📁 Installing files..."

    mkdir -p "$INSTALL_DIR"
    cp -r "$SCRIPT_DIR/"* "$INSTALL_DIR/"

    # Create config directory
    mkdir -p "$INSTALL_DIR/config"
    mkdir -p "$INSTALL_DIR/db"
    mkdir -p "$INSTALL_DIR/logs"
}

# 4. Generate Configuration
generate_config() {
    echo ""
    echo "⚙️  Generating configuration..."

    cat > "$CONFIG_FILE" <<EOF
# Obsidian Local Sage Configuration
# Generated: $(date)

vault:
  path: $VAULT_PATH
  name: $(basename "$VAULT_PATH")

project:
  root: $INSTALL_DIR
  db_path: $INSTALL_DIR/db/automation.db
  search_results_dir: 검색결과

services:
  ollama:
    api_base: http://127.0.0.1:11434
    model: bge-m3
    timeout: 120

  qdrant:
    host: 127.0.0.1
    port: 6333
    collection: obsidian_docs
    timeout: 30

features:
  search:
    max_results: 8
    min_score: 0.3
    create_notes: true

  jump:
    enable_recent_tracking: true
    fzf_height: 60%

  health_check:
    old_document_days: 365
    large_document_kb: 100
    show_max_items: 20

  batch:
    recursive_default: false
    moc_group_by: folder

advanced:
  debug: false
  log_path: $INSTALL_DIR/logs
  backup_before_batch: true
EOF
}

# 5. Initialize Database
init_database() {
    echo ""
    echo "🗄️  Initializing database..."

    python3 "$INSTALL_DIR/db/init.py"
}

# 6. Build Initial Index
build_index() {
    echo ""
    echo "📊 Building document index..."

    python3 "$INSTALL_DIR/src/core/ingest.py" --full
}

# 7. Configure Obsidian
configure_obsidian() {
    echo ""
    echo "🔧 Obsidian configuration..."
    echo ""
    echo "📝 Next steps:"
    echo "1. Install Shell Commands plugin in Obsidian"
    echo "2. Import shell commands from: $INSTALL_DIR/obsidian-config/shell-commands.json"
    echo "3. Restart Obsidian"
    echo "4. Test with Command Palette: 🔍 AI 검색"
    echo ""
    echo "📚 Documentation: $INSTALL_DIR/README.md"
}

# Main Installation Flow
main() {
    detect_vault
    check_dependencies
    install_files
    generate_config
    init_database
    build_index
    configure_obsidian

    echo ""
    echo "✅ Installation complete!"
    echo ""
    echo "Config file: $CONFIG_FILE"
    echo "Installation directory: $INSTALL_DIR"
}

main
```

### Phase 4: Code Refactoring

**Example refactored search script:**

**Before (hardcoded):**
```python
VAULT_PATH = "/Users/kakao/workspace/my-note/나의노트"
DB_PATH = "/Users/kakao/workspace/kakao-github/claude-help-me/db/automation.db"
QDRANT_HOST = "127.0.0.1"
```

**After (config-based):**
```python
from src.core.config import config

# Load configuration
config.load()

# Use config values
VAULT_PATH = config.vault_path
DB_PATH = config.db_path
QDRANT_HOST = config.get('services.qdrant.host')
QDRANT_PORT = config.get('services.qdrant.port')
```

---

## Comparison with Existing Solutions

### Our Advantages

| Feature | obsidian-local-sage | Smart Connections | Vector Search |
|---------|---------------------|-------------------|---------------|
| **Local AI (No API costs)** | ✅ Ollama + BGE-M3 | ❌ Requires OpenAI | ❌ Cloud-based |
| **Hybrid Search** | ✅ Vector + FTS | ⚠️ Vector only | ⚠️ Vector only |
| **Document Jump (fzf)** | ✅ 1755+ docs | ❌ N/A | ❌ N/A |
| **Batch Operations** | ✅ MOC, tags, links | ❌ N/A | ❌ N/A |
| **Vault Health Check** | ✅ 8 issue types | ❌ N/A | ❌ N/A |
| **Document Comparison** | ✅ Semantic + Text | ❌ N/A | ❌ N/A |
| **CLI + Obsidian** | ✅ Both | ⚠️ Obsidian only | ⚠️ Obsidian only |
| **Installation** | ❌ Complex (will fix) | ✅ Plugin install | ✅ Plugin install |

### Our Disadvantages (Current)

1. **Installation Complexity**: Requires multiple services (Ollama, Qdrant, SQLite)
2. **Manual Configuration**: 60+ files with hardcoded paths
3. **No Plugin**: Must use Shell Commands plugin
4. **Technical Barrier**: Requires CLI comfort

### After Refactoring

- ✅ One-command installation: `./install.sh`
- ✅ Auto-detection of vault and services
- ✅ Config-based, no hardcoded paths
- ✅ Clear documentation
- ⚠️ Still requires CLI for some features (by design - more powerful)

---

## Roadmap

### Phase 1: Foundation (Week 1)
- [x] Document current state
- [ ] Create new project structure
- [ ] Implement config system
- [ ] Refactor core 10 scripts
- [ ] Create install.sh (basic)

### Phase 2: Migration (Week 2)
- [ ] Refactor all 60+ scripts
- [ ] Update database schema
- [ ] Create migration script for existing users
- [ ] Write comprehensive tests

### Phase 3: Documentation (Week 3)
- [ ] README.md with screenshots
- [ ] INSTALL.md with troubleshooting
- [ ] ARCHITECTURE.md for contributors
- [ ] FEATURES.md with examples
- [ ] Video tutorials (optional)

### Phase 4: Polish (Week 4)
- [ ] Enhanced install.sh (service validation)
- [ ] Obsidian plugin configuration generator
- [ ] Performance optimization
- [ ] Beta testing with 5+ users
- [ ] GitHub release

### Phase 5: Community (Ongoing)
- [ ] Public GitHub repository
- [ ] Issue tracker and support
- [ ] Feature requests and voting
- [ ] Plugin store submission (future)

---

## Success Metrics

### Technical
- [ ] Zero hardcoded paths in codebase
- [ ] 90%+ test coverage
- [ ] Installation success rate: >95%
- [ ] Configuration time: <5 minutes

### User Experience
- [ ] Installation: One command (`./install.sh`)
- [ ] Documentation: Complete, clear, beginner-friendly
- [ ] Support: Issue response time <24 hours
- [ ] Community: 100+ GitHub stars in 3 months

---

## Risk Analysis

### High Risk
1. **Service Dependencies**: Ollama/Qdrant must be running
   - Mitigation: Auto-start in install.sh, health checks

2. **Korean Path Handling**: Complex bash escaping
   - Mitigation: Already solved with bash wrapper pattern

### Medium Risk
3. **Cross-platform Support**: Currently macOS only
   - Mitigation: Phase 2 - Linux support, Phase 3 - Windows

4. **Breaking Changes**: Config system changes file locations
   - Mitigation: Migration script for existing users

### Low Risk
5. **Performance**: Large vaults (10,000+ docs)
   - Mitigation: Already tested with 1755 docs, scales linearly

---

## Conclusion

**Current State:** Fully functional but not shareable (hardcoded paths)

**Target State:** One-command installable, config-based, well-documented

**Estimated Effort:** 4 weeks (1 week per phase)

**Unique Value Proposition:**
- Most advanced local AI integration for Obsidian
- No API costs (Ollama + BGE-M3)
- Hybrid search (vector + full-text)
- CLI power tools for batch operations
- Comprehensive vault health monitoring

**Next Immediate Steps:**
1. Create new project at `~/workspace/obsidian-local-sage/`
2. Copy working code to new structure
3. Implement config system
4. Refactor core 10 scripts
5. Test with clean vault
