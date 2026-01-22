#!/usr/bin/env python3
"""
Obsidian: Vault Health Check
Find and report various issues in your Obsidian vault
"""

import os
import sys
import sqlite3
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import config

# Use config values
DB_PATH = str(config.db_path)
VAULT_PATH = str(config.vault_path)

class HealthChecker:
    def __init__(self, vault_path):
        self.vault_path = Path(vault_path)
        self.issues = defaultdict(list)

    def get_all_documents(self):
        """Get all markdown documents"""
        return list(self.vault_path.rglob("*.md"))

    def check_empty_documents(self, docs):
        """Find empty or nearly empty documents"""
        print("📄 빈 문서 검사...")

        for doc in docs:
            try:
                with open(doc, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                if len(content) == 0:
                    self.issues['empty'].append(str(doc.relative_to(self.vault_path)))
                elif len(content) < 20:
                    self.issues['nearly_empty'].append((
                        str(doc.relative_to(self.vault_path)),
                        len(content)
                    ))
            except:
                continue

    def check_orphaned_documents(self, docs):
        """Find documents with no incoming links"""
        print("🔗 고립된 문서 검사...")

        # Build link graph
        incoming_links = defaultdict(set)

        for doc in docs:
            try:
                with open(doc, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find all wikilinks
                links = re.findall(r'\[\[([^\]|]+)', content)

                for link in links:
                    target = link.strip()
                    incoming_links[target].add(str(doc.relative_to(self.vault_path)))

            except:
                continue

        # Find documents with no incoming links
        for doc in docs:
            doc_name = doc.stem
            if doc_name not in incoming_links and len(incoming_links.get(doc_name, [])) == 0:
                # Check if it's an index or MOC
                is_special = any(keyword in doc_name.lower()
                                for keyword in ['index', 'moc', 'readme', '목차'])
                if not is_special:
                    self.issues['orphaned'].append(str(doc.relative_to(self.vault_path)))

    def check_broken_links(self, docs):
        """Find broken wikilinks"""
        print("🔗 깨진 링크 검사...")

        for doc in docs:
            try:
                with open(doc, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find all wikilinks
                links = re.findall(r'\[\[([^\]|]+)', content)

                for link in links:
                    target = link.strip()

                    # Try to find target file
                    found = False
                    for ext in ['.md', '']:
                        target_path = self.vault_path / f"{target}{ext}"
                        if target_path.exists():
                            found = True
                            break

                    if not found:
                        self.issues['broken_links'].append((
                            str(doc.relative_to(self.vault_path)),
                            target
                        ))

            except:
                continue

    def check_duplicate_names(self, docs):
        """Find documents with the same name in different folders"""
        print("📁 중복 이름 검사...")

        names = defaultdict(list)

        for doc in docs:
            names[doc.stem].append(str(doc.relative_to(self.vault_path)))

        for name, paths in names.items():
            if len(paths) > 1:
                self.issues['duplicates'].append((name, paths))

    def check_old_documents(self, docs):
        """Find documents not modified in a long time"""
        print("⏰ 오래된 문서 검사...")

        old_days = config.get('features.health_check.old_document_days', 365)
        threshold = datetime.now() - timedelta(days=old_days)

        for doc in docs:
            try:
                mtime = datetime.fromtimestamp(doc.stat().st_mtime)
                if mtime < threshold:
                    self.issues['old'].append((
                        str(doc.relative_to(self.vault_path)),
                        (datetime.now() - mtime).days
                    ))
            except:
                continue

    def check_large_documents(self, docs):
        """Find very large documents"""
        print("📏 큰 문서 검사...")

        large_kb = config.get('features.health_check.large_document_kb', 100)
        size_threshold = large_kb * 1000

        for doc in docs:
            try:
                size = doc.stat().st_size
                if size > size_threshold:
                    with open(doc, 'r', encoding='utf-8') as f:
                        lines = len(f.readlines())

                    self.issues['large'].append((
                        str(doc.relative_to(self.vault_path)),
                        size,
                        lines
                    ))
            except:
                continue

    def check_missing_tags(self, docs):
        """Find documents without any tags"""
        print("🏷️  태그 없는 문서 검사...")

        for doc in docs:
            try:
                with open(doc, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find tags
                tags = re.findall(r'#(\w+)', content)

                if not tags:
                    self.issues['no_tags'].append(str(doc.relative_to(self.vault_path)))

            except:
                continue

    def check_todo_items(self, docs):
        """Find documents with uncompleted TODO items"""
        print("✅ TODO 항목 검사...")

        for doc in docs:
            try:
                with open(doc, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find uncompleted TODO items
                todos = re.findall(r'- \[ \] (.+)', content)

                if todos:
                    self.issues['todos'].append((
                        str(doc.relative_to(self.vault_path)),
                        len(todos)
                    ))

            except:
                continue

    def print_report(self):
        """Print health check report"""
        print()
        print("=" * 60)
        print("📊 Vault Health Check Report")
        print("=" * 60)
        print()

        total_issues = sum(len(v) for v in self.issues.values())

        if total_issues == 0:
            print("✅ 발견된 문제 없음!")
            print("   Vault가 건강합니다!")
            return

        # Empty documents
        if self.issues['empty']:
            print(f"📄 빈 문서: {len(self.issues['empty'])}개")
            for path in self.issues['empty'][:5]:
                print(f"   • {path}")
            if len(self.issues['empty']) > 5:
                print(f"   ... +{len(self.issues['empty']) - 5}개 더")
            print()

        # Nearly empty
        if self.issues['nearly_empty']:
            print(f"⚠️  거의 빈 문서 (< 20자): {len(self.issues['nearly_empty'])}개")
            for path, size in self.issues['nearly_empty'][:5]:
                print(f"   • {path} ({size}자)")
            if len(self.issues['nearly_empty']) > 5:
                print(f"   ... +{len(self.issues['nearly_empty']) - 5}개 더")
            print()

        # Orphaned
        if self.issues['orphaned']:
            print(f"🔗 고립된 문서 (링크 없음): {len(self.issues['orphaned'])}개")
            for path in self.issues['orphaned'][:5]:
                print(f"   • {path}")
            if len(self.issues['orphaned']) > 5:
                print(f"   ... +{len(self.issues['orphaned']) - 5}개 더")
            print()

        # Broken links
        if self.issues['broken_links']:
            print(f"🔗 깨진 링크: {len(self.issues['broken_links'])}개")
            for doc_path, link in self.issues['broken_links'][:5]:
                print(f"   • {doc_path} → [[{link}]]")
            if len(self.issues['broken_links']) > 5:
                print(f"   ... +{len(self.issues['broken_links']) - 5}개 더")
            print()

        # Duplicates
        if self.issues['duplicates']:
            print(f"📁 중복 이름: {len(self.issues['duplicates'])}개")
            for name, paths in self.issues['duplicates'][:3]:
                print(f"   • {name}:")
                for path in paths:
                    print(f"     - {path}")
            if len(self.issues['duplicates']) > 3:
                print(f"   ... +{len(self.issues['duplicates']) - 3}개 더")
            print()

        # Old documents
        if self.issues['old']:
            print(f"⏰ 오래된 문서 (> 1년): {len(self.issues['old'])}개")
            sorted_old = sorted(self.issues['old'], key=lambda x: x[1], reverse=True)
            for path, days in sorted_old[:5]:
                print(f"   • {path} ({days}일 전)")
            if len(self.issues['old']) > 5:
                print(f"   ... +{len(self.issues['old']) - 5}개 더")
            print()

        # Large documents
        if self.issues['large']:
            print(f"📏 큰 문서 (> 100KB): {len(self.issues['large'])}개")
            sorted_large = sorted(self.issues['large'], key=lambda x: x[1], reverse=True)
            for path, size, lines in sorted_large[:5]:
                print(f"   • {path} ({size/1024:.1f}KB, {lines}줄)")
            if len(self.issues['large']) > 5:
                print(f"   ... +{len(self.issues['large']) - 5}개 더")
            print()

        # No tags
        if self.issues['no_tags']:
            print(f"🏷️  태그 없음: {len(self.issues['no_tags'])}개")
            for path in self.issues['no_tags'][:5]:
                print(f"   • {path}")
            if len(self.issues['no_tags']) > 5:
                print(f"   ... +{len(self.issues['no_tags']) - 5}개 더")
            print()

        # TODOs
        if self.issues['todos']:
            total_todos = sum(count for _, count in self.issues['todos'])
            print(f"✅ 미완료 TODO: {total_todos}개 ({len(self.issues['todos'])}개 문서)")
            sorted_todos = sorted(self.issues['todos'], key=lambda x: x[1], reverse=True)
            for path, count in sorted_todos[:5]:
                print(f"   • {path} ({count}개)")
            if len(self.issues['todos']) > 5:
                print(f"   ... +{len(self.issues['todos']) - 5}개 더")
            print()

        # Summary
        print("=" * 60)
        print(f"총 문제: {total_issues}개")
        print()
        print("💡 제안:")
        print("• 빈 문서는 내용을 추가하거나 삭제하세요")
        print("• 고립된 문서는 다른 문서에서 링크하세요")
        print("• 깨진 링크는 수정하거나 제거하세요")
        print("• 중복 이름은 구분 가능하도록 이름을 변경하세요")
        print("• 오래된 문서는 보관하거나 삭제하세요")
        print()

def main():
    print("🏥 Obsidian Vault Health Check")
    print("=" * 60)
    print()

    if not Path(VAULT_PATH).exists():
        print(f"❌ Vault를 찾을 수 없습니다: {VAULT_PATH}")
        sys.exit(1)

    checker = HealthChecker(VAULT_PATH)

    # Get all documents
    print("📁 문서 검색 중...")
    docs = checker.get_all_documents()
    print(f"   발견: {len(docs)}개 문서")
    print()

    # Run checks
    checker.check_empty_documents(docs)
    checker.check_orphaned_documents(docs)
    checker.check_broken_links(docs)
    checker.check_duplicate_names(docs)
    checker.check_old_documents(docs)
    checker.check_large_documents(docs)
    checker.check_missing_tags(docs)
    checker.check_todo_items(docs)

    # Print report
    checker.print_report()

if __name__ == "__main__":
    main()
