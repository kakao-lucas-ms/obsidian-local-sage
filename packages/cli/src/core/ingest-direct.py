#!/usr/bin/env python3

"""
Direct Obsidian to Qdrant Ingestion
Bypasses n8n completely - reads files and uploads to Qdrant directly
"""

import re
import requests
import sqlite3
from pathlib import Path
from datetime import datetime
import hashlib

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
import sys

sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import config

# Configuration from config system
VAULT_PATH = str(config.vault_path)
OLLAMA_URL = f"{config.ollama_api_base}/api/embeddings"
QDRANT_URL = f"http://{config.qdrant_host}:{config.qdrant_port}/collections/{config.qdrant_collection}/points"
DB_PATH = str(config.db_path)
CHUNK_SIZE = config.get("advanced.chunk_size", 1000)
CHUNK_OVERLAP = config.get("advanced.chunk_overlap", 200)

# Folder categorization (can be overridden in config)
WORK_FOLDERS = config.get(
    "features.categorization.work_folders",
    [
        "working_log",
        "주간 스프린트",
        "프로젝트",
        "HR",
        "n8n",
        "발표-공유",
        "디자인시스템",
        "기술문서",
        "2025",
        "2026",
    ],
)
PERSONAL_FOLDERS = config.get(
    "features.categorization.personal_folders", ["개인", "아이디어", "Side Proj", "Study", "지식"]
)


def find_markdown_files(vault_path):
    """Find all markdown files"""
    vault = Path(vault_path)
    excluded_dirs = {".trash", ".git", "templates", ".obsidian"}

    md_files = []
    for md_file in vault.rglob("*.md"):
        if any(part in excluded_dirs for part in md_file.parts):
            continue
        md_files.append(md_file)

    return md_files


def categorize_file(file_path):
    """Determine if file is work or personal"""
    path_str = str(file_path)
    for folder in PERSONAL_FOLDERS:
        if f"/{folder}/" in path_str:
            return "personal"
    return "work"


def extract_obsidian_links(text):
    """Extract Obsidian internal links [[link]]"""
    # Pattern: [[link]] or [[link|display text]]
    pattern = r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]"
    links = re.findall(pattern, text)
    return list(set(links))  # Remove duplicates


def extract_frontmatter(content):
    """Extract YAML frontmatter"""
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}, content

    yaml_content = match.group(1)
    body = content[match.end() :].strip()

    # Simple YAML parser for tags, date, aliases
    frontmatter = {}
    current_key = None

    for line in yaml_content.split("\n"):
        line = line.strip()

        if line.startswith("tags:"):
            current_key = "tags"
            tags_str = line.replace("tags:", "").strip()
            if tags_str and tags_str != "[]":
                frontmatter["tags"] = [t.strip("[]") for t in tags_str.split(",") if t.strip()]
            else:
                frontmatter["tags"] = []

        elif line.startswith("aliases:"):
            current_key = "aliases"
            aliases_str = line.replace("aliases:", "").strip()
            if aliases_str and aliases_str != "[]":
                frontmatter["aliases"] = [
                    a.strip("[]\"'") for a in aliases_str.split(",") if a.strip()
                ]
            else:
                frontmatter["aliases"] = []

        elif line.startswith("date:"):
            current_key = "date"
            frontmatter["date"] = line.replace("date:", "").strip()

        elif line.startswith("  - ") or line.startswith("- "):
            # List item under current key
            item = line.replace("  - ", "").replace("- ", "").strip(" \"'")
            if current_key == "tags":
                if "tags" not in frontmatter:
                    frontmatter["tags"] = []
                frontmatter["tags"].append(item)
            elif current_key == "aliases":
                if "aliases" not in frontmatter:
                    frontmatter["aliases"] = []
                frontmatter["aliases"].append(item)

    return frontmatter, body


def semantic_chunk_text(text, max_chunk_size=CHUNK_SIZE):
    """
    Split text by Markdown headers while preserving context
    Returns: List of (header_path, chunk_text) tuples
    """
    header_pattern = r"^(#{1,6})\s+(.+)$"
    lines = text.split("\n")
    sections = []
    current_headers = ["", "", "", "", "", ""]
    current_content = []
    current_level = 0

    for line in lines:
        header_match = re.match(header_pattern, line)

        if header_match:
            if current_content:
                header_path = " > ".join([h for h in current_headers[:current_level] if h])
                content = "\n".join(current_content).strip()
                if content:
                    sections.append((header_path, content))

            level = len(header_match.group(1))
            title = header_match.group(2)
            current_headers[level - 1] = f"{'#' * level} {title}"
            for i in range(level, 6):
                current_headers[i] = ""
            current_level = level
            current_content = [line]
        else:
            current_content.append(line)

    if current_content:
        header_path = " > ".join([h for h in current_headers[:current_level] if h])
        content = "\n".join(current_content).strip()
        if content:
            sections.append((header_path, content))

    # Split large sections by paragraphs
    final_chunks = []
    for header_path, content in sections:
        if len(content) <= max_chunk_size:
            final_chunks.append((header_path, content))
        else:
            paragraphs = content.split("\n\n")
            current_chunk = []
            current_size = 0

            for para in paragraphs:
                para_size = len(para)
                if current_size + para_size > max_chunk_size and current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    final_chunks.append((header_path, chunk_text))
                    current_chunk = []
                    current_size = 0
                current_chunk.append(para)
                current_size += para_size

            if current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                final_chunks.append((header_path, chunk_text))

    return final_chunks


