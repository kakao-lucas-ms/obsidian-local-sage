#!/usr/bin/env python3
"""
Obsidian: Batch Document Processing
Process multiple documents at once with various operations
"""

import sys
import os
import sqlite3
from pathlib import Path
import argparse
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import config

# Use config values
DB_PATH = str(config.db_path)
VAULT_PATH = str(config.vault_path)

def get_documents_in_folder(folder_path, recursive=False):
    """Get all markdown documents in a folder"""
    folder = Path(folder_path)

    if not folder.exists():
        return []

    if recursive:
        return list(folder.rglob("*.md"))
    else:
        return list(folder.glob("*.md"))

def get_documents_by_tag(tag):
    """Get all documents with a specific tag"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT file_path, title
            FROM document_index
            WHERE tags LIKE ?
        """, (f"%{tag}%",))

        results = cursor.fetchall()
        conn.close()

        return [(Path(r[0]), r[1]) for r in results]
    except Exception as e:
        return []

def generate_folder_summary(docs):
    """Generate a summary of documents in a folder"""
    print("📊 폴더 요약")
    print("=" * 60)
    print()
    print(f"총 문서: {len(docs)}개")
    print()

    # Count by extension
    exts = {}
    for doc in docs:
        ext = doc.suffix
        exts[ext] = exts.get(ext, 0) + 1

    print("📄 파일 유형:")
    for ext, count in exts.items():
        print(f"   {ext}: {count}개")
    print()

    # Total size
    total_size = sum(doc.stat().st_size for doc in docs if doc.exists())
    print(f"💾 총 크기: {total_size / 1024:.1f} KB")
    print()

    # List documents
    print("📝 문서 목록:")
    for i, doc in enumerate(sorted(docs), 1):
        print(f"   {i}. {doc.stem}")
        if i >= 20:
            print(f"   ... +{len(docs) - 20}개 더")
            break

    print()

def generate_moc(docs, title="목차"):
    """Generate Map of Content (MOC) for documents"""
    print(f"# {title}")
    print()
    print(f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"문서 수: {len(docs)}개")
    print()
    print("---")
    print()

    # Group by subfolder
    by_folder = {}
    for doc in docs:
        if len(doc.parts) > 1:
            folder = doc.parts[-2]
        else:
            folder = "Root"

        if folder not in by_folder:
            by_folder[folder] = []
        by_folder[folder].append(doc)

    # Output by folder
    for folder in sorted(by_folder.keys()):
        docs_in_folder = sorted(by_folder[folder])

        print(f"## {folder}")
        print()

        for doc in docs_in_folder:
            # Create wikilink
            try:
                rel_path = doc.relative_to(VAULT_PATH)
                wikilink_path = str(rel_path).replace(".md", "")
                print(f"- [[{wikilink_path}|{doc.stem}]]")
            except:
                print(f"- [[{doc.stem}]]")

        print()

def add_tag_to_documents(docs, tag):
    """Add a tag to multiple documents"""
    print(f"🏷️  태그 추가: #{tag}")
    print()

    success = 0
    failed = 0

    for doc in docs:
        try:
            # Read document
            with open(doc, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if tag already exists
            if f"#{tag}" in content:
                print(f"⊘ {doc.name} - 이미 태그가 있음")
                continue

            # Add tag at the end of frontmatter or after title
            lines = content.split('\n')

            # Find where to add tag
            insert_idx = 0
            in_frontmatter = False

            for i, line in enumerate(lines):
                if i == 0 and line.strip() == '---':
                    in_frontmatter = True
                elif in_frontmatter and line.strip() == '---':
                    insert_idx = i + 1
                    break
                elif line.startswith('# '):
                    insert_idx = i + 1
                    break

            # Insert tag
            if insert_idx > 0:
                lines.insert(insert_idx, f"\n#{tag}\n")
            else:
                lines.insert(0, f"#{tag}\n")

            # Write back
            new_content = '\n'.join(lines)
            with open(doc, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print(f"✓ {doc.name}")
            success += 1

        except Exception as e:
            print(f"✗ {doc.name} - 오류: {e}")
            failed += 1

    print()
    print(f"완료: {success}개, 실패: {failed}개")

def check_broken_links(docs):
    """Check for broken links in documents"""
    print("🔗 깨진 링크 검사")
    print()

    import re

    total_links = 0
    broken_links = []

    for doc in docs:
        try:
            with open(doc, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find all wikilinks
            links = re.findall(r'\[\[([^\]|]+)', content)
            total_links += len(links)

            for link in links:
                # Check if target exists
                target_path = VAULT_PATH / f"{link}.md"
                if not target_path.exists():
                    broken_links.append((doc.name, link))

        except Exception as e:
            continue

    print(f"총 링크: {total_links}개")
    print(f"깨진 링크: {len(broken_links)}개")
    print()

    if broken_links:
        print("깨진 링크 목록:")
        for doc_name, link in broken_links[:20]:
            print(f"   {doc_name}: [[{link}]]")

        if len(broken_links) > 20:
            print(f"   ... +{len(broken_links) - 20}개 더")

def main():
    parser = argparse.ArgumentParser(description='Obsidian Batch Processing')
    parser.add_argument('operation', choices=['summary', 'moc', 'add-tag', 'check-links'],
                        help='Operation to perform')
    parser.add_argument('path', help='Folder path or tag (for tag-based operations)')
    parser.add_argument('--recursive', '-r', action='store_true',
                        help='Process subfolders recursively')
    parser.add_argument('--tag', help='Tag to add (for add-tag operation)')
    parser.add_argument('--title', default='목차', help='Title for MOC')

    args = parser.parse_args()

    # Get documents
    if args.path.startswith('#'):
        # Tag-based selection
        tag = args.path[1:]
        docs = get_documents_by_tag(tag)
        doc_paths = [d[0] for d in docs]
        print(f"🏷️  태그로 검색: #{tag}")
        print(f"   발견: {len(doc_paths)}개 문서")
        print()
    else:
        # Folder-based selection
        doc_paths = get_documents_in_folder(args.path, args.recursive)
        if not doc_paths:
            print(f"❌ 폴더에서 문서를 찾을 수 없습니다: {args.path}")
            sys.exit(1)

    # Perform operation
    if args.operation == 'summary':
        generate_folder_summary(doc_paths)

    elif args.operation == 'moc':
        generate_moc(doc_paths, args.title)

    elif args.operation == 'add-tag':
        if not args.tag:
            print("❌ --tag 옵션이 필요합니다")
            sys.exit(1)
        add_tag_to_documents(doc_paths, args.tag)

    elif args.operation == 'check-links':
        check_broken_links(doc_paths)

if __name__ == "__main__":
    main()
