#!/usr/bin/env python3
"""
Obsidian Wrapper: Search v2 (Fixed escaping)
"""

import sys
import os
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import config


# Unescape backslashes from Obsidian
def unescape_text(text):
    """Remove backslash escaping added by Obsidian"""
    # Replace \x with x for all characters
    result = ""
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            # Skip the backslash, keep the next char
            result += text[i + 1]
            i += 2
        else:
            result += text[i]
            i += 1
    return result


def main():
    if len(sys.argv) < 2:
        print("❌ No search query")
        sys.exit(0)

    # Get query and unescape
    query = " ".join(sys.argv[1:])
    query = unescape_text(query)

    if not query or query.strip() == "":
        print("❌ Empty query")
        sys.exit(0)

    print(f"🔍 검색: {query}\n")

    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import requests

        # Quick Qdrant search
        # Get embedding
        emb_response = requests.post(
            f"{config.ollama_api_base}/api/embeddings",
            json={"model": config.ollama_model, "prompt": query},
            timeout=30,
        )
        embedding = emb_response.json()["embedding"]

        # Search
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
            title = payload.get("title", "Unknown")
            file_path = payload.get("file_path", "")
            chunk = payload.get("chunk", "")[:100]
            score = r.get("score", 0)

            # Get relative path
            try:
                rel_path = Path(file_path).relative_to(config.vault_path)
            except Exception:
                rel_path = Path(file_path).name

            print(f"{i}. {title}")
            print(f"   📂 {rel_path}")
            print(f"   📊 점수: {score:.3f}")
            print(f"   {chunk}...")
            print()

    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
