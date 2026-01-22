#!/usr/bin/env python3
"""
Central configuration management for Obsidian Local Sage
Loads settings from YAML and provides easy access to configuration values
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Singleton configuration manager"""

    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}
    _config_path: Optional[Path] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, config_path: Optional[str] = None) -> None:
        """
        Load configuration from YAML file

        Args:
            config_path: Path to config file. If None, searches standard locations.

        Raises:
            FileNotFoundError: If config file not found in any location
        """
        if config_path is None:
            # Try standard locations in order of preference
            locations = [
                # User-specific config
                Path.home() / ".obsidian-local-sage" / "config" / "settings.yaml",
                # Development config
                Path(__file__).parent.parent.parent / "config" / "settings.yaml",
                # Legacy location (for migration)
                Path.home() / ".config" / "obsidian-local-sage" / "settings.yaml"
            ]

            for loc in locations:
                if loc.exists():
                    config_path = str(loc)
                    break

        if config_path and Path(config_path).exists():
            self._config_path = Path(config_path)
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(
                "Config file not found. Please run install.sh or create config/settings.yaml"
            )

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation

        Args:
            key: Dot-separated key path (e.g., 'vault.path' or 'services.ollama.api_base')
            default: Default value if key not found

        Returns:
            Configuration value or default

        Examples:
            >>> config.get('vault.path')
            '/Users/username/Documents/MyVault'
            >>> config.get('services.qdrant.port', 6333)
            6333
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def reload(self) -> None:
        """Reload configuration from disk"""
        if self._config_path:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}

    # Convenience properties for commonly used paths

    @property
    def vault_path(self) -> Path:
        """Get Obsidian vault path as Path object"""
        path = self.get('vault.path', '~/Documents/Obsidian')
        return Path(path).expanduser().resolve()

    @property
    def vault_name(self) -> str:
        """Get Obsidian vault name"""
        return self.get('vault.name', self.vault_path.name)

    @property
    def db_path(self) -> Path:
        """Get database path as Path object"""
        path = self.get('project.db_path', '~/.obsidian-local-sage/db/automation.db')
        return Path(path).expanduser().resolve()

    @property
    def project_root(self) -> Path:
        """Get project root directory as Path object"""
        path = self.get('project.root', '~/.obsidian-local-sage')
        return Path(path).expanduser().resolve()

    @property
    def search_results_dir(self) -> Path:
        """Get search results directory (relative to vault)"""
        dir_name = self.get('project.search_results_dir', '검색결과')
        return self.vault_path / dir_name

    @property
    def log_path(self) -> Path:
        """Get log directory path"""
        path = self.get('advanced.log_path', '~/.obsidian-local-sage/logs')
        log_dir = Path(path).expanduser().resolve()
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    # Service connection properties

    @property
    def ollama_api_base(self) -> str:
        """Get Ollama API base URL"""
        return self.get('services.ollama.api_base', 'http://127.0.0.1:11434')

    @property
    def ollama_model(self) -> str:
        """Get Ollama model name"""
        return self.get('services.ollama.model', 'bge-m3')

    @property
    def qdrant_host(self) -> str:
        """Get Qdrant host"""
        return self.get('services.qdrant.host', '127.0.0.1')

    @property
    def qdrant_port(self) -> int:
        """Get Qdrant port"""
        return self.get('services.qdrant.port', 6333)

    @property
    def qdrant_collection(self) -> str:
        """Get Qdrant collection name"""
        return self.get('services.qdrant.collection', 'obsidian_docs')

    # Feature flags

    @property
    def debug(self) -> bool:
        """Check if debug mode is enabled"""
        return self.get('advanced.debug', False)

    def __repr__(self) -> str:
        return f"Config(vault={self.vault_path}, db={self.db_path})"


# Global singleton instance
config = Config()


def get_config() -> Config:
    """
    Get the global configuration instance

    Returns:
        Global Config instance

    Example:
        >>> from src.core.config import get_config
        >>> cfg = get_config()
        >>> print(cfg.vault_path)
    """
    return config


# Auto-load config if available (for convenience)
try:
    config.load()
except FileNotFoundError:
    # Config will need to be loaded explicitly
    pass


if __name__ == '__main__':
    # Test configuration loading
    try:
        config.load()
        print(f"✅ Config loaded successfully")
        print(f"Vault: {config.vault_path}")
        print(f"Database: {config.db_path}")
        print(f"Ollama: {config.ollama_api_base}")
        print(f"Qdrant: {config.qdrant_host}:{config.qdrant_port}")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("Please create config/settings.yaml based on config/settings.example.yaml")
