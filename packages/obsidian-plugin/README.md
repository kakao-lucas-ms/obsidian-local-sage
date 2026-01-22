# Sage AI - Obsidian Plugin

**AI-powered semantic search for Obsidian, running entirely locally.**

## Features

- **Semantic Search** - Search your vault by meaning, not just keywords
- **Jump to Document** - Fast fuzzy finder sorted by recent modifications
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

## License

MIT License
