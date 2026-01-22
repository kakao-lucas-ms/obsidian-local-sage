#!/usr/bin/env python3
"""
Obsidian Wrapper: Simple Search (Debug Version)
Very simple output for testing
"""

import sys
import os

def main():
    # Check if query provided
    if len(sys.argv) < 2:
        print("❌ No search query provided")
        print("Usage: Select text in Obsidian and run the command")
        sys.exit(0)

    query = " ".join(sys.argv[1:])

    # Show what we received
    if not query or query.strip() == "":
        print("❌ Empty search query")
        print("Please select some text before running this command")
        sys.exit(0)

    print(f"✅ Received query: {query}")
    print(f"Query length: {len(query)} characters")

    # Try to do actual search
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import requests

        # Test Qdrant connection
        response = requests.get("http://127.0.0.1:6333/collections/obsidian_notes", timeout=5)
        if response.status_code == 200:
            data = response.json()
            count = data.get("result", {}).get("points_count", 0)
            print(f"✅ Qdrant connected: {count} documents")
        else:
            print(f"⚠️ Qdrant response: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n(This is a test version)")

if __name__ == "__main__":
    main()
