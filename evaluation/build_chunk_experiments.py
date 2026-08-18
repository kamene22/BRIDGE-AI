"""
evaluation/build_chunk_experiments.py — Multi-Chunk Experimental Index Builder

Ingests corpus documents into 4 isolated experimental ChromaDB collections:
  1. exp_chunks_500_75   (500 chars, 75 overlap)
  2. exp_chunks_800_100  (800 chars, 100 overlap)
  3. exp_chunks_1100_150 (1,100 chars, 150 overlap - Baseline)
  4. exp_chunks_1500_200 (1,500 chars, 200 overlap)

Ensures the active production index is never mutated or overwritten.
Includes a --cleanup flag to delete experimental collections after evaluation.
"""

import os
import sys
import argparse
import chromadb
from typing import List, Dict, Any
from pypdf import PdfReader
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from src.llm_provider.provider import GeminiProvider

CORPUS_DIR = os.path.join(PROJECT_ROOT, "corpus")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(PROJECT_ROOT, "db"))

EXPERIMENTAL_CONFIGS = [
    {"name": "exp_chunks_500_75", "chunk_size": 500, "overlap": 75},
    {"name": "exp_chunks_800_100", "chunk_size": 800, "overlap": 100},
    {"name": "exp_chunks_1100_150", "chunk_size": 1100, "overlap": 150},
    {"name": "exp_chunks_1500_200", "chunk_size": 1500, "overlap": 200},
]


def load_corpus_documents() -> List[Dict[str, Any]]:
    """Loads text content from all Markdown and PDF corpus files."""
    docs = []
    if not os.path.exists(CORPUS_DIR):
        print(f"[Error] Corpus directory not found: {CORPUS_DIR}")
        return docs

    for fname in sorted(os.listdir(CORPUS_DIR)):
        fpath = os.path.join(CORPUS_DIR, fname)
        if fname.endswith(".md"):
            with open(fpath, "r", encoding="utf-8") as f:
                text = f.read()
            docs.append({"source": fname, "text": text, "type": "markdown"})
        elif fname.endswith(".pdf"):
            reader = PdfReader(fpath)
            text_parts = []
            for idx, page in enumerate(reader.pages):
                page_txt = page.extract_text() or ""
                text_parts.append(page_txt)
            docs.append({"source": fname, "text": "\n\n".join(text_parts), "type": "pdf"})

    return docs


def split_text_into_chunks(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Splits text into sliding-window character chunks with specified overlap."""
    if not text:
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += (chunk_size - overlap)

    return chunks


def build_collection(
    chroma_client: chromadb.PersistentClient,
    provider: GeminiProvider,
    config: Dict[str, Any],
    raw_docs: List[Dict[str, Any]]
):
    col_name = config["name"]
    chunk_size = config["chunk_size"]
    overlap = config["overlap"]

    print(f"\nBuilding collection [{col_name}] (chunk_size={chunk_size}, overlap={overlap})...")

    # Re-create experimental collection cleanly
    try:
        chroma_client.delete_collection(col_name)
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name=col_name,
        metadata={"hnsw:space": "cosine"}
    )

    all_chunks = []
    all_metadatas = []
    all_ids = []

    chunk_counter = 0
    for doc in raw_docs:
        chunks = split_text_into_chunks(doc["text"], chunk_size, overlap)
        for idx, chunk in enumerate(chunks, 1):
            chunk_counter += 1
            cid = f"{doc['source']}_c{idx}_s{chunk_size}"
            all_chunks.append(chunk)
            all_metadatas.append({
                "source": doc["source"],
                "title": doc["source"],
                "chunk_index": idx,
                "chunk_size": chunk_size,
                "overlap": overlap,
                "char_length": len(chunk),
                "est_tokens": len(chunk) // 4
            })
            all_ids.append(cid)

    print(f"  Generated {len(all_chunks)} chunks across {len(raw_docs)} documents.")

    # Embed in batches of 50
    batch_size = 50
    for i in range(0, len(all_chunks), batch_size):
        b_chunks = all_chunks[i:i + batch_size]
        b_metas = all_metadatas[i:i + batch_size]
        b_ids = all_ids[i:i + batch_size]

        embeddings = provider.embed_texts(b_chunks, task_type="retrieval_document")
        collection.add(
            documents=b_chunks,
            embeddings=embeddings,
            metadatas=b_metas,
            ids=b_ids
        )

    print(f"  ✓ Collection [{col_name}] indexed successfully with {collection.count()} chunks.")


def cleanup_experimental_collections(chroma_client: chromadb.PersistentClient):
    """Deletes experimental collections from ChromaDB persistent store."""
    print("\nCleaning up experimental ChromaDB collections...")
    for cfg in EXPERIMENTAL_CONFIGS:
        try:
            chroma_client.delete_collection(cfg["name"])
            print(f"  Deleted {cfg['name']}")
        except Exception as e:
            print(f"  Collection {cfg['name']} not found or already deleted.")


def main():
    parser = argparse.ArgumentParser(description="Build experimental ChromaDB chunk collections")
    parser.add_argument("--cleanup", action="store_true", help="Delete experimental collections from ChromaDB")
    args = parser.parse_args()

    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    if args.cleanup:
        cleanup_experimental_collections(chroma_client)
        sys.exit(0)

    print("=" * 80)
    print("BRIDGE AI — EXPERIMENTAL CHUNK COLLECTION BUILDER")
    print("=" * 80)

    provider = GeminiProvider()
    raw_docs = load_corpus_documents()
    print(f"Loaded {len(raw_docs)} raw corpus documents from {CORPUS_DIR}.")

    for cfg in EXPERIMENTAL_CONFIGS:
        build_collection(chroma_client, provider, cfg, raw_docs)

    print("\n" + "=" * 80)
    print("ALL EXPERIMENTAL CHUNK COLLECTIONS INDEXED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
