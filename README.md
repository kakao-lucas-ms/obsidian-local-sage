# Obsidian Local Sage

**AI-powered local tools for Obsidian, running entirely on your machine.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/kakao-lucas-ms/obsidian-local-sage/actions/workflows/ci.yml/badge.svg)](https://github.com/kakao-lucas-ms/obsidian-local-sage/actions/workflows/ci.yml)

---

## Overview

Obsidian Local Sage is a monorepo containing tools to bring AI-powered features to your Obsidian vault without sending data to the cloud. Everything runs locally using Ollama and Qdrant.

## Packages

| Package | Description | Status |
|---------|-------------|--------|
| [`@obsidian-local-sage/cli`](./packages/cli) | Python CLI with semantic search, document jump, health check | Stable |
| [`sage-ai`](./packages/obsidian-plugin) | Obsidian community plugin (TypeScript) | In Development |

## Quick Start

### Prerequisites

- [Ollama](https://ollama.ai/) with bge-m3 model
- [Docker](https://www.docker.com/) for Qdrant
- Python 3.8+ (for CLI)
- Node.js 18+ and pnpm (for plugin development)

### Install CLI

```bash
pip install obsidian-local-sage
```

Or from source:

```bash
cd packages/cli
pip install -e ".[dev]"
```

### Install Obsidian Plugin

The Sage AI plugin is currently in development. Once released, it will be available in the Obsidian Community Plugins.

For development:

```bash
cd packages/obsidian-plugin
pnpm install
pnpm run dev
```

## Features

### CLI Features

- **Semantic Search** - AI-powered search by meaning, not just keywords
- **Document Jump** - Fast fuzzy finder across all documents
- **Link Suggestions** - AI finds related documents automatically
- **Document Comparison** - Compare any two documents
- **Vault Health Check** - Find empty notes, broken links, orphans

### Plugin Features (Coming Soon)

- **Sage AI: Search** - Native Obsidian semantic search
- **Sage AI: Jump** - Quick document finder modal
- **Sage AI: Reindex** - Rebuild search index

## Architecture

```
obsidian-local-sage/
├── packages/
│   ├── cli/                 # Python CLI package
│   │   ├── src/             # Source code
│   │   ├── tests/           # pytest tests
│   │   └── pyproject.toml   # Package config
│   │
│   └── obsidian-plugin/     # TypeScript Obsidian plugin
│       ├── src/             # Plugin source
│       ├── manifest.json    # Obsidian manifest
│       └── package.json     # npm package config
│
├── package.json             # Monorepo root (pnpm workspaces)
└── pnpm-workspace.yaml      # Workspace config
```

## Development

```bash
# Install pnpm if needed
npm install -g pnpm

# Install all dependencies
pnpm install

# Run all tests
pnpm test

# Build all packages
pnpm build
```

### CLI Development

```bash
cd packages/cli
pip install -e ".[dev]"
pytest tests/ -v
```

### Plugin Development

```bash
cd packages/obsidian-plugin
pnpm install
pnpm run dev   # Watch mode
pnpm run build # Production build
```

## Documentation

- [CLI README](./packages/cli/README.md) - Full CLI documentation
- [Plugin README](./packages/obsidian-plugin/README.md) - Plugin documentation
- [Work Plan](./.sisyphus/plans/remaining-work-plan.md) - Development roadmap

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Made with love for the Obsidian community**
