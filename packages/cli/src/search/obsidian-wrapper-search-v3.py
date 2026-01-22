#!/usr/bin/env python3
"""
Obsidian Wrapper: Search v3 (Fixed title lookup from SQLite)
"""

import sys
import os
import sqlite3
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import config

# Use config values
DB_PATH = str(config.db_path)
VAULT_PATH = str(config.vault_path)


def get_title_from_db(file_path):
    """Get actual title from SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT title FROM document_index
            WHERE file_path = ?
            LIMIT 1
        """,
            (file_path,),
        )

        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            return result[0]

        # Fallback to filename
        return Path(file_path).stem

    except Exception as e:
        print(f"DB lookup error: {e}", file=sys.stderr)
        return Path(file_path).stem


def create_obsidian_uri(file_path):
    """Create Obsidian URI for opening the file"""
    try:
        # Get relative path from vault
        rel_path = Path(file_path).relative_to(VAULT_PATH)

        # URL encode
        import urllib.parse

        encoded = urllib.parse.quote(str(rel_path))

        # Vault name encoding
        vault_encoded = urllib.parse.quote(config.vault_name)

        return f"obsidian://open?vault={vault_encoded}&file={encoded}"
    except Exception:
        return None


def main():
    if len(sys.argv) < 2:
        print("❌ 검색어를 입력하세요")
        sys.exit(0)

    query = " ".join(sys.argv[1:])

    if not query or query.strip() == "":
        print("❌ 빈 검색어")
        sys.exit(0)

    print(f"🔍 검색: {query}\n")

    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import requests

        # Get embedding
        emb_response = requests.post(
            f"{config.ollama_api_base}/api/embeddings",
            json={"model": config.ollama_model, "prompt": query},
            timeout=30,
        )
        embedding = emb_response.json()["embedding"]

        # Search Qdrant
        qdrant_url = f"http://{config.qdrant_host}:{config.qdrant_port}/collections/{config.qdrant_collection}/points/search"
        search_response = requests.post(
            qdrant_url, json={"vector": embedding, "limit": 5, "with_payload": True}, timeout=10
        )
        results = search_response.json()["result"]

        if not results:
            print("❌ 검색 결과 없음")
            sys.exit(0)

        print(f"✅ {len(results)}개 결과:\n")

        for i, r in enumerate(results, 1):
            payload = r.get("payload", {})
            file_path = payload.get("file_path", "")
            chunk = payload.get("chunk", "")
            score = r.get("score", 0)

            # Get actual title from database
            title = get_title_from_db(file_path)

            # Get relative path
            try:
                rel_path = Path(file_path).relative_to(VAULT_PATH)
            except Exception:
                rel_path = Path(file_path).name

            # Get Obsidian URI
            uri = create_obsidian_uri(file_path)

            # Display result
            print(f"{i}. {title}")
            print(f"   📂 {rel_path}")
            print(f"   📊 점수: {score:.3f}")

            # Show more content
            if chunk:
                # Clean and truncate chunk
                clean_chunk = chunk.replace("\n", " ").strip()
                if len(clean_chunk) > 200:
                    clean_chunk = clean_chunk[:200] + "..."
                print(f"   💬 {clean_chunk}")

            if uri:
                print(f"   🔗 {uri}")

            print()

    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
