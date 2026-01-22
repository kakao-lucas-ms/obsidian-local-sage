#!/usr/bin/env python3
"""
Obsidian Wrapper: Simple Text Search (for notifications)
Returns top search results in clean text format
"""

import sys
from pathlib import Path
import pickle
import requests

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import config

# Try to import rank_bm25, handle if not installed
try:

    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

# Configuration from config system
QDRANT_URL = f"http://{config.qdrant_host}:{config.qdrant_port}"
COLLECTION_NAME = config.qdrant_collection
OLLAMA_URL = f"{config.ollama_api_base}/api/embeddings"
EMBEDDING_MODEL = config.ollama_model
BM25_INDEX_PATH = Path.home() / ".cache" / "obsidian-search" / "bm25_index.pkl"
BM25_DOCS_PATH = Path.home() / ".cache" / "obsidian-search" / "bm25_docs.pkl"
VAULT_PATH = str(config.vault_path)

# Search weights from config
RRF_K = 60
VECTOR_WEIGHT = config.get("features.search.vector_weight", 0.6)
BM25_WEIGHT = config.get("features.search.fts_weight", 0.4)


def get_embedding(text):
    """Get embedding from Ollama"""
    try:
        response = requests.post(
            OLLAMA_URL, json={"model": EMBEDDING_MODEL, "prompt": text}, timeout=30
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as e:
        print(f"❌ Embedding error: {e}", file=sys.stderr)
        return None


def vector_search(query, limit=10):
    """Search using Qdrant vector database"""
    embedding = get_embedding(query)
    if not embedding:
        return []

    try:
        response = requests.post(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search",
            json={"vector": embedding, "limit": limit, "with_payload": True},
            timeout=10,
        )
        response.raise_for_status()
        results = response.json()["result"]

        # Format results
        formatted = []
        for i, r in enumerate(results):
            payload = r.get("payload", {})
            formatted.append(
                {
                    "file_path": payload.get("file_path", ""),
                    "title": payload.get("title", "Unknown"),
                    "content": payload.get("chunk", ""),
                    "score": r.get("score", 0),
                    "rank": i + 1,
                }
            )
        return formatted
    except Exception as e:
        print(f"❌ Vector search error: {e}", file=sys.stderr)
        return []


def bm25_search(query, limit=10):
    """Search using BM25 keyword search"""
    if not HAS_BM25:
        print("❌ rank_bm25 not installed. Run: pip install rank-bm25", file=sys.stderr)
        return []

    try:
        if not BM25_INDEX_PATH.exists() or not BM25_DOCS_PATH.exists():
            print("❌ BM25 index not found. Run: sage-ingest to build index", file=sys.stderr)
            return []

        with open(BM25_INDEX_PATH, "rb") as f:
            bm25 = pickle.load(f)
        with open(BM25_DOCS_PATH, "rb") as f:
            docs = pickle.load(f)

        # Tokenize query
        query_tokens = query.lower().split()

        # Get scores
        scores = bm25.get_scores(query_tokens)

        # Get top results
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit]

        formatted = []
        for rank, idx in enumerate(top_indices):
            doc = docs[idx]
            formatted.append(
                {
                    "file_path": doc.get("file_path", ""),
                    "title": doc.get("title", "Unknown"),
                    "content": doc.get("content", ""),
                    "score": scores[idx],
                    "rank": rank + 1,
                }
            )
        return formatted
    except Exception as e:
        print(f"❌ BM25 search error: {e}", file=sys.stderr)
        return []


def rrf_fusion(vector_results, bm25_results):
    """Reciprocal Rank Fusion to combine results"""
    scores = {}

    # Add vector scores
    for r in vector_results:
        key = r["file_path"]
        scores[key] = scores.get(key, 0) + VECTOR_WEIGHT / (RRF_K + r["rank"])

    # Add BM25 scores
    for r in bm25_results:
        key = r["file_path"]
        scores[key] = scores.get(key, 0) + BM25_WEIGHT / (RRF_K + r["rank"])

    # Sort by combined score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Merge results
    file_map = {}
    for r in vector_results + bm25_results:
        key = r["file_path"]
        if key not in file_map:
            file_map[key] = r

    final = []
    for file_path, score in ranked[:10]:
        if file_path in file_map:
            result = file_map[file_path].copy()
            result["final_score"] = score
            final.append(result)

    return final


def format_result(result, index):
    """Format a single result for display"""
    title = result.get("title", "Unknown")
    file_path = result.get("file_path", "")
    content = result.get("content", "")[:150]

    # Get relative path from vault
    try:
        rel_path = Path(file_path).relative_to(VAULT_PATH)
    except Exception:
        rel_path = Path(file_path).name

    return f"{index}. {title}\n   📂 {rel_path}\n   {content}...\n"


def main():
    if len(sys.argv) < 2:
        print("Usage: obsidian-wrapper-search.py <query>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    # Perform hybrid search
    print(f"🔍 Searching for: {query}\n")

    vector_results = vector_search(query, limit=20)
    bm25_results = bm25_search(query, limit=20)

    if not vector_results and not bm25_results:
        print("❌ No results found")
        sys.exit(1)

    # Combine results
    final_results = rrf_fusion(vector_results, bm25_results)

    if not final_results:
        print("❌ No results after fusion")
        sys.exit(1)

    # Print results
    print(f"Found {len(final_results)} results:\n")
    for i, result in enumerate(final_results, 1):
        print(format_result(result, i))


if __name__ == "__main__":
    main()
