#!/usr/bin/env python3
"""
Obsidian Wrapper: Search v4 (Save results as clickable note)
"""

import sys
import os
import sqlite3
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import config

# Use config values
DB_PATH = str(config.db_path)
VAULT_PATH = str(config.vault_path)
SEARCH_RESULTS_DIR = config.search_results_dir

def get_title_from_db(file_path):
    """Get actual title from SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT title FROM document_index
            WHERE file_path = ?
            LIMIT 1
        """, (file_path,))

        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            return result[0]

        return Path(file_path).stem

    except Exception as e:
        return Path(file_path).stem

def create_search_results_note(query, results):
    """Create a note with search results and clickable links"""
    # Create search results directory if it doesn't exist
    SEARCH_RESULTS_DIR.mkdir(exist_ok=True)

    # Create note filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    note_path = SEARCH_RESULTS_DIR / f"검색_{query}_{timestamp}.md"

    # Build note content
    content = f"""# 검색 결과: {query}

검색일시: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
결과 수: {len(results)}개

---

"""

    for i, r in enumerate(results, 1):
        payload = r.get("payload", {})
        file_path = payload.get("file_path", "")
        chunk = payload.get("chunk", "")
        score = r.get("score", 0)

        # Get actual title
        title = get_title_from_db(file_path)

        # Get relative path for wikilink
        try:
            rel_path = Path(file_path).relative_to(VAULT_PATH)
            # Remove .md extension for wikilink
            wikilink = str(rel_path).replace(".md", "")
        except:
            wikilink = Path(file_path).stem

        # Clean chunk
        clean_chunk = chunk.replace('\n', ' ').strip()
        if len(clean_chunk) > 200:
            clean_chunk = clean_chunk[:200] + "..."

        # Add result to note
        content += f"""## {i}. [[{wikilink}|{title}]]

**점수:** {score:.3f}

**내용 미리보기:**
> {clean_chunk}

---

"""

    # Write note
    with open(note_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return note_path

def main():
    if len(sys.argv) < 2:
        print("❌ 검색어를 입력하세요")
        sys.exit(0)

    query = " ".join(sys.argv[1:])

    if not query or query.strip() == "":
        print("❌ 빈 검색어")
        sys.exit(0)

    print(f"🔍 검색 중: {query}")

    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import requests

        # Get embedding
        emb_response = requests.post(
            f"{config.ollama_api_base}/api/embeddings",
            json={"model": config.ollama_model, "prompt": query},
            timeout=30
        )
        embedding = emb_response.json()["embedding"]

        # Search Qdrant
        qdrant_url = f"http://{config.qdrant_host}:{config.qdrant_port}/collections/{config.qdrant_collection}/points/search"
        search_response = requests.post(
            qdrant_url,
            json={"vector": embedding, "limit": 10, "with_payload": True},
            timeout=10
        )
        results = search_response.json()["result"]

        if not results:
            print("❌ 검색 결과 없음")
            sys.exit(0)

        # Create note with results
        note_path = create_search_results_note(query, results)

        # Get relative path for Obsidian URI
        rel_path = note_path.relative_to(VAULT_PATH)

        # URL encode
        import urllib.parse
        encoded = urllib.parse.quote(str(rel_path))
        vault_encoded = urllib.parse.quote(config.vault_name)

        uri = f"obsidian://open?vault={vault_encoded}&file={encoded}"

        # Print success message
        print(f"✅ {len(results)}개 결과를 찾았습니다!")
        print(f"📝 검색 결과 노트를 생성했습니다")
        print(f"\n{note_path.name}")
        print(f"\n💡 노트에서 [[링크]]를 클릭하면 해당 문서로 이동합니다")

        # Open the note
        os.system(f"open '{uri}'")

    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
