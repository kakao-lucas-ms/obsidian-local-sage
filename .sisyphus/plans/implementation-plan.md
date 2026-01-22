# Obsidian Local Sage - Implementation Plan

**Created:** 2026-01-21
**Status:** Ready for Execution
**Target:** PyPI Package Release (obsidian-local-sage)

---

## Executive Summary

Obsidian Local Sage를 오픈소스로 공개 가능한 PyPI 패키지로 완성하는 구현 계획입니다.

### Goals
1. 하드코딩된 경로 제거 (17개 파일)
2. 자동 설치 스크립트 (install.sh) 생성
3. PyPI 패키지 구조 설정
4. pytest 자동 테스트 작성
5. 문서 업데이트

### Scope
- Platform: macOS (우선)
- Package: obsidian-local-sage
- Distribution: PyPI

---

## Phase 1: Core Refactoring (하드코딩 경로 제거)

### 1.1 Python Scripts Refactoring (9 files)

모든 Python 스크립트에서 하드코딩된 경로를 config 시스템으로 교체합니다.

#### Priority 1 - Search Scripts (4 files)
| File | Changes Required |
|------|------------------|
| `src/search/obsidian-wrapper-search-v4.py` | VAULT_PATH, DB_PATH, OUTPUT_DIR → config |
| `src/search/obsidian-wrapper-search-v3.py` | 동일 |
| `src/search/obsidian-wrapper-search-v2.py` | 동일 |
| `src/search/obsidian-wrapper-search.py` | 동일 |

**Refactoring Pattern:**
```python
# Before
VAULT_PATH = "/Users/kakao/workspace/my-note/나의노트"
DB_PATH = "/Users/kakao/workspace/kakao-github/claude-help-me/db/automation.db"

# After
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.core.config import config

VAULT_PATH = config.vault_path
DB_PATH = config.db_path
```

#### Priority 2 - Core Scripts (2 files)
| File | Changes Required |
|------|------------------|
| `src/core/ingest-direct.py` | DB_PATH, VAULT_PATH → config |
| `src/core/ingest-with-bm25.py` | 동일 |

#### Priority 3 - Feature Scripts (3 files)
| File | Changes Required |
|------|------------------|
| `src/batch/obsidian-batch-process.py` | VAULT_PATH → config |
| `src/health/obsidian-health-check.py` | VAULT_PATH, DB_PATH → config |
| `src/analysis/obsidian-suggest-links.py` | All paths → config |

### 1.2 Shell Scripts Refactoring (5 files)

Shell 스크립트는 환경변수 또는 config 파일에서 경로를 읽도록 수정합니다.

| File | Changes Required |
|------|------------------|
| `src/jump/obsidian-jump-fixed.sh` | VAULT_PATH → $OBSIDIAN_VAULT or config |
| `src/jump/obsidian-jump.sh` | 동일 |
| `src/jump/obsidian-wrapper-jump-v2.sh` | 동일 |
| `src/jump/obsidian-wrapper-jump-v3.sh` | 동일 |
| `src/search/obsidian-wrapper-search-interactive-v2.sh` | 동일 |

**Shell Refactoring Pattern:**
```bash
# Before
VAULT_PATH="/Users/kakao/workspace/my-note/나의노트"

# After
CONFIG_FILE="${HOME}/.obsidian-local-sage/config/settings.yaml"
if [ -f "$CONFIG_FILE" ]; then
    VAULT_PATH=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE'))['vault']['path'])" 2>/dev/null)
fi
VAULT_PATH="${VAULT_PATH:-$HOME/Documents/MyVault}"
```

### 1.3 Deliverables
- [ ] 9개 Python 스크립트 리팩토링 완료
- [ ] 5개 Shell 스크립트 리팩토링 완료
- [ ] 모든 스크립트 테스트 통과

---

## Phase 2: Installation Automation

### 2.1 install.sh 생성

자동 설치 스크립트를 생성합니다.

```bash
#!/bin/bash
# install.sh - Obsidian Local Sage Installer

set -e

echo "🔮 Installing Obsidian Local Sage..."

# 1. Check prerequisites
check_prerequisites() {
    # Python 3.8+
    # fzf
    # Ollama
    # Docker (for Qdrant)
}

# 2. Detect Obsidian vault
detect_vault() {
    # Search common locations
    # Ask user to confirm
}

# 3. Install Python dependencies
install_dependencies() {
    pip install -r requirements.txt
}

# 4. Create configuration
setup_config() {
    # Copy settings.example.yaml
    # Update vault path
}

# 5. Initialize database
init_database() {
    # Create db/automation.db
    # Run schema.sql
}

# 6. Start services
start_services() {
    # Check Ollama
    # Start Qdrant container
}

# 7. Build initial index
build_index() {
    # Run ingest-direct.py
}
```

### 2.2 Dependencies Management

**requirements.txt 생성:**
```
pyyaml>=6.0
qdrant-client>=1.7.0
requests>=2.28.0
```

**setup.py / pyproject.toml 생성:**
- Package metadata
- Entry points for CLI commands
- Dependencies

