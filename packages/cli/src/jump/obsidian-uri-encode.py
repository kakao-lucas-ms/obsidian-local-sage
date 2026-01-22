#!/usr/bin/env python3
"""
Encode file path for Obsidian URI
Converts absolute path to vault-relative path and URL encodes it
"""

import sys
from pathlib import Path
from urllib.parse import quote

VAULT_PATH = "/Users/kakao/workspace/my-note/나의노트"

if len(sys.argv) < 2:
    sys.exit(1)

file_path = sys.argv[1]

try:
    # Convert to vault-relative path
    abs_path = Path(file_path)
    vault = Path(VAULT_PATH)
    rel_path = abs_path.relative_to(vault)

    # Convert to string and encode (keep slashes)
    encoded = quote(str(rel_path), safe="/")
    print(encoded, end="")  # No newline
except Exception:
    # Fallback: just encode as-is
    encoded = quote(file_path, safe="/")
    print(encoded, end="")
    sys.exit(0)
