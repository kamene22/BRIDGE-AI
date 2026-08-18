import os
import chromadb
import json

client = chromadb.PersistentClient(path="db")
coll = client.get_collection("exp_chunks_1500_200")
data = coll.get(limit=5, include=["metadatas", "documents"])

print(f"Total chunks in collection: {coll.count()}")
for i, (cid, meta) in enumerate(zip(data["ids"], data["metadatas"])):
    print(f"[{i}] ID: {cid} | Metadata: {meta}")
