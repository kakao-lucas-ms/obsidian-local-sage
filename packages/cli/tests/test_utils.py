"""
Tests for utility functions and common operations.
"""

import sys
import sqlite3
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestDatabase:
    """Tests for database operations."""

    def test_database_creation(self, mock_db: Path):
        """Test that mock database is created correctly."""
        assert mock_db.exists()

        conn = sqlite3.connect(str(mock_db))
        cursor = conn.cursor()

        # Check tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        assert "document_index" in tables
        assert "recent_documents" in tables
        conn.close()

    def test_database_fts(self, mock_db: Path):
        """Test FTS5 virtual table."""
        conn = sqlite3.connect(str(mock_db))
        cursor = conn.cursor()

        # Check FTS table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='document_fts'
        """)
        result = cursor.fetchone()
        assert result is not None
        conn.close()

    def test_insert_document(self, mock_db: Path):
        """Test inserting a document into the index."""
        conn = sqlite3.connect(str(mock_db))
        cursor = conn.cursor()

        # Insert a test document
        cursor.execute(
            """
            INSERT INTO document_index (file_path, file_name, title, content, tags)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                "/test/path/doc.md",
                "doc.md",
                "Test Document",
                "This is test content for searching.",
                "test,sample",
            ),
        )
        conn.commit()

        # Verify insert
        cursor.execute("SELECT * FROM document_index WHERE file_path = ?", ("/test/path/doc.md",))
        row = cursor.fetchone()
        assert row is not None
        assert row[2] == "doc.md"  # file_name

        conn.close()

    def test_fts_search(self, mock_db: Path):
        """Test full-text search functionality."""
        conn = sqlite3.connect(str(mock_db))
        cursor = conn.cursor()

        # Insert documents
        docs = [
            (
                "/path/python.md",
                "python.md",
                "Python Guide",
                "Learn Python programming language",
                "python,programming",
            ),
            (
                "/path/javascript.md",
                "javascript.md",
                "JavaScript Guide",
                "Learn JavaScript for web development",
                "javascript,web",
            ),
            (
                "/path/rust.md",
                "rust.md",
                "Rust Guide",
                "Learn Rust for system programming",
                "rust,systems",
            ),
        ]

        for doc in docs:
            cursor.execute(
                """
                INSERT INTO document_index (file_path, file_name, title, content, tags)
                VALUES (?, ?, ?, ?, ?)
            """,
                doc,
            )
            # Also insert into FTS (contentless FTS requires manual sync)
            cursor.execute(
                """
                INSERT INTO document_fts (rowid, title, content, tags, aliases)
                VALUES (last_insert_rowid(), ?, ?, ?, ?)
            """,
                (doc[2], doc[3], doc[4], ""),
            )
        conn.commit()

        # Search for "programming"
        cursor.execute("""
            SELECT d.title FROM document_index d
            JOIN document_fts fts ON fts.rowid = d.id
            WHERE document_fts MATCH 'programming'
        """)
        results = cursor.fetchall()
        titles = [r[0] for r in results]

        assert "Python Guide" in titles
        assert "Rust Guide" in titles
        assert "JavaScript Guide" not in titles

        conn.close()

    def test_recent_documents_tracking(self, mock_db: Path):
        """Test recent documents tracking."""
        conn = sqlite3.connect(str(mock_db))
        cursor = conn.cursor()

        # Insert a recent document
        cursor.execute(
            """
            INSERT INTO recent_documents (file_path, title, access_count)
            VALUES (?, ?, ?)
        """,
            ("/path/recent.md", "Recent Doc", 1),
        )
        conn.commit()

        # Update access count (simulate re-access)
        cursor.execute(
            """
            UPDATE recent_documents
            SET access_count = access_count + 1,
                accessed_at = CURRENT_TIMESTAMP
            WHERE file_path = ?
        """,
            ("/path/recent.md",),
        )
        conn.commit()

        # Verify count increased
        cursor.execute(
            "SELECT access_count FROM recent_documents WHERE file_path = ?", ("/path/recent.md",)
        )
        row = cursor.fetchone()
        assert row[0] == 2

        conn.close()


