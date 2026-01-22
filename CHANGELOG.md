# Changelog

All notable changes to Obsidian Local Sage will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-01-21

### Added

- **Configuration System**
  - Centralized YAML-based configuration (`~/.obsidian-local-sage/config/settings.yaml`)
  - Singleton Config class with dot-notation access
  - Support for multiple config locations (user, development, legacy)
  - Automatic vault and path detection

- **CLI Entry Points**
  - `obsidian-sage` - Main CLI with subcommands
  - `sage-search` - AI-powered semantic search
  - `sage-jump` - Interactive document jump with fzf
  - `sage-ingest` - Build/rebuild search index
  - `sage-health` - Vault health check

- **Installation Automation**
  - Comprehensive `install.sh` script
  - Automatic vault detection
  - Docker-based Qdrant setup
  - Ollama model pulling
  - Database initialization

- **PyPI Packaging**
  - `pyproject.toml` with full metadata
  - Optional dependencies (`bm25`, `dev`)
  - Properly configured entry points
  - `requirements.txt` and `requirements-dev.txt`

- **Testing**
  - pytest test suite
  - Tests for configuration system
  - Tests for CLI entry points
  - Mock fixtures for vault and database

### Changed

- **Refactored Scripts**
  - All Python scripts now use centralized config
  - All Shell scripts load config from Python
  - Removed 60+ hardcoded paths
  - Dynamic vault name encoding for Obsidian URIs

- **Project Structure**
  - Organized source code into `src/` modules
  - Created `tests/` directory with pytest tests
  - Added development dependencies

### Fixed

- Shell script delimiter issues in fzf
- Path encoding for Korean file names
- Configuration fallback defaults

### Security

- No more hardcoded file paths
- Configurable service URLs
- Safe YAML loading

## [0.0.1] - 2026-01-15

### Added

- Initial project setup
- Core search functionality
- Document jump with fzf
- Health check features
- Basic configuration

---

[Unreleased]: https://github.com/your-username/obsidian-local-sage/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-username/obsidian-local-sage/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/your-username/obsidian-local-sage/releases/tag/v0.0.1