### 2.3 Deliverables
- [ ] install.sh 완성
- [ ] requirements.txt 생성
- [ ] 의존성 체크 로직 구현

---

## Phase 3: PyPI Package Structure

### 3.1 Package Configuration

**pyproject.toml:**
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "obsidian-local-sage"
version = "0.1.0"
description = "Local AI-powered search and analysis tools for Obsidian"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.8"
authors = [
    {name = "Your Name", email = "your@email.com"}
]
keywords = ["obsidian", "ai", "search", "local", "ollama", "qdrant"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Operating System :: MacOS",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Text Processing :: Indexing",
]
dependencies = [
    "pyyaml>=6.0",
    "qdrant-client>=1.7.0",
    "requests>=2.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
]

[project.scripts]
obsidian-sage = "obsidian_local_sage.cli:main"
sage-search = "obsidian_local_sage.search:main"
sage-jump = "obsidian_local_sage.jump:main"
sage-health = "obsidian_local_sage.health:main"
sage-batch = "obsidian_local_sage.batch:main"
sage-ingest = "obsidian_local_sage.ingest:main"

[project.urls]
Homepage = "https://github.com/yourname/obsidian-local-sage"
Documentation = "https://github.com/yourname/obsidian-local-sage#readme"
Repository = "https://github.com/yourname/obsidian-local-sage"
Issues = "https://github.com/yourname/obsidian-local-sage/issues"
```

### 3.2 Package Structure

```
obsidian-local-sage/
├── pyproject.toml
├── setup.py (optional, for backward compatibility)
├── MANIFEST.in
├── README.md
├── LICENSE
├── requirements.txt
├── install.sh
│
├── src/
│   └── obsidian_local_sage/    # Renamed for PyPI
│       ├── __init__.py
│       ├── cli.py              # Main CLI entry point
│       ├── core/
│       ├── search/
│       ├── jump/
│       ├── batch/
│       ├── health/
│       └── analysis/
│
├── config/
│   └── settings.example.yaml
│
├── db/
│   └── schema.sql
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_config.py
    ├── test_search.py
    ├── test_health.py
    └── test_batch.py
```

### 3.3 CLI Entry Point

**src/obsidian_local_sage/cli.py:**
```python
#!/usr/bin/env python3
"""Main CLI entry point for Obsidian Local Sage."""

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description="Obsidian Local Sage - AI-powered tools for your vault"
    )
    subparsers = parser.add_subparsers(dest="command")

    # search command
    search_parser = subparsers.add_parser("search", help="Search your vault")
    search_parser.add_argument("query", help="Search query")

    # jump command
    jump_parser = subparsers.add_parser("jump", help="Jump to a document")

    # health command
    health_parser = subparsers.add_parser("health", help="Check vault health")

    # batch command
    batch_parser = subparsers.add_parser("batch", help="Batch operations")

    # ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Index your vault")

    args = parser.parse_args()

    if args.command == "search":
        from .search import run_search
        run_search(args.query)
    # ... other commands

if __name__ == "__main__":
    main()
```

### 3.4 Deliverables
- [ ] pyproject.toml 생성
- [ ] 패키지 구조 재구성 (src → obsidian_local_sage)
- [ ] CLI entry point 구현
- [ ] MANIFEST.in 생성

---

## Phase 4: Testing Infrastructure

### 4.1 Test Structure

```
tests/
├── __init__.py
├── conftest.py           # Pytest fixtures
├── test_config.py        # Config system tests
├── test_search.py        # Search functionality tests
├── test_health.py        # Health check tests
├── test_batch.py         # Batch operation tests
├── test_analysis.py      # Analysis tool tests
└── fixtures/
    ├── sample_vault/     # Mock vault for testing
    │   ├── Note1.md
    │   ├── Note2.md
    │   └── folder/
    │       └── Note3.md
    └── sample_config.yaml
```

### 4.2 Test Cases

**test_config.py:**
```python
import pytest
from obsidian_local_sage.core.config import Config

class TestConfig:
    def test_load_config(self, tmp_path):
        """Config loads from YAML file."""

    def test_dot_notation_access(self):
        """Config supports dot notation: config.get('vault.path')"""

    def test_default_values(self):
        """Config returns defaults for missing keys."""

    def test_path_expansion(self):
        """Config expands ~ to home directory."""
```

**test_search.py:**
```python
class TestSearch:
    def test_hybrid_search(self, mock_vault):
        """Hybrid search returns relevant results."""

    def test_fts_search(self, mock_vault):
        """Full-text search works correctly."""

    def test_vector_search(self, mock_qdrant):
        """Vector search returns similar documents."""
```

**test_health.py:**
```python
class TestHealthCheck:
    def test_empty_files_detection(self, mock_vault):
        """Detects empty markdown files."""

    def test_orphaned_files_detection(self, mock_vault):
        """Detects files with no backlinks."""

    def test_broken_links_detection(self, mock_vault):
        """Detects broken internal links."""
```

### 4.3 Test Fixtures

**conftest.py:**
```python
import pytest
from pathlib import Path
import tempfile
import shutil

