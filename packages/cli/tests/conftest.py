"""
Pytest configuration and fixtures for Obsidian Local Sage tests.
"""

import sys
import tempfile
import shutil
from pathlib import Path
from typing import Generator

import pytest
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    tmp_dir = tempfile.mkdtemp(prefix="obsidian_test_")
    yield Path(tmp_dir)
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def mock_vault(temp_dir: Path) -> Path:
    """Create a mock Obsidian vault for testing."""
    vault_path = temp_dir / "TestVault"
    vault_path.mkdir()

    # Create .obsidian directory (marks it as an Obsidian vault)
    (vault_path / ".obsidian").mkdir()

    # Create some test documents
    docs = {
        "README.md": """# Test Vault

This is a test vault for Obsidian Local Sage.

## Features

- Document search
- Link suggestions
- Health check
""",
        "Project/project-alpha.md": """# Project Alpha

Tags: #project #active

## Overview

This is a sample project document.

## Related

- [[Project Beta]]
- [[Meeting Notes]]
""",
        "Project/project-beta.md": """# Project Beta

Tags: #project #planning

## Overview

Another project document.

## TODOs

- [ ] Task 1
- [ ] Task 2
""",
        "Notes/meeting-notes.md": """# Meeting Notes

Date: 2024-01-15

## Attendees

- Person A
- Person B

## Discussion

Meeting content here.
""",
        "Notes/empty-note.md": "",
        "Archive/old-document.md": """# Old Document

This is an old document for testing.
""",
    }

    for path, content in docs.items():
        file_path = vault_path / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    return vault_path


@pytest.fixture
def mock_config_file(temp_dir: Path, mock_vault: Path) -> Path:
    """Create a mock configuration file."""
    config_dir = temp_dir / "config"
    config_dir.mkdir()

    config_path = config_dir / "settings.yaml"
    config_data = {
        "vault": {
            "path": str(mock_vault),
            "name": mock_vault.name,
        },
        "project": {
            "root": str(temp_dir),
            "db_path": str(temp_dir / "db" / "automation.db"),
            "search_results_dir": "검색결과",
        },
        "services": {
            "ollama": {
                "api_base": "http://127.0.0.1:11434",
                "model": "bge-m3",
                "timeout": 120,
            },
            "qdrant": {
                "host": "127.0.0.1",
                "port": 6333,
                "collection": "test_docs",
            },
        },
        "features": {
            "search": {
                "max_results": 8,
                "min_score": 0.3,
            },
            "health_check": {
                "old_document_days": 365,
                "large_document_kb": 100,
            },
        },
        "advanced": {
            "debug": True,
            "log_path": str(temp_dir / "logs"),
        },
    }

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, allow_unicode=True)

    # Create required directories
    (temp_dir / "db").mkdir()
    (temp_dir / "logs").mkdir()

    return config_path


@pytest.fixture
def mock_db(temp_dir: Path) -> Path:
    """Create a mock SQLite database."""
    import sqlite3

    db_path = temp_dir / "db" / "automation.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create tables
    cursor.executescript("""
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

        CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
            title,
            content,
            tags,
            aliases,
            content='document_index',
            content_rowid='id'
        );

        CREATE TABLE IF NOT EXISTS recent_documents (
            file_path TEXT PRIMARY KEY,
            title TEXT,
            accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            access_count INTEGER DEFAULT 1
        );
    """)

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def sample_markdown_content() -> str:
    """Sample markdown content for testing."""
    return """# Sample Document

Tags: #test #sample

## Introduction

This is a sample document for testing purposes.

## Features

- Feature 1
- Feature 2
- Feature 3

## Code Example

```python
def hello():
    print("Hello, World!")
```

## Links

- [[Related Document]]
- [[Another Note]]

## TODOs

- [ ] Incomplete task
- [x] Complete task
"""


@pytest.fixture
def mock_env(mock_config_file: Path, monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("OBSIDIAN_SAGE_CONFIG", str(mock_config_file))
