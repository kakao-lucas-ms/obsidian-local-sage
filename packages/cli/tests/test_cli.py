"""
Tests for the CLI entry points.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestCLIHelpers:
    """Tests for CLI helper functions."""

    def test_get_script_path(self):
        """Test get_script_path returns correct path."""
        from src.cli import get_script_path

        path = get_script_path("search", "obsidian-wrapper-search-v4.py")

        assert path.name == "obsidian-wrapper-search-v4.py"
        assert "search" in str(path)

    def test_run_python_script_not_found(self, temp_dir: Path):
        """Test run_python_script with non-existent script."""
        from src.cli import run_python_script

        result = run_python_script(temp_dir / "nonexistent.py", [])
        assert result == 1

    def test_run_shell_script_not_found(self, temp_dir: Path):
        """Test run_shell_script with non-existent script."""
        from src.cli import run_shell_script

        result = run_shell_script(temp_dir / "nonexistent.sh", [])
        assert result == 1


class TestMainCLI:
    """Tests for the main CLI entry point."""

    def test_main_no_command_shows_help(self, capsys):
        """Test that main with no args shows help."""
        from src.cli import main

        with patch("sys.argv", ["obsidian-sage"]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower() or "obsidian-sage" in captured.out

    def test_main_version(self, capsys):
        """Test --version flag."""
        from src.cli import main

        with patch("sys.argv", ["obsidian-sage", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

        # argparse exits with 0 for --version
        assert exc_info.value.code == 0

    def test_main_config_command(self, mock_config_file: Path, mock_vault: Path, capsys):
        """Test config command output."""
        from src.cli import show_config

        # Mock the config module
        mock_config = MagicMock()
        mock_config._config_path = mock_config_file
        mock_config.vault_path = mock_vault
        mock_config.vault_name = "TestVault"
        mock_config.project_root = Path("/tmp/test")
        mock_config.db_path = Path("/tmp/test/db/automation.db")
        mock_config.log_path = Path("/tmp/test/logs")
        mock_config.ollama_api_base = "http://127.0.0.1:11434"
        mock_config.ollama_model = "bge-m3"
        mock_config.qdrant_host = "127.0.0.1"
        mock_config.qdrant_port = 6333
        mock_config.qdrant_collection = "test_docs"
        mock_config.debug = False

        with patch("src.core.config.config", mock_config):
            result = show_config(path_only=False)

        assert result == 0
        captured = capsys.readouterr()
        assert "Configuration" in captured.out

    def test_main_config_path_only(self, mock_config_file: Path, capsys):
        """Test config --path flag."""
        from src.cli import show_config

        mock_config = MagicMock()
        mock_config._config_path = mock_config_file

        with patch("src.core.config.config", mock_config):
            result = show_config(path_only=True)

        assert result == 0
        captured = capsys.readouterr()
        assert str(mock_config_file) in captured.out


class TestSearchCLI:
    """Tests for the search CLI."""

    def test_search_with_query(self):
        """Test search command with a query."""
        from src.cli import search

        with patch("src.cli.run_python_script") as mock_run:
            mock_run.return_value = 0
            result = search("test query")

        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert "test query" in args[1]
        assert result == 0

    def test_search_interactive_cancelled(self, capsys):
        """Test search without query (interactive mode) when cancelled."""
        from src.cli import search

        with patch("builtins.input", side_effect=KeyboardInterrupt):
            result = search(None)

        assert result == 0
        captured = capsys.readouterr()
        assert "Cancelled" in captured.out

    def test_search_interactive_empty(self, capsys):
        """Test search with empty input."""
        from src.cli import search

        with patch("builtins.input", return_value=""):
            result = search(None)

        assert result == 1
        captured = capsys.readouterr()
        assert "No query" in captured.out


class TestJumpCLI:
    """Tests for the jump CLI."""

    def test_jump_without_query(self):
        """Test jump command without initial query."""
        from src.cli import jump

        with patch("src.cli.run_shell_script") as mock_run:
            mock_run.return_value = 0
            result = jump(None)

        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert args[1] == []  # No arguments
        assert result == 0

    def test_jump_with_query(self):
        """Test jump command with initial query."""
        from src.cli import jump

        with patch("src.cli.run_shell_script") as mock_run:
            mock_run.return_value = 0
            result = jump("test")

        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert "test" in args[1]
        assert result == 0


class TestIngestCLI:
    """Tests for the ingest CLI."""

    def test_ingest_full(self):
        """Test ingest --full command."""
        from src.cli import ingest

        with patch("src.cli.run_python_script") as mock_run:
            mock_run.return_value = 0
            result = ingest(full=True, incremental=False)

        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert "--full" in args[1]
        assert result == 0

    def test_ingest_incremental(self):
        """Test ingest --incremental command."""
        from src.cli import ingest

        with patch("src.cli.run_python_script") as mock_run:
            mock_run.return_value = 0
            result = ingest(full=False, incremental=True)

        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert "--incremental" in args[1]
        assert result == 0


class TestHealthCLI:
    """Tests for the health CLI."""

    def test_health_default(self):
        """Test health command without options."""
        from src.cli import health

        with patch("src.cli.run_python_script") as mock_run:
            mock_run.return_value = 0
            result = health(json_output=False)

        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert "--json" not in args[1]
        assert result == 0

    def test_health_json(self):
        """Test health --json command."""
        from src.cli import health

        with patch("src.cli.run_python_script") as mock_run:
            mock_run.return_value = 0
            result = health(json_output=True)

        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert "--json" in args[1]
        assert result == 0


class TestBatchCLI:
    """Tests for the batch CLI."""

    def test_batch_moc(self):
        """Test batch moc command."""
        from src.cli import batch

        with patch("src.cli.run_python_script") as mock_run:
            mock_run.return_value = 0
            result = batch("moc", "/path/to/folder", title="Index")

        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert "moc" in args[1]
        assert "/path/to/folder" in args[1]
        assert "--title" in args[1]
        assert "Index" in args[1]
        assert result == 0

    def test_batch_add_tag(self):
        """Test batch add-tag command."""
        from src.cli import batch

        with patch("src.cli.run_python_script") as mock_run:
            mock_run.return_value = 0
            result = batch("add-tag", "/path/to/folder", tag="project")

        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert "add-tag" in args[1]
        assert "--tag" in args[1]
        assert "project" in args[1]
        assert result == 0


class TestSuggestCLI:
    """Tests for the suggest CLI."""

    def test_suggest(self):
        """Test suggest command."""
        from src.cli import suggest

        with patch("src.cli.run_python_script") as mock_run:
            mock_run.return_value = 0
            result = suggest("/path/to/file.md", limit=8)

        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert "/path/to/file.md" in args[1]
        assert result == 0


class TestCompareCLI:
    """Tests for the compare CLI."""

    def test_compare(self):
        """Test compare command."""
        from src.cli import compare

        with patch("src.cli.run_python_script") as mock_run:
            mock_run.return_value = 0
            result = compare("/path/to/file1.md", "/path/to/file2.md")

        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert "/path/to/file1.md" in args[1]
        assert "/path/to/file2.md" in args[1]
        assert result == 0


class TestCLIEntryPoints:
    """Tests for the CLI entry point functions."""

    def test_cli_main_entry(self):
        """Test cli_main entry point."""
        from src.cli import cli_main

        with patch("src.cli.main", return_value=0):
            with pytest.raises(SystemExit) as exc_info:
                cli_main()
            assert exc_info.value.code == 0

    def test_cli_search_entry(self):
        """Test cli_search entry point."""
        from src.cli import cli_search

        with patch("sys.argv", ["sage-search", "test"]):
            with patch("src.cli.search", return_value=0) as mock_search:
                with pytest.raises(SystemExit) as exc_info:
                    cli_search()
                mock_search.assert_called_once()
                assert exc_info.value.code == 0

    def test_cli_jump_entry(self):
        """Test cli_jump entry point."""
        from src.cli import cli_jump

        with patch("sys.argv", ["sage-jump"]):
            with patch("src.cli.jump", return_value=0) as mock_jump:
                with pytest.raises(SystemExit) as exc_info:
                    cli_jump()
                mock_jump.assert_called_once()
                assert exc_info.value.code == 0

    def test_cli_ingest_entry(self):
        """Test cli_ingest entry point."""
        from src.cli import cli_ingest

        with patch("sys.argv", ["sage-ingest", "--full"]):
            with patch("src.cli.ingest", return_value=0) as mock_ingest:
                with pytest.raises(SystemExit) as exc_info:
                    cli_ingest()
                mock_ingest.assert_called_once()
                assert exc_info.value.code == 0

    def test_cli_health_entry(self):
        """Test cli_health entry point."""
        from src.cli import cli_health

        with patch("sys.argv", ["sage-health"]):
            with patch("src.cli.health", return_value=0) as mock_health:
                with pytest.raises(SystemExit) as exc_info:
                    cli_health()
                mock_health.assert_called_once()
                assert exc_info.value.code == 0
