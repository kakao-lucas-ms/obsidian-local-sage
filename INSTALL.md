# 📦 Installation Guide

Complete step-by-step installation guide for Obsidian Local Sage.

---

## Prerequisites

### Required

1. **macOS** (10.15+)
   - Linux support planned
   - Windows WSL support planned

2. **Python 3.8+**
   ```bash
   python3 --version  # Should show 3.8 or higher
   ```
   If not installed:
   ```bash
   brew install python3
   ```

3. **Obsidian**
   - Download from [obsidian.md](https://obsidian.md/)
   - Have at least one vault created

4. **Shell Commands Plugin**
   - Install from Obsidian Community Plugins
   - Settings → Community plugins → Browse
   - Search for "Shell commands"
   - Install and Enable

### Optional (Will be installed automatically)

- **Ollama** - Local LLM runtime
- **Qdrant** - Vector database (via Docker)
- **fzf** - Fuzzy finder

---

## Quick Installation

### Option 1: Automatic (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/obsidian-local-sage.git
cd obsidian-local-sage

# Run the installer
./install.sh
```

The installer will:
1. Auto-detect your Obsidian vault
2. Install all dependencies
3. Configure services (Ollama, Qdrant)
4. Create configuration file
5. Build initial document index
6. Generate Shell Commands config

**Estimated time:** 10-15 minutes

---

## Manual Installation

If automatic installation fails, follow these steps:

### Step 1: Install Dependencies

#### Install Homebrew (if not installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Install fzf
```bash
brew install fzf
```

#### Install Python packages
```bash
pip3 install qdrant-client requests pyyaml
```

#### Install Ollama
```bash
# Download and install from https://ollama.ai/
# Or via Homebrew:
brew install ollama

# Pull BGE-M3 embedding model
ollama pull bge-m3
```

#### Install Qdrant (via Docker)
```bash
# Install Docker Desktop from https://www.docker.com/products/docker-desktop
# Or via Homebrew:
brew install --cask docker

# Start Qdrant
docker run -d -p 6333:6333 \
  -v qdrant_data:/qdrant/storage \
  --name qdrant \
  qdrant/qdrant
```

### Step 2: Clone and Setup

```bash
# Clone repository
git clone https://github.com/your-username/obsidian-local-sage.git
cd obsidian-local-sage

# Create installation directory
mkdir -p ~/.obsidian-local-sage
cp -r * ~/.obsidian-local-sage/

# Create directories
mkdir -p ~/.obsidian-local-sage/{config,db,logs}
```

### Step 3: Configure

```bash
# Copy example config
cp config/settings.example.yaml ~/.obsidian-local-sage/config/settings.yaml

# Edit configuration
nano ~/.obsidian-local-sage/config/settings.yaml
```

**Update these values:**
```yaml
vault:
  path: /path/to/your/vault  # Change this!
  name: YourVaultName

project:
  root: ~/.obsidian-local-sage
  db_path: ~/.obsidian-local-sage/db/automation.db
```

### Step 4: Initialize Database

```bash
cd ~/.obsidian-local-sage

# Create database schema
sqlite3 db/automation.db < db/schema.sql

# Build initial index
python3 src/core/ingest-direct.py --full
```

**This will take 5-10 minutes depending on vault size.**

### Step 5: Configure Obsidian

#### Import Shell Commands

1. Open Obsidian
2. Settings → Community plugins → Shell commands
3. Click "Import" (top right)
4. Select `~/.obsidian-local-sage/obsidian-config/shell-commands.json`
5. Click "Import all"

#### Test Commands

1. Open Command Palette (`Cmd+P`)
2. Try these commands:
   - "🔍 AI 검색" - Semantic search
   - "📄 문서 점프" - Document jump
   - "🏥 Vault 건강 체크" - Health check

---

## Verification

### Check Services

#### Verify Ollama
```bash
# List models
ollama list

# Should show:
# NAME           ID              SIZE    MODIFIED
# bge-m3:latest  abc123...       2.0 GB  2 days ago
```

#### Verify Qdrant
```bash
# Check collections
curl http://127.0.0.1:6333/collections

# Should return JSON with collections
```

#### Verify Database
```bash
# Check document count
sqlite3 ~/.obsidian-local-sage/db/automation.db \
  "SELECT COUNT(*) FROM document_index;"

# Should show number of indexed documents
```

### Test Features

#### Test Search (CLI)
```bash
cd ~/.obsidian-local-sage
python3 src/search/obsidian-wrapper-search-v4.py "test query"
```

Should create a note in your vault's `검색결과/` directory.

#### Test Document Jump (CLI)
```bash
bash src/jump/obsidian-jump-fixed.sh
```

Should show fzf interface with all documents.

#### Test Health Check (CLI)
```bash
python3 src/health/obsidian-health-check.py
```

Should display vault health report.

---

## Troubleshooting

### "Command not found: ollama"

**Problem:** Ollama not in PATH

**Solution:**
```bash
# Add to ~/.zshrc or ~/.bash_profile
export PATH="/usr/local/bin:$PATH"

# Reload shell
source ~/.zshrc
```

### "Cannot connect to Qdrant"

**Problem:** Qdrant not running or wrong port

**Solutions:**

1. Check if Docker is running:
   ```bash
   docker ps
   ```

2. Start Qdrant if not running:
   ```bash
   docker start qdrant
   ```

3. Check if port 6333 is in use:
   ```bash
   lsof -i :6333
   ```

4. Recreate Qdrant container:
   ```bash
   docker stop qdrant
   docker rm qdrant
   docker run -d -p 6333:6333 -v qdrant_data:/qdrant/storage --name qdrant qdrant/qdrant
   ```

### "Database locked"

**Problem:** Multiple processes accessing database

**Solution:**
```bash
# Kill any hanging processes
pkill -f "obsidian"

# Restart and try again
```

### Shell Commands Show "No Output"

**Problem:** Script permissions or output handler

**Solutions:**

1. Check script permissions:
   ```bash
   chmod +x ~/.obsidian-local-sage/src/**/*.sh
   ```

2. Change output handler:
   - Settings → Shell commands → Select command
   - Change "Output channel" to "Modal"
   - Or change to "Notification" for quick messages

3. Check logs:
   ```bash
   tail -f ~/.obsidian-local-sage/logs/obsidian-sage.log
   ```

### Korean/Unicode Path Issues

**Problem:** File paths with Korean characters fail

**Solution:** Our bash wrappers already handle this. If you see issues:

1. Verify bash wrapper is being called:
   ```bash
   # In Shell Commands, command should be:
   bash ~/.obsidian-local-sage/src/search/obsidian-wrapper-search-terminal.sh
   # NOT:
   python3 ~/.obsidian-local-sage/src/search/obsidian-wrapper-search-v4.py
   ```

2. Check Shell Commands variables:
   - Use `{{selection}}` not `"{{selection}}"`
   - Bash wrapper handles quoting

### "Embedding model not found"

**Problem:** BGE-M3 not pulled

**Solution:**
```bash
ollama pull bge-m3

# Verify
ollama list | grep bge-m3
```

### "Collection not found in Qdrant"

**Problem:** Index not built

**Solution:**
```bash
# Rebuild index
python3 ~/.obsidian-local-sage/src/core/ingest-direct.py --full
```

---

## Performance Optimization

### For Large Vaults (5000+ documents)

1. **Increase Qdrant memory:**
   ```bash
   docker stop qdrant
   docker rm qdrant
   docker run -d -p 6333:6333 \
     -v qdrant_data:/qdrant/storage \
     --memory=2g \
     --name qdrant \
     qdrant/qdrant
   ```

2. **Adjust config:**
   ```yaml
   features:
     search:
       max_results: 5  # Reduce from 8
     batch:
       recursive_default: false  # Don't recurse by default
   ```

3. **Scheduled indexing:**
   ```bash
   # Add to crontab (daily at 3am)
   0 3 * * * cd ~/.obsidian-local-sage && python3 src/core/ingest-direct.py --incremental
   ```

### For Slow Searches

1. Check Ollama is using GPU:
   ```bash
   ollama ps
   # Should show GPU memory usage
   ```

2. Reduce batch size in search:
   ```yaml
   advanced:
     cache:
       enabled: true
       ttl_seconds: 3600
   ```

---

## Updating

### Update to Latest Version

```bash
cd obsidian-local-sage
git pull origin main

# Re-run installer
./install.sh
```

### Rebuild Index After Update

```bash
python3 ~/.obsidian-local-sage/src/core/ingest-direct.py --full
```

---

## Uninstallation

### Remove All Data

```bash
# Stop services
docker stop qdrant
docker rm qdrant

# Remove installation
rm -rf ~/.obsidian-local-sage

# Remove Docker volume
docker volume rm qdrant_data
```

### Keep Data, Remove Only Code

```bash
# Backup config and database
cp -r ~/.obsidian-local-sage/config ~/obsidian-sage-backup/
cp -r ~/.obsidian-local-sage/db ~/obsidian-sage-backup/

# Remove installation
rm -rf ~/.obsidian-local-sage

# Reinstall later and restore:
cp -r ~/obsidian-sage-backup/* ~/.obsidian-local-sage/
```

---

## Next Steps

After successful installation:

1. **Read the feature guide:**
   ```bash
   cat ~/.obsidian-local-sage/docs/NEW_FEATURES_GUIDE.md
   ```

2. **Try each command in Obsidian:**
   - 🔍 AI 검색
   - 📄 문서 점프
   - 🔗 링크 제안
   - 🏥 Vault 건강 체크

3. **Customize your workflow:**
   - Edit `~/.obsidian-local-sage/config/settings.yaml`
   - Adjust search parameters, thresholds, etc.

4. **Set up hotkeys in Obsidian:**
   - Settings → Hotkeys
   - Search for "Shell commands"
   - Assign shortcuts to your favorite commands

5. **Run regular maintenance:**
   ```bash
   # Weekly: Health check
   python3 ~/.obsidian-local-sage/src/health/obsidian-health-check.py

   # Monthly: Rebuild full index
   python3 ~/.obsidian-local-sage/src/core/ingest-direct.py --full
   ```

---

## Support

If you encounter issues:

1. Check [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
2. Search [existing issues](https://github.com/your-username/obsidian-local-sage/issues)
3. Open a [new issue](https://github.com/your-username/obsidian-local-sage/issues/new) with:
   - OS version
   - Python version (`python3 --version`)
   - Error messages
   - Relevant config (remove sensitive paths)

---

**Welcome to Obsidian Local Sage! 🧙**
