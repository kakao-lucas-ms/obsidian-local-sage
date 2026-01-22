"""
Tests for the configuration system.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestConfig:
    """Tests for the Config class."""

    def test_config_singleton(self):
        """Test that Config is a singleton."""
        from src.core.config import Config

        config1 = Config()
        config2 = Config()
        assert config1 is config2

    def test_config_load_from_file(self, mock_config_file: Path):
        """Test loading configuration from a file."""
        from src.core.config import Config

        # Create a new instance (reset singleton for testing)
        config = Config.__new__(Config)
        config._config = {}
        config._config_path = None

        config.load(str(mock_config_file))

        assert config._config_path == mock_config_file
        assert config.get("vault.name") == "TestVault"
        assert config.get("services.ollama.model") == "bge-m3"

    def test_config_get_with_default(self, mock_config_file: Path):
        """Test getting config values with defaults."""
        from src.core.config import Config

        config = Config.__new__(Config)
        config._config = {}
        config._config_path = None
        config.load(str(mock_config_file))

        # Existing key
        assert config.get("services.qdrant.port") == 6333

        # Non-existing key with default
        assert config.get("nonexistent.key", "default") == "default"

        # Nested non-existing key
        assert config.get("services.nonexistent.setting", 42) == 42

    def test_config_vault_path_property(self, mock_config_file: Path, mock_vault: Path):
        """Test vault_path property."""
        from src.core.config import Config

        config = Config.__new__(Config)
        config._config = {}
        config._config_path = None
        config.load(str(mock_config_file))

        # vault_path should return a Path object
        assert isinstance(config.vault_path, Path)
        # Use resolve() to handle macOS /private symlink
        assert config.vault_path.resolve() == mock_vault.resolve()

    def test_config_db_path_property(self, mock_config_file: Path, temp_dir: Path):
        """Test db_path property."""
        from src.core.config import Config

        config = Config.__new__(Config)
        config._config = {}
        config._config_path = None
        config.load(str(mock_config_file))

        expected_db_path = temp_dir / "db" / "automation.db"
        # Use resolve() to handle macOS /private symlink
        assert config.db_path.resolve() == expected_db_path.resolve()

    def test_config_service_properties(self, mock_config_file: Path):
        """Test service-related properties."""
        from src.core.config import Config

        config = Config.__new__(Config)
        config._config = {}
        config._config_path = None
        config.load(str(mock_config_file))

        assert config.ollama_api_base == "http://127.0.0.1:11434"
        assert config.ollama_model == "bge-m3"
        assert config.qdrant_host == "127.0.0.1"
        assert config.qdrant_port == 6333
        assert config.qdrant_collection == "test_docs"

    def test_config_reload(self, mock_config_file: Path, temp_dir: Path):
        """Test config reload functionality."""
        from src.core.config import Config

        config = Config.__new__(Config)
        config._config = {}
        config._config_path = None
        config.load(str(mock_config_file))

        original_model = config.get("services.ollama.model")

        # Modify config file
        with open(mock_config_file, "r") as f:
            config_data = yaml.safe_load(f)

        config_data["services"]["ollama"]["model"] = "new-model"

        with open(mock_config_file, "w") as f:
            yaml.dump(config_data, f)

        # Reload
        config.reload()

        assert config.get("services.ollama.model") == "new-model"

    def test_config_not_found_error(self, temp_dir: Path):
        """Test that FileNotFoundError is raised when config not found."""
        from src.core.config import Config

        config = Config.__new__(Config)
        config._config = {}
        config._config_path = None

        with pytest.raises(FileNotFoundError):
            config.load(str(temp_dir / "nonexistent.yaml"))

    def test_config_debug_property(self, mock_config_file: Path):
        """Test debug property."""
        from src.core.config import Config

        config = Config.__new__(Config)
        config._config = {}
        config._config_path = None
        config.load(str(mock_config_file))

        # In mock config, debug is True
        assert config.debug is True


class TestConfigGet:
    """Tests for Config.get() method with various key formats."""

    def test_simple_key(self, mock_config_file: Path):
        """Test getting top-level keys."""
        from src.core.config import Config

        config = Config.__new__(Config)
        config._config = {"simple_key": "value"}
        config._config_path = None

        assert config.get("simple_key") == "value"

    def test_nested_key(self, mock_config_file: Path):
        """Test getting nested keys with dot notation."""
        from src.core.config import Config

        config = Config.__new__(Config)
        config._config = {
            "level1": {
                "level2": {
                    "level3": "deep_value"
                }
            }
        }
        config._config_path = None

        assert config.get("level1.level2.level3") == "deep_value"

    def test_missing_intermediate_key(self):
        """Test getting a key when intermediate key is missing."""
        from src.core.config import Config

        config = Config.__new__(Config)
        config._config = {"level1": {}}
        config._config_path = None

        assert config.get("level1.nonexistent.key", "default") == "default"

    def test_non_dict_intermediate(self):
        """Test getting a key when intermediate value is not a dict."""
        from src.core.config import Config

        config = Config.__new__(Config)
        config._config = {"level1": "string_value"}
        config._config_path = None

        assert config.get("level1.nested.key", "default") == "default"


class TestConfigRepr:
    """Tests for Config string representation."""

    def test_repr(self, mock_config_file: Path, mock_vault: Path, temp_dir: Path):
        """Test __repr__ method."""
        from src.core.config import Config

        config = Config.__new__(Config)
        config._config = {}
        config._config_path = None
        config.load(str(mock_config_file))

        repr_str = repr(config)
        assert "Config" in repr_str
        assert "vault=" in repr_str
        assert "db=" in repr_str
