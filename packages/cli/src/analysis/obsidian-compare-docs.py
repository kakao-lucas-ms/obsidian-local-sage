#!/usr/bin/env python3
"""
Obsidian: Document Comparison Tool
Compares two documents and shows similarities/differences
"""

import sys
import os
import requests
import difflib
from pathlib import Path
from collections import Counter
import re

OLLAMA_URL = "http://127.0.0.1:11434/api/embeddings"


def read_document(file_path):
    """Read document content"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def extract_metadata(content):
    """Extract metadata from document"""
    lines = content.split("\n")

    # Title (first h1)
    title = None
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # Headings
    headings = []
    for line in lines:
        if line.startswith("##"):
            h = line.lstrip("#").strip()
            if h:
                headings.append(h)

    # Tags
    tags = re.findall(r"#(\w+)", content)

    # Links
    links = re.findall(r"\[\[([^\]]+)\]\]", content)

    # Word count
    words = len(content.split())

    return {
        "title": title or "Untitled",
        "headings": headings,
        "tags": list(set(tags)),
        "links": list(set(links)),
        "word_count": words,
        "lines": len(lines),
    }


def get_embedding(text):
    """Get embedding for text"""
    try:
        response = requests.post(
            OLLAMA_URL, json={"model": "bge-m3", "prompt": text[:2000]}, timeout=30  # Limit length
        )
        return response.json()["embedding"]
    except Exception:
        return None


def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity"""
    if not vec1 or not vec2:
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def extract_key_phrases(content):
    """Extract key phrases (simple word frequency)"""
    # Remove markdown syntax
    text = re.sub(r"[#*`\[\]()]", "", content)
    words = text.lower().split()

    # Filter stop words (simple)
    stop_words = {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "as",
        "is",
        "was",
        "are",
        "were",
        "be",
        "been",
        "being",
        "이",
        "그",
        "저",
        "것",
        "수",
        "등",
        "및",
    }

    filtered = [w for w in words if len(w) > 2 and w not in stop_words]

    # Count frequency
    counter = Counter(filtered)
    return counter.most_common(15)


def compare_content(content1, content2):
    """Compare content using difflib"""
    lines1 = content1.split("\n")
    lines2 = content2.split("\n")

    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    ratio = matcher.ratio()

    # Find common lines
    common = []
    for block in matcher.get_matching_blocks():
        if block.size > 0:
            common.extend(lines1[block.a : block.a + block.size])

    return {
        "similarity_ratio": ratio,
        "common_lines": len(common),
        "total_lines": max(len(lines1), len(lines2)),
    }