@pytest.fixture
def mock_vault(tmp_path):
    """Create a temporary mock vault for testing."""
    vault = tmp_path / "test_vault"
    vault.mkdir()

    # Create sample notes
    (vault / "Note1.md").write_text("# Note 1\nSome content here.")
    (vault / "Note2.md").write_text("# Note 2\n[[Note1]] linked.")
    (vault / "Empty.md").write_text("")  # Empty file

    return vault

@pytest.fixture
def mock_config(tmp_path, mock_vault):
    """Create a temporary config for testing."""
    config_content = f"""
vault:
  path: {mock_vault}
project:
  db_path: {tmp_path}/test.db
"""
    config_file = tmp_path / "settings.yaml"
    config_file.write_text(config_content)
    return config_file
```

### 4.4 Deliverables
- [ ] conftest.py with fixtures
- [ ] test_config.py (5+ tests)
- [ ] test_search.py (5+ tests)
- [ ] test_health.py (8 tests - one per check type)
- [ ] test_batch.py (3+ tests)
- [ ] Mock vault fixture
- [ ] CI configuration (.github/workflows/test.yml)

---

## Phase 5: Documentation Update

### 5.1 README.md Updates

- [ ] Installation via pip: `pip install obsidian-local-sage`
- [ ] Quick start guide
- [ ] CLI usage examples
- [ ] Configuration guide
- [ ] Screenshots/GIFs

### 5.2 Documentation Files

- [ ] CHANGELOG.md 생성
- [ ] CONTRIBUTING.md 생성
- [ ] API documentation (if needed)

### 5.3 Deliverables
- [ ] README.md 업데이트
- [ ] CHANGELOG.md
- [ ] CONTRIBUTING.md
- [ ] 예제 코드/스크린샷

---

## Implementation Order

### Week 1: Core Refactoring

| Day | Task | Files |
|-----|------|-------|
| 1 | Search scripts refactoring | 4 files |
| 2 | Core scripts refactoring | 2 files |
| 3 | Feature scripts refactoring | 3 files |
| 4 | Shell scripts refactoring | 5 files |
| 5 | Testing & verification | All |

### Week 2: Package & Install

| Day | Task | Deliverables |
|-----|------|--------------|
| 1 | requirements.txt, pyproject.toml | 2 files |
| 2 | Package restructure | Directory changes |
| 3 | CLI entry point | cli.py |
| 4 | install.sh | 1 file |
| 5 | Integration testing | Verification |

### Week 3: Testing & Polish

| Day | Task | Deliverables |
|-----|------|--------------|
| 1 | Test fixtures, conftest.py | Base testing |
| 2 | test_config.py, test_health.py | 13+ tests |
| 3 | test_search.py, test_batch.py | 8+ tests |
| 4 | Documentation updates | README, CHANGELOG |
| 5 | Final testing & PyPI prep | Release ready |

---

## Success Criteria

### Functional Requirements
- [ ] `pip install obsidian-local-sage` works
- [ ] `obsidian-sage --help` shows all commands
- [ ] `obsidian-sage search "query"` returns results
- [ ] `obsidian-sage health` runs all 8 checks
- [ ] All tests pass (>90% coverage)

### Quality Requirements
- [ ] No hardcoded paths in any file
- [ ] All scripts use config system
- [ ] Documentation is complete
- [ ] CI/CD pipeline works

### Distribution Requirements
- [ ] Package published to PyPI
- [ ] GitHub release created
- [ ] Install script works on fresh macOS

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Qdrant/Ollama dependency | Clear documentation, optional features |
| Korean path encoding | Tested bash escaping patterns |
| Python version compatibility | Test on 3.8, 3.9, 3.10, 3.11, 3.12 |
| Config migration | Migration script for existing users |

---

## Appendix: File Refactoring Checklist

### Python Files (9)
- [ ] `src/search/obsidian-wrapper-search-v4.py`
- [ ] `src/search/obsidian-wrapper-search-v3.py`
- [ ] `src/search/obsidian-wrapper-search-v2.py`
- [ ] `src/search/obsidian-wrapper-search.py`
- [ ] `src/core/ingest-direct.py`
- [ ] `src/core/ingest-with-bm25.py`
- [ ] `src/batch/obsidian-batch-process.py`
- [ ] `src/health/obsidian-health-check.py`
- [ ] `src/analysis/obsidian-suggest-links.py`

### Shell Files (5)
- [ ] `src/jump/obsidian-jump-fixed.sh`
- [ ] `src/jump/obsidian-jump.sh`
- [ ] `src/jump/obsidian-wrapper-jump-v2.sh`
- [ ] `src/jump/obsidian-wrapper-jump-v3.sh`
- [ ] `src/search/obsidian-wrapper-search-interactive-v2.sh`

### Documentation (2)
- [ ] `PROJECT_STATUS.md`
- [ ] `REFACTORING_PLAN.md`

---

**Plan Author:** Prometheus (Claude)
**Plan Version:** 1.0
**Ready for:** Execution with Sisyphus
