"""
verify_all_6_corpuses.py — Verify that all 6 corpus documents are indexed in ChromaDB.
"""

import os
import sys
import chromadb

db_dir = os.path.abspath("db")
client = chromadb.PersistentClient(path=db_dir)
collection = client.get_collection(name="bridge_ai_corpus")

total_chunks = collection.count()
print(f"Total chunks in ChromaDB: {total_chunks}")

all_data = collection.get(include=["metadatas"])
metadatas = all_data.get("metadatas", [])

sources_count = {}
for meta in metadatas:
    src = meta.get("source", "Unknown")
    sources_count[src] = sources_count.get(src, 0) + 1

print("\n" + "=" * 75)
print("DISTRIBUTION OF ALL 6 CORPUS DOCUMENTS IN CHROMADB:")
print("=" * 75)
for src, count in sorted(sources_count.items()):
    print(f"  • {src:<52} : {count} chunks")

print("=" * 75)
print(f"Total Unique Document Sources Indexed: {len(sources_count)}")
