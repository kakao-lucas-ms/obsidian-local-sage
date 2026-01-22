#!/usr/bin/env python3
"""
Obsidian: AI-Powered Link Suggestions
Analyzes current document and suggests related documents to link
"""

import sys
import os
import sqlite3
import requests
from pathlib import Path
from collections import defaultdict

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import config

# Use config values
DB_PATH = str(config.db_path)
VAULT_PATH = str(config.vault_path)
OLLAMA_URL = f"{config.ollama_api_base}/api/embeddings"
QDRANT_URL = f"http://{config.qdrant_host}:{config.qdrant_port}/collections/{config.qdrant_collection}/points/search"


def get_document_info(file_path):
    """Get document metadata from SQLite"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT title, category, tags, aliases
            FROM document_index
            WHERE file_path = ?
            LIMIT 1
        """,
            (file_path,),
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "title": result[0] or Path(file_path).stem,
                "category": result[1],
                "tags": result[2],
                "aliases": result[3],
            }
        return None
    except Exception:
        return None


def extract_key_phrases(file_path):
    """Extract key phrases from document for search"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract first paragraph (usually most important)
        lines = [
            line.strip()
            for line in content.split("\n")
            if line.strip() and not line.startswith("#")
        ]
        first_para = lines[0] if lines else ""

        # Extract headings
        headings = [
            line.strip("#").strip() for line in content.split("\n") if line.startswith("##")
        ]

        # Combine for context
        context = f"{first_para} {' '.join(headings[:3])}"
        return context[:500]  # Limit length

    except Exception:
        return ""


def find_similar_documents(file_path, limit=10):
    """Find semantically similar documents"""
    try:
        # Get content for embedding
        context = extract_key_phrases(file_path)
        if not context:
            return []

        # Get embedding from Ollama
        emb_response = requests.post(
            OLLAMA_URL,
            json={"model": config.ollama_model, "prompt": context},
            timeout=config.get("services.ollama.timeout", 30),
        )
        embedding = emb_response.json()["embedding"]

        # Search Qdrant
        search_response = requests.post(
            QDRANT_URL,
            json={
                "vector": embedding,
                "limit": limit + 5,  # Get extra to filter out current doc
                "with_payload": True,
            },
            timeout=10,
        )
        results = search_response.json()["result"]

        # Filter out current document
        filtered = []
        current_stem = Path(file_path).stem

        for r in results:
            result_path = r.get("payload", {}).get("file_path", "")
            if result_path and Path(result_path).stem != current_stem:
                filtered.append(r)
                if len(filtered) >= limit:
                    break

        return filtered

    except Exception as e:
        print(f"⚠️  Error finding similar documents: {e}")
        return []


def group_by_document(results):
    """Group chunks by document"""
    docs = defaultdict(lambda: {"score": 0, "chunks": [], "path": ""})

    for r in results:
        payload = r.get("payload", {})
        file_path = payload.get("file_path", "")
        chunk = payload.get("chunk", "")
        score = r.get("score", 0)

        if file_path:
            docs[file_path]["score"] = max(docs[file_path]["score"], score)
            docs[file_path]["chunks"].append(chunk)
            docs[file_path]["path"] = file_path

    # Sort by score
    sorted_docs = sorted(docs.items(), key=lambda x: x[1]["score"], reverse=True)
    return sorted_docs


def get_wikilink(file_path, title):
    """Generate wikilink for a document"""
    try:
        rel_path = Path(file_path).relative_to(VAULT_PATH)
        wikilink_path = str(rel_path).replace(".md", "")
        return f"[[{wikilink_path}|{title}]]"
    except Exception:
        return f"[[{Path(file_path).stem}|{title}]]"


def main():
    if len(sys.argv) < 2:
        print("❌ 파일 경로가 필요합니다")
        print("Usage: obsidian-suggest-links.py <file_path>")
        sys.exit(1)

    file_path = " ".join(sys.argv[1:])

    # Unescape if needed
    if "\\/" in file_path:
        file_path = file_path.replace("\\/", "/")
        file_path = file_path.replace("\\-", "-")
        file_path = file_path.replace("\\ ", " ")

    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        sys.exit(1)

    # Get document info
    doc_info = get_document_info(file_path)
    if not doc_info:
        doc_info = {"title": Path(file_path).stem}

    print(f"🔗 링크 제안: {doc_info['title']}")
    print()
    print("🔍 관련 문서를 찾고 있습니다...")

    # Find similar documents
    results = find_similar_documents(file_path, limit=10)

    if not results:
        print()
        print("❌ 관련 문서를 찾지 못했습니다")
        sys.exit(0)

    # Group by document
    grouped = group_by_document(results)

    print()
    print(f"✅ {len(grouped)}개의 관련 문서를 찾았습니다!")
    print()
    print("=" * 60)

    # Show suggestions
    for i, (doc_path, data) in enumerate(grouped[:8], 1):
        # Get title from DB
        info = get_document_info(doc_path)
        title = info["title"] if info else Path(doc_path).stem

        score = data["score"]
        chunks = data["chunks"]

        # Generate wikilink
        wikilink = get_wikilink(doc_path, title)

        print()
        print(f"{i}. {title}")
        print(f"   점수: {score:.3f}")
        print(f"   링크: {wikilink}")

        # Show snippet
        if chunks:
            snippet = chunks[0].replace("\n", " ").strip()
            if len(snippet) > 100:
                snippet = snippet[:100] + "..."
            print(f"   내용: {snippet}")

        print()

    print("=" * 60)
    print()
    print("💡 위 링크를 복사해서 문서에 추가하세요")
    print("   예: '이 내용은 [[다른문서|다른 문서]]와 관련이 있습니다'")


if __name__ == "__main__":
    main()
