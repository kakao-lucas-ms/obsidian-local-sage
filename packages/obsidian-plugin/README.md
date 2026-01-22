# Sage AI - Obsidian Plugin

**AI-powered semantic search for Obsidian, running entirely locally.**

## Features

- **Semantic Search** - Search your vault by meaning, not just keywords
- **Jump to Document** - Fast fuzzy finder sorted by recent modifications
- **Link Suggestions** - AI-powered suggestions for connecting related documents
- **Vault Health Check** - Diagnose vault issues (empty docs, broken links, orphans, etc.)
- **Document Comparison** - Analyze similarities and differences between two documents
- **Vault Indexing** - Index all your notes for instant search

## Prerequisites

Before using Sage AI, you need to have these services running locally:

### 1. Ollama

Install Ollama and download the bge-m3 embedding model:

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama
ollama serve

# Download embedding model
ollama pull bge-m3
```

### 2. Qdrant

Run Qdrant using Docker:

```bash
docker run -p 6333:6333 qdrant/qdrant
```

## Installation

### From Community Plugins (Coming Soon)

1. Open Obsidian Settings
2. Go to Community Plugins
3. Search for "Sage AI"
4. Click Install, then Enable

### Manual Installation

1. Download the latest release (`main.js`, `manifest.json`, `styles.css`)
2. Create a folder: `.obsidian/plugins/sage-ai/`
3. Copy the files into that folder
4. Enable the plugin in Obsidian Settings > Community Plugins

## Usage

### Commands

Open the command palette (Cmd/Ctrl + P) and search for:

- **Sage AI: Semantic Search** - Search your vault by meaning
- **Sage AI: Jump to Document** - Quick fuzzy finder
- **Sage AI: Suggest Links for Current Note** - Get AI-powered link suggestions
- **Sage AI: Vault Health Check** - Diagnose vault health issues
- **Sage AI: Compare with Another Document** - Compare current document with another
- **Sage AI: Rebuild Index** - Re-index all documents
- **Sage AI: Check Connection Status** - Verify Ollama & Qdrant connections

### First Time Setup

1. Go to Settings > Sage AI
2. Verify Ollama URL (default: `http://127.0.0.1:11434`)
3. Verify Qdrant URL (default: `http://127.0.0.1:6333`)
4. Click "Test Connections" to verify
5. Run "Sage AI: Rebuild Index" to index your vault

## Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| Ollama URL | URL of your Ollama server | `http://127.0.0.1:11434` |
| Embedding Model | Model for generating embeddings | `bge-m3` |
| Qdrant URL | URL of your Qdrant server | `http://127.0.0.1:6333` |
| Collection Name | Qdrant collection for vectors | `obsidian_docs` |
| Max Results | Maximum search results | 8 |
| Minimum Score | Minimum similarity threshold | 0.3 |

## Development

```bash
# Install dependencies
pnpm install

# Development mode (watch)
pnpm run dev

# Production build
pnpm run build
```

## How It Works

### Link Suggestions
Analyzes the current document's content using embeddings, finds semantically similar documents in your vault, and suggests relevant wikilinks to add.

### Vault Health Check
Performs 8 diagnostic checks:
- Empty documents (0 characters)
- Nearly empty documents (< 20 characters)
- Orphaned documents (no incoming links)
- Broken wikilinks
- Duplicate file names
- Old documents (not modified in 1+ year)
- Large documents (> 100KB)
- Documents without tags
- Uncompleted TODO items

### Document Comparison
Compares two documents and provides:
- Semantic similarity score (using embeddings)
- Text match percentage
- Common tags and links
- Shared keywords vs unique keywords
- Actionable suggestions (merge, link, or organize)

## Privacy & Security

**Everything runs locally on your machine.** No data is sent to external servers. Sage AI uses:
- **Ollama** for local embeddings (bge-m3 model)
- **Qdrant** for local vector search

## License

MIT License
