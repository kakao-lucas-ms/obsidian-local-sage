#!/usr/bin/env python3
"""
Obsidian Local Sage - CLI Entry Points

This module provides command-line interface entry points for the obsidian-local-sage package.
These functions are registered as console scripts in pyproject.toml.
"""

import sys
import argparse
import subprocess
from pathlib import Path
from typing import Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_script_path(module: str, script: str) -> Path:
    """Get the full path to a script file."""
    return PROJECT_ROOT / "src" / module / script


def run_python_script(script_path: Path, args: list) -> int:
    """Run a Python script and return the exit code."""
    if not script_path.exists():
        print(f"Error: Script not found: {script_path}", file=sys.stderr)
        return 1

    cmd = [sys.executable, str(script_path)] + args
    return subprocess.call(cmd)


def run_shell_script(script_path: Path, args: list) -> int:
    """Run a shell script and return the exit code."""
    if not script_path.exists():
        print(f"Error: Script not found: {script_path}", file=sys.stderr)
        return 1

    cmd = ["bash", str(script_path)] + args
    return subprocess.call(cmd)


def main() -> int:
    """
    Main CLI entry point for obsidian-sage command.

    Usage:
        obsidian-sage <command> [options]

    Commands:
        search   - AI-powered semantic search
        jump     - Interactive document jump
        ingest   - Build/rebuild search index
        health   - Vault health check
        suggest  - AI link suggestions
        compare  - Document comparison
        batch    - Batch operations
        config   - Show configuration
    """
    parser = argparse.ArgumentParser(
        prog="obsidian-sage",
        description="AI-powered local tools for Obsidian",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  obsidian-sage search "machine learning"    Search for documents
  obsidian-sage jump                         Interactive document jump
  obsidian-sage ingest --full                Rebuild entire index
  obsidian-sage health                       Run vault health check
  obsidian-sage config                       Show current configuration
        """
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version="%(prog)s 0.1.0"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Search command
    search_parser = subparsers.add_parser("search", help="AI-powered semantic search")
    search_parser.add_argument("query", nargs="?", help="Search query")
    search_parser.add_argument("--limit", "-l", type=int, default=8, help="Max results")
    search_parser.add_argument("--no-create-note", action="store_true", help="Don't create result note")

    # Jump command
    jump_parser = subparsers.add_parser("jump", help="Interactive document jump")
    jump_parser.add_argument("query", nargs="?", help="Initial search query")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Build/rebuild search index")
    ingest_parser.add_argument("--full", action="store_true", help="Full rebuild")
    ingest_parser.add_argument("--incremental", action="store_true", help="Incremental update")

    # Health command
    health_parser = subparsers.add_parser("health", help="Vault health check")
    health_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Suggest command
    suggest_parser = subparsers.add_parser("suggest", help="AI link suggestions")
    suggest_parser.add_argument("file", help="Path to document")
    suggest_parser.add_argument("--limit", "-l", type=int, default=8, help="Max suggestions")

    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two documents")
    compare_parser.add_argument("file1", help="First document path")
    compare_parser.add_argument("file2", help="Second document path")

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Batch operations")
    batch_parser.add_argument("operation", choices=["summary", "moc", "add-tag", "check-links"],
                              help="Batch operation type")
    batch_parser.add_argument("folder", help="Target folder path")
    batch_parser.add_argument("--tag", help="Tag to add (for add-tag)")
    batch_parser.add_argument("--title", help="Title (for moc)")

    # Config command
    config_parser = subparsers.add_parser("config", help="Show configuration")
    config_parser.add_argument("--path", action="store_true", help="Show config file path only")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Route to appropriate handler
    if args.command == "search":
        return search(args.query, args.limit, not args.no_create_note)
    elif args.command == "jump":
        return jump(args.query)
    elif args.command == "ingest":
        return ingest(full=args.full, incremental=args.incremental)
    elif args.command == "health":
        return health(json_output=args.json)
    elif args.command == "suggest":
        return suggest(args.file, args.limit)
    elif args.command == "compare":
        return compare(args.file1, args.file2)
    elif args.command == "batch":
        return batch(args.operation, args.folder, tag=args.tag, title=args.title)
    elif args.command == "config":
        return show_config(path_only=args.path)

    return 0


def search(query: Optional[str] = None, limit: int = 8, create_note: bool = True) -> int:
    """
    Run AI-powered semantic search.

    Entry point: sage-search
    """
    if query is None:
        # Interactive mode - prompt for query
        try:
            query = input("Enter search query: ").strip()
            if not query:
                print("No query provided.")
                return 1
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return 0

    script_path = get_script_path("search", "obsidian-wrapper-search-v4.py")
    args = [query]

    return run_python_script(script_path, args)


def jump(query: Optional[str] = None) -> int:
    """
    Run interactive document jump with fzf.

    Entry point: sage-jump
    """
    script_path = get_script_path("jump", "obsidian-jump-fixed.sh")
    args = [query] if query else []

    return run_shell_script(script_path, args)


def ingest(full: bool = False, incremental: bool = False) -> int:
    """
    Build or update the search index.

    Entry point: sage-ingest
    """
    script_path = get_script_path("core", "ingest-direct.py")
    args = []

    if full:
        args.append("--full")
    elif incremental:
        args.append("--incremental")

    return run_python_script(script_path, args)


def health(json_output: bool = False) -> int:
    """
    Run vault health check.

    Entry point: sage-health
    """
    script_path = get_script_path("health", "obsidian-health-check.py")
    args = []

    if json_output:
        args.append("--json")

    return run_python_script(script_path, args)


def suggest(file_path: str, limit: int = 8) -> int:
    """
    Get AI-powered link suggestions for a document.
    """
    script_path = get_script_path("analysis", "obsidian-suggest-links.py")
    args = [file_path]

    return run_python_script(script_path, args)


def compare(file1: str, file2: str) -> int:
    """
    Compare two documents.
    """
    script_path = get_script_path("analysis", "obsidian-compare-docs.py")
    args = [file1, file2]

    return run_python_script(script_path, args)


def batch(operation: str, folder: str, tag: Optional[str] = None, title: Optional[str] = None) -> int:
    """
    Run batch operations on a folder.
    """
    script_path = get_script_path("batch", "obsidian-batch-process.py")
    args = [operation, folder]

    if tag:
        args.extend(["--tag", tag])
    if title:
        args.extend(["--title", title])

    return run_python_script(script_path, args)


def show_config(path_only: bool = False) -> int:
    """
    Show current configuration.
    """
    try:
        from src.core.config import config

        if path_only:
            if config._config_path:
                print(config._config_path)
            else:
                print("Config not loaded")
            return 0

        print("=" * 60)
        print("Obsidian Local Sage Configuration")
        print("=" * 60)
        print(f"\nConfig file: {config._config_path or 'Not loaded'}")
        print(f"\nVault:")
        print(f"  Path: {config.vault_path}")
        print(f"  Name: {config.vault_name}")
        print(f"\nProject:")
        print(f"  Root: {config.project_root}")
        print(f"  Database: {config.db_path}")
        print(f"  Logs: {config.log_path}")
        print(f"\nServices:")
        print(f"  Ollama: {config.ollama_api_base} (model: {config.ollama_model})")
        print(f"  Qdrant: {config.qdrant_host}:{config.qdrant_port} (collection: {config.qdrant_collection})")
        print(f"\nDebug: {config.debug}")
        print("")

        return 0

    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        return 1


# CLI entry points for pyproject.toml

def cli_main() -> None:
    """Entry point for obsidian-sage command."""
    sys.exit(main())


def cli_search() -> None:
    """Entry point for sage-search command."""
    parser = argparse.ArgumentParser(
        prog="sage-search",
        description="AI-powered semantic search for Obsidian"
    )
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--limit", "-l", type=int, default=8, help="Max results")

    args = parser.parse_args()
    sys.exit(search(args.query, args.limit))


def cli_jump() -> None:
    """Entry point for sage-jump command."""
    parser = argparse.ArgumentParser(
        prog="sage-jump",
        description="Interactive document jump with fuzzy search"
    )
    parser.add_argument("query", nargs="?", help="Initial search query")

    args = parser.parse_args()
    sys.exit(jump(args.query))


def cli_ingest() -> None:
    """Entry point for sage-ingest command."""
    parser = argparse.ArgumentParser(
        prog="sage-ingest",
        description="Build or update the search index"
    )
    parser.add_argument("--full", action="store_true", help="Full rebuild")
    parser.add_argument("--incremental", action="store_true", help="Incremental update")

    args = parser.parse_args()
    sys.exit(ingest(full=args.full, incremental=args.incremental))


def cli_health() -> None:
    """Entry point for sage-health command."""
    parser = argparse.ArgumentParser(
        prog="sage-health",
        description="Vault health check"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    sys.exit(health(json_output=args.json))


if __name__ == "__main__":
    cli_main()