class TestVaultOperations:
    """Tests for vault-related operations."""

    def test_mock_vault_structure(self, mock_vault: Path):
        """Test that mock vault has correct structure."""
        assert mock_vault.exists()
        assert (mock_vault / ".obsidian").exists()

    def test_mock_vault_documents(self, mock_vault: Path):
        """Test that mock vault has expected documents."""
        readme = mock_vault / "README.md"
        assert readme.exists()
        content = readme.read_text()
        assert "Test Vault" in content

    def test_mock_vault_folders(self, mock_vault: Path):
        """Test that mock vault has expected folders."""
        assert (mock_vault / "Project").exists()
        assert (mock_vault / "Notes").exists()
        assert (mock_vault / "Archive").exists()

    def test_empty_note_detection(self, mock_vault: Path):
        """Test empty note detection logic."""
        empty_note = mock_vault / "Notes" / "empty-note.md"
        assert empty_note.exists()

        content = empty_note.read_text()
        # Empty or very short content
        assert len(content.strip()) < 20


class TestMarkdownParsing:
    """Tests for markdown parsing operations."""

    def test_extract_title(self, sample_markdown_content: str):
        """Test extracting title from markdown."""
        import re

        # Simple title extraction
        match = re.search(r"^#\s+(.+)$", sample_markdown_content, re.MULTILINE)
        assert match is not None
        assert match.group(1) == "Sample Document"

    def test_extract_tags(self, sample_markdown_content: str):
        """Test extracting tags from markdown."""
        import re

        # Find hashtags in content
        tags = re.findall(r"#(\w+)", sample_markdown_content)
        assert "test" in tags
        assert "sample" in tags

    def test_extract_wikilinks(self, sample_markdown_content: str):
        """Test extracting wikilinks from markdown."""
        import re

        # Find [[wikilinks]]
        links = re.findall(r"\[\[([^\]]+)\]\]", sample_markdown_content)
        assert "Related Document" in links
        assert "Another Note" in links

    def test_extract_todos(self, sample_markdown_content: str):
        """Test extracting todos from markdown."""
        import re

        # Find incomplete todos
        incomplete = re.findall(r"- \[ \] (.+)", sample_markdown_content)
        complete = re.findall(r"- \[x\] (.+)", sample_markdown_content)

        assert len(incomplete) == 1
        assert len(complete) == 1
        assert "Incomplete task" in incomplete[0]

    def test_count_headings(self, sample_markdown_content: str):
        """Test counting headings in markdown."""
        import re

        # Count all headings
        headings = re.findall(r"^#+\s+.+$", sample_markdown_content, re.MULTILINE)
        assert len(headings) >= 4  # Title + Introduction + Features + etc.


class TestPathOperations:
    """Tests for path handling operations."""

    def test_path_expansion(self):
        """Test home directory expansion."""
        path = Path("~/Documents")
        expanded = path.expanduser()
        assert "~" not in str(expanded)

    def test_relative_path_calculation(self, mock_vault: Path):
        """Test calculating relative paths."""
        doc_path = mock_vault / "Project" / "project-alpha.md"
        relative = doc_path.relative_to(mock_vault)
        assert str(relative) == "Project/project-alpha.md"

    def test_file_stem_extraction(self):
        """Test extracting file name without extension."""
        path = Path("/path/to/document.md")
        assert path.stem == "document"
        assert path.suffix == ".md"


class TestURIEncoding:
    """Tests for URI encoding (for Obsidian URLs)."""

    def test_simple_path_encoding(self):
        """Test encoding simple path for Obsidian URI."""
        from urllib.parse import quote

        path = "Project/document.md"
        encoded = quote(path)
        assert "Project" in encoded
        assert "%2F" in encoded or "/" in encoded  # Slash may or may not be encoded

    def test_korean_path_encoding(self):
        """Test encoding Korean path for Obsidian URI."""
        from urllib.parse import quote

        path = "프로젝트/문서.md"
        encoded = quote(path, safe="")
        # Korean characters should be percent-encoded
        assert "%" in encoded

    def test_space_encoding(self):
        """Test encoding paths with spaces."""
        from urllib.parse import quote

        path = "My Project/my document.md"
        encoded = quote(path)
        assert "%20" in encoded or "+" in encoded


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_valid_yaml_config(self, mock_config_file: Path):
        """Test that config file is valid YAML."""
        import yaml

        with open(mock_config_file, "r") as f:
            config = yaml.safe_load(f)

        assert isinstance(config, dict)
        assert "vault" in config
        assert "services" in config

    def test_required_config_keys(self, mock_config_file: Path):
        """Test that required config keys are present."""
        import yaml

        with open(mock_config_file, "r") as f:
            config = yaml.safe_load(f)

        # Required keys
        assert "vault" in config
        assert "path" in config["vault"]
        assert "services" in config
        assert "ollama" in config["services"]
        assert "qdrant" in config["services"]