def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Legacy chunking - kept for compatibility"""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        start += size - overlap
    return chunks


def generate_embedding(text):
    """Generate embedding using Ollama"""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": config.ollama_model, "prompt": text},
            timeout=config.get("services.ollama.timeout", 30),
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as e:
        print(f"Embedding error: {e}")
        return None


def string_to_id(s):
    """Convert string to numeric ID"""
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)


def init_db():
    """Initialize database connection and ensure tables exist"""
    try:
        # Ensure db directory exists
        db_path = Path(DB_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(DB_PATH)
        # Execute schema if needed
        schema_path = PROJECT_ROOT / "db" / "schema.sql"
        if schema_path.exists():
            with open(schema_path, "r") as f:
                conn.executescript(f.read())
        return conn
    except Exception as e:
        print(f"Database initialization error: {e}")
        return None


def extract_title_from_content(content, file_name):
    """Extract document title from content or filename"""
    # Try to find first H1 header
    lines = content.split("\n")
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()

    # Fallback to filename without extension
    return file_name.replace(".md", "")


def index_document(conn, file_path, file_name, title, aliases, category, tags, modified_at):
    """Index document in SQLite for title search"""
    try:
        cursor = conn.cursor()

        # Convert aliases list to comma-separated string
        aliases_str = ", ".join(aliases) if aliases else ""
        tags_str = ", ".join(tags) if tags else ""

        cursor.execute(
            """
            INSERT OR REPLACE INTO document_index
            (file_path, file_name, title, aliases, category, tags, modified_at, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
            (str(file_path), file_name, title, aliases_str, category, tags_str, modified_at),
        )

        conn.commit()
        return True
    except Exception as e:
        print(f"Document indexing error: {e}")
        return False


def upsert_to_qdrant(chunk_id, vector, payload):
    """Upload vector to Qdrant"""
    try:
        response = requests.put(
            QDRANT_URL,
            json={"points": [{"id": string_to_id(chunk_id), "vector": vector, "payload": payload}]},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Qdrant error: {e}")
        return False


def process_file(file_path, db_conn=None):
    """Process single markdown file"""
    try:
        # Try UTF-8 first, fallback to other encodings
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="cp949") as f:
                    content = f.read()
            except Exception:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()

        if not content.strip():
            return 0

        # Extract metadata
        frontmatter, body_content = extract_frontmatter(content)
        category = categorize_file(file_path)
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        modified_at = mtime.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Extract title for indexing
        title = extract_title_from_content(content, file_path.name)
        aliases = frontmatter.get("aliases", [])
        tags = frontmatter.get("tags", [])

        # Index document in SQLite database
        if db_conn:
            index_document(
                db_conn, file_path, file_path.name, title, aliases, category, tags, modified_at
            )

        # Semantic chunking by headers
        chunks = semantic_chunk_text(body_content)

        # Process each chunk
        success_count = 0
        for i, (header_path, text_chunk) in enumerate(chunks):
            # Generate embedding
            embedding = generate_embedding(text_chunk)
            if embedding is None:
                continue

            # Extract Obsidian links from this chunk
            links = extract_obsidian_links(text_chunk)

            # Prepare payload
            chunk_id = f"{str(file_path).replace('/', '_')}_{i}"
            payload = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "category": category,
                "tags": frontmatter.get("tags", []),
                "aliases": frontmatter.get("aliases", []),
                "links": links,  # NEW: Obsidian internal links
                "date": frontmatter.get("date", modified_at.split("T")[0]),
                "modified_at": modified_at,
                "chunk_index": i,
                "header_path": header_path,  # NEW: semantic context
                "text": text_chunk,
            }

            # Upload to Qdrant
            if upsert_to_qdrant(chunk_id, embedding, payload):
                success_count += 1

        return success_count

    except Exception as e:
        print(f"Error processing {file_path.name}: {e}")
        return 0


def main():
    print("🧠 Obsidian to Qdrant Direct Ingestion")
    print("=" * 60)

    # Initialize database
    print("\n💾 Initializing document index database...")
    db_conn = init_db()
    if db_conn is None:
        print("⚠️  Warning: Database initialization failed. Document indexing will be skipped.")

    # Find files
    print("\n📁 Finding markdown files...")
    files = find_markdown_files(VAULT_PATH)
    total_files = len(files)
    print(f"Found {total_files} files")

    # Process all files
    print("\n🚀 Processing files...")
    total_chunks = 0
    processed_files = 0
    indexed_files = 0

    for i, file_path in enumerate(files, 1):
        chunks_uploaded = process_file(file_path, db_conn)
        if chunks_uploaded > 0:
            total_chunks += chunks_uploaded
            processed_files += 1
            indexed_files += 1

        if i % 10 == 0:
            print(
                f"Progress: {i}/{total_files} files ({total_chunks} chunks uploaded, {indexed_files} indexed)"
            )

    # Close database connection
    if db_conn:
        db_conn.close()

    print("\n✅ Ingestion Complete!")
    print(f"Files processed: {processed_files}/{total_files}")
    print(f"Total chunks uploaded to Qdrant: {total_chunks}")
    print(f"Documents indexed in database: {indexed_files}")


if __name__ == "__main__":
    main()
