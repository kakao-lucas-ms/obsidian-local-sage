# 🧙 Obsidian Local Sage

**Advanced AI-powered tools for Obsidian, running entirely on your machine.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/Ollama-BGE--M3-green.svg)](https://ollama.ai/)
[![CI](https://github.com/kakao-lucas-ms/obsidian-local-sage/actions/workflows/ci.yml/badge.svg)](https://github.com/kakao-lucas-ms/obsidian-local-sage/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/kakao-lucas-ms/obsidian-local-sage/branch/main/graph/badge.svg)](https://codecov.io/gh/kakao-lucas-ms/obsidian-local-sage)
[![PyPI version](https://badge.fury.io/py/obsidian-local-sage.svg)](https://badge.fury.io/py/obsidian-local-sage)

---

## 🎯 What is Obsidian Local Sage?

Obsidian Local Sage brings the power of AI to your Obsidian vault without sending your data to the cloud. Everything runs locally using Ollama and open-source models.

### 🌟 Key Features

#### 1. **AI-Powered Semantic Search** 🔍
- Search by meaning, not just keywords
- Creates clickable wikilink notes with results
- Hybrid search combining vector + full-text

#### 2. **Lightning-Fast Document Jump** ⚡
- Interactive fuzzy finder (fzf) for all documents
- Full-text search across 1000+ documents
- Recent document tracking

#### 3. **Smart Link Suggestions** 🔗
- AI finds related documents automatically
- Semantic similarity analysis
- One-click wikilink generation

#### 4. **Document Comparison** 📊
- Compare any two documents
- Similarity scores and analysis
- Find common themes and differences

#### 5. **Batch Operations** 📦
- Generate MOC (Map of Content) automatically
- Bulk tag management
- Broken link detection
- Folder summaries

#### 6. **Vault Health Check** 🏥
- Find empty documents
- Detect orphaned notes
- Check broken links
- Identify old/large files
- Count unfinished TODOs

---

## 🚀 Quick Start

### Prerequisites

- macOS (Linux support coming soon)
- Python 3.8+
- [Ollama](https://ollama.ai/) installed
- [Docker](https://www.docker.com/) (for Qdrant)
- Obsidian with [Shell Commands](https://github.com/Taitava/obsidian-shellcommands) plugin

### Installation

**Option 1: Using pip (Recommended)**

```bash
pip install obsidian-local-sage
```

**Option 2: From Source**

```bash
# Clone the repository
git clone https://github.com/your-username/obsidian-local-sage.git
cd obsidian-local-sage

# Run the installer (auto-detects vault, installs dependencies)
./install.sh
```

**Option 3: Development Install**

```bash
git clone https://github.com/your-username/obsidian-local-sage.git
cd obsidian-local-sage
pip install -e ".[dev]"  # Install with dev dependencies
```

The installer will:
1. ✅ Detect your Obsidian vault
2. ✅ Install required dependencies (fzf, Python packages)
3. ✅ Pull Ollama BGE-M3 model
4. ✅ Start Qdrant vector database
5. ✅ Create configuration file
6. ✅ Initialize database and build index
7. ✅ Set up CLI commands (obsidian-sage, sage-search, etc.)

### Configure Obsidian

1. Install [Shell Commands](https://github.com/Taitava/obsidian-shellcommands) plugin
2. Import commands from `obsidian-config/shell-commands.json`
3. Restart Obsidian
4. Test with `Cmd+P` → "🔍 AI 검색"

---

## 📖 Features in Detail

### 1. AI Search

**From Obsidian:**
- Open Command Palette (`Cmd+P`)
- Run "🔍 AI 검색"
- Enter your search query
- Results open as a new note with clickable wikilinks

**From CLI:**
```bash
python3 src/search/obsidian-wrapper-search-v4.py "query"
```

**Example Results:**
```markdown
# 검색 결과: machine learning

검색일시: 2026-01-21 10:30:00
결과 수: 5개

---

## 1. [[Projects/ML/Neural Networks|Neural Networks]]

**점수:** 0.852
**내용 미리보기:**
> Neural networks are the foundation of deep learning...
```

### 2. Document Jump

**From Obsidian:**
- `Cmd+P` → "📄 문서 점프"
- Start typing to filter
- Press Enter to open

**From CLI:**
```bash
bash src/jump/obsidian-jump-fixed.sh [search query]
```

**Features:**
- Searches across all 1755+ documents
- Shows file name, category, aliases
- Preview pane with file contents
- Recent access tracking

### 3. Link Suggestions

**From Obsidian:**
- Open a document
- `Cmd+P` → "🔗 링크 제안"
- Copy suggested wikilinks
- Paste into your document

**From CLI:**
```bash
python3 src/analysis/obsidian-suggest-links.py "path/to/note.md"
```

**Example Output:**
```
🔗 링크 제안: 프로젝트 회고

✅ 8개의 관련 문서를 찾았습니다!

1. 워크샵_프로세스_재사용_정리방법
   점수: 0.553
   링크: [[아이데이션 워크샵/워크샵_프로세스_재사용_정리방법]]
   내용: 워크샵 프로세스를 정리하고 재사용하는 방법...
```

### 4. Document Comparison

```bash
python3 src/analysis/obsidian-compare-docs.py "doc1.md" "doc2.md"
```

**Analysis includes:**
- Basic stats (word count, lines, headings)
- Semantic similarity (0-1 score)
- Text overlap percentage
- Common tags and links
- Unique keywords
- Merge suggestions

### 5. Batch Processing

```bash
# Folder summary
python3 src/batch/obsidian-batch-process.py summary "folder/"

# Generate MOC
python3 src/batch/obsidian-batch-process.py moc "folder/" --title "Index"

# Add tags to all documents
python3 src/batch/obsidian-batch-process.py add-tag "folder/" --tag "project"

# Check broken links
python3 src/batch/obsidian-batch-process.py check-links "folder/"
```

### 6. Vault Health Check

**From Obsidian:**
- `Cmd+P` → "🏥 Vault 건강 체크"

**From CLI:**
```bash
# Using CLI command
sage-health

# Or directly
python3 src/health/obsidian-health-check.py
```

**Checks for:**
- 📄 Empty documents (< 20 chars)
- 🔗 Orphaned notes (no incoming links)
- 🔗 Broken links
- 📁 Duplicate file names
- ⏰ Old documents (> 1 year)
- 📏 Large files (> 100KB)
- 🏷️ Untagged documents
- ✅ Unfinished TODOs

---

## 🎓 Use Cases

### Research & Writing
```bash
# Find related papers
python3 src/analysis/obsidian-suggest-links.py "Research/Paper.md"

# Compare two literature reviews
python3 src/analysis/obsidian-compare-docs.py "Review1.md" "Review2.md"
```

### Project Management
```bash
# Generate project MOC
python3 src/batch/obsidian-batch-process.py moc "Projects/MyProject/"

# Add project tag to all notes
python3 src/batch/obsidian-batch-process.py add-tag "Projects/MyProject/" --tag "active"

# Find broken links in project
python3 src/batch/obsidian-batch-process.py check-links "Projects/MyProject/"
```

### Vault Maintenance
```bash
# Weekly health check
python3 src/health/obsidian-health-check.py

# Find and fix orphaned notes
# (Review health check output and add links)
```

---

## ⚙️ Configuration

Edit `~/.obsidian-local-sage/config/settings.yaml`:

```yaml
vault:
  path: ~/Documents/MyVault

services:
  ollama:
    api_base: http://127.0.0.1:11434
    model: bge-m3

  qdrant:
    host: 127.0.0.1
    port: 6333

features:
  search:
    max_results: 8
    min_score: 0.3

  health_check:
    old_document_days: 365
    large_document_kb: 100
```

See `config/settings.example.yaml` for all options.

---

## 💻 CLI Commands

After installation, you have access to these CLI commands:

| Command | Description | Example |
|---------|-------------|---------|
| `obsidian-sage` | Main CLI with all commands | `obsidian-sage search "query"` |
| `sage-search` | AI semantic search | `sage-search "machine learning"` |
| `sage-jump` | Interactive document jump | `sage-jump` |
| `sage-ingest` | Build/rebuild index | `sage-ingest --full` |
| `sage-health` | Vault health check | `sage-health --json` |

### Main CLI Usage

```bash
# Show all commands
obsidian-sage --help

# AI Search
obsidian-sage search "my query"

# Document Jump
obsidian-sage jump

# Rebuild Index
obsidian-sage ingest --full

# Health Check
obsidian-sage health

# Show Configuration
obsidian-sage config
```

---

## 🔧 Advanced Usage

### Custom Search Weights

Adjust hybrid search in config:
```yaml
features:
  search:
    vector_weight: 0.7  # Semantic similarity
    fts_weight: 0.3     # Keyword matching
```

### Rebuild Index

```bash
python3 src/core/ingest-direct.py --full
```

### View Logs

```bash
tail -f ~/.obsidian-local-sage/logs/obsidian-sage.log
```

---

## 🆚 Comparison with Other Tools

| Feature | Obsidian Local Sage | Smart Connections | Vector Search |
|---------|---------------------|-------------------|---------------|
| **Local AI** | ✅ Ollama | ❌ OpenAI API | ❌ Cloud |
| **No API Costs** | ✅ Free | ❌ Paid | ❌ Paid |
| **Hybrid Search** | ✅ Vector + FTS | ⚠️ Vector only | ⚠️ Vector only |
| **Document Jump** | ✅ fzf | ❌ | ❌ |
| **Batch Operations** | ✅ MOC, tags, links | ❌ | ❌ |
| **Health Check** | ✅ 8 checks | ❌ | ❌ |
| **CLI Tools** | ✅ Full suite | ❌ | ❌ |
| **Installation** | ⚠️ One command | ✅ Plugin only | ✅ Plugin only |

**Unique advantages:**
- 🆓 Completely free (no API costs)
- 🔒 100% local (privacy)
- 🛠️ Powerful CLI tools
- 🔍 Advanced batch operations
- 🏥 Comprehensive health monitoring

---

## 🐛 Troubleshooting

### "Cannot connect to Ollama"
```bash
# Check if Ollama is running
ollama list

# Pull BGE-M3 model
ollama pull bge-m3
```

### "Cannot connect to Qdrant"
```bash
# Check if Qdrant container is running
docker ps | grep qdrant

# Start Qdrant
docker run -d -p 6333:6333 -v qdrant_data:/qdrant/storage qdrant/qdrant
```

### "Database not found"
```bash
# Rebuild database
python3 src/core/ingest-direct.py --full
```

### Shell Commands not working
- Check output handler (modal/notification/ignore)
- Check bash wrapper permissions: `chmod +x src/*/obsidian-*.sh`
- Check logs: `~/.obsidian-local-sage/logs/`

---

## 📚 Documentation

- [Feature Guide](docs/NEW_FEATURES_GUIDE.md) - Detailed feature documentation
- [Integration Status](docs/OBSIDIAN_INTEGRATION_STATUS.md) - All features tested
- [Refactoring Plan](REFACTORING_PLAN.md) - Architecture and roadmap
- [Old README](docs/OLD_README.md) - Original project documentation

---

## 🗺️ Roadmap

### Phase 1: Foundation ✅
- [x] Core features working
- [x] Configuration system
- [x] Project restructuring

### Phase 2: Migration ✅
- [x] Refactor all scripts to use config
- [x] Remove hardcoded paths
- [x] Create install.sh
- [x] PyPI packaging (pyproject.toml)
- [x] CLI entry points

### Phase 3: Testing & CI (Current)
- [x] Comprehensive pytest tests
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Code coverage reporting
- [ ] Pre-commit hooks

### Phase 4: Enhancement
- [ ] Web UI (optional)
- [ ] Plugin version
- [ ] Linux support
- [ ] Windows support (WSL)

### Phase 5: Community
- [ ] Public PyPI release
- [ ] Video tutorials
- [ ] Community plugins
- [ ] Obsidian plugin store submission

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone and install in dev mode
git clone https://github.com/your-username/obsidian-local-sage.git
cd obsidian-local-sage

# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html

# Format code
black src/ tests/

# Type checking
mypy src/

# Lint
flake8 src/ tests/
```

### Project Structure

```
obsidian-local-sage/
├── src/
│   ├── core/          # Core functionality (config, ingest)
│   ├── search/        # Search-related scripts
│   ├── jump/          # Document jump scripts
│   ├── batch/         # Batch operations
│   ├── health/        # Vault health check
│   ├── analysis/      # Document analysis tools
│   └── cli.py         # CLI entry points
├── tests/             # pytest tests
├── config/            # Configuration templates
├── install.sh         # Installation script
├── pyproject.toml     # Package configuration
└── requirements.txt   # Dependencies
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **Ollama** - Local LLM runtime
- **BGE-M3** - Embedding model
- **Qdrant** - Vector database
- **fzf** - Fuzzy finder
- **Obsidian** - Amazing knowledge base

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/obsidian-local-sage/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/obsidian-local-sage/discussions)
- **Email**: your-email@example.com

---

**Made with ❤️ for the Obsidian community**

*"Knowledge is power, but only if you can find it."*