def main():
    if len(sys.argv) < 3:
        print("❌ 두 개의 파일 경로가 필요합니다")
        print("Usage: obsidian-compare-docs.py <file1> <file2>")
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]

    # Unescape paths if needed
    for i, f in enumerate([file1, file2]):
        if "\\/" in f:
            f = f.replace("\\/", "/")
            f = f.replace("\\-", "-")
            f = f.replace("\\ ", " ")
            if i == 0:
                file1 = f
            else:
                file2 = f

    # Check files exist
    if not os.path.exists(file1):
        print(f"❌ 파일을 찾을 수 없습니다: {file1}")
        sys.exit(1)

    if not os.path.exists(file2):
        print(f"❌ 파일을 찾을 수 없습니다: {file2}")
        sys.exit(1)

    # Read documents
    content1 = read_document(file1)
    content2 = read_document(file2)

    if not content1 or not content2:
        print("❌ 파일을 읽을 수 없습니다")
        sys.exit(1)

    print("📊 문서 비교 분석")
    print("=" * 60)
    print()

    # Extract metadata
    meta1 = extract_metadata(content1)
    meta2 = extract_metadata(content2)

    print(f"📄 문서 1: {meta1['title']}")
    print(f"   단어: {meta1['word_count']}, 줄: {meta1['lines']}")
    print(
        f"   헤딩: {len(meta1['headings'])}, 태그: {len(meta1['tags'])}, 링크: {len(meta1['links'])}"
    )
    print()

    print(f"📄 문서 2: {meta2['title']}")
    print(f"   단어: {meta2['word_count']}, 줄: {meta2['lines']}")
    print(
        f"   헤딩: {len(meta2['headings'])}, 태그: {len(meta2['tags'])}, 링크: {len(meta2['links'])}"
    )
    print()
    print("=" * 60)

    # Semantic similarity
    print()
    print("🔍 의미론적 유사도 분석 중...")

    emb1 = get_embedding(content1)
    emb2 = get_embedding(content2)

    if emb1 and emb2:
        similarity = cosine_similarity(emb1, emb2)
        print(f"   유사도: {similarity:.3f} ({int(similarity * 100)}%)")

        if similarity > 0.8:
            print("   ✅ 매우 유사한 문서입니다")
        elif similarity > 0.6:
            print("   ✅ 유사한 주제를 다루고 있습니다")
        elif similarity > 0.4:
            print("   ⚠️  일부 관련성이 있습니다")
        else:
            print("   ❌ 서로 다른 주제입니다")
    else:
        print("   ⚠️  유사도 계산 실패")

    # Content comparison
    print()
    print("📝 내용 비교...")
    comp = compare_content(content1, content2)
    print(f"   텍스트 일치율: {int(comp['similarity_ratio'] * 100)}%")
    print(f"   공통 줄: {comp['common_lines']}/{comp['total_lines']}")

    # Shared tags
    print()
    print("🏷️  공통 태그:")
    common_tags = set(meta1["tags"]) & set(meta2["tags"])
    if common_tags:
        print(f"   {', '.join('#' + t for t in common_tags)}")
    else:
        print("   (없음)")

    # Shared links
    print()
    print("🔗 공통 링크:")
    common_links = set(meta1["links"]) & set(meta2["links"])
    if common_links:
        for link in list(common_links)[:5]:
            print(f"   • [[{link}]]")
        if len(common_links) > 5:
            print(f"   ... +{len(common_links) - 5}개 더")
    else:
        print("   (없음)")

    # Key phrases
    print()
    print("💡 주요 키워드 비교:")

    phrases1 = extract_key_phrases(content1)
    phrases2 = extract_key_phrases(content2)

    words1 = {word for word, _ in phrases1}
    words2 = {word for word, _ in phrases2}
    common_words = words1 & words2

    print()
    print("   공통 키워드:")
    if common_words:
        print(f"   {', '.join(list(common_words)[:10])}")
    else:
        print("   (없음)")

    print()
    print("   문서 1 고유:")
    unique1 = [w for w, _ in phrases1[:5] if w not in words2]
    if unique1:
        print(f"   {', '.join(unique1)}")
    else:
        print("   (없음)")

    print()
    print("   문서 2 고유:")
    unique2 = [w for w, _ in phrases2[:5] if w not in words1]
    if unique2:
        print(f"   {', '.join(unique2)}")
    else:
        print("   (없음)")

    # Suggestions
    print()
    print("=" * 60)
    print("💡 제안:")
    print()

    if similarity and similarity > 0.7:
        print("• 문서가 매우 유사합니다. 하나로 합치는 것을 고려하세요")
        print("• 또는 하나를 다른 하나의 하위 문서로 재구성하세요")
    elif similarity and similarity > 0.4:
        print("• 관련된 내용이 있습니다. 상호 참조 링크를 추가하세요")
        print(f"  예: [[{Path(file1).stem}]], [[{Path(file2).stem}]]")
    else:
        print("• 서로 다른 주제를 다루고 있습니다")
        print("• 하나의 MOC(Map of Content)로 연결할 수 있습니다")

    if common_tags:
        print(f"• 공통 태그 {len(common_tags)}개로 연결되어 있습니다")

    print()


if __name__ == "__main__":
    main()
