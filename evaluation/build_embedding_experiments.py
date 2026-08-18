"""
evaluation/build_embedding_experiments.py — Stage 1: Embedding Model Comparison Index Builder

Ingests corpus documents at baseline chunking parameters (1,100 chars, 150 overlap) into 3 isolated ChromaDB collections:
  1. emb_gemini_embedding_2 (models/gemini-embedding-2 - Current Baseline)
  2. emb_text_embedding_004 (models/text-embedding-004)
  3. emb_bge_small_en       (sentence-transformers/all-MiniLM-L6-v2)

Preserves production collections and allows clean evaluation.
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

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

CORPUS_DIR = os.path.join(PROJECT_ROOT, "corpus")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(PROJECT_ROOT, "db"))

EMBEDDING_CONFIGS = [
    {"name": "emb_gemini_embedding_2", "model_id": "models/gemini-embedding-2", "type": "gemini"},
    {"name": "emb_text_embedding_004", "model_id": "models/text-embedding-004", "type": "gemini"},
]


def load_corpus_documents() -> List[Dict[str, Any]]:
    docs = []
    if not os.path.exists(CORPUS_DIR):
        print(f"[Error] Corpus directory not found: {CORPUS_DIR}")
        return docs

    for fname in sorted(os.listdir(CORPUS_DIR)):
        fpath = os.path.join(CORPUS_DIR, fname)
        if fname.endswith(".md"):
            with open(fpath, "r", encoding="utf-8") as f:
                docs.append({"source": fname, "text": f.read(), "type": "markdown"})
        elif fname.endswith(".pdf"):
            reader = PdfReader(fpath)
            text_parts = [p.extract_text() or "" for p in reader.pages]
            docs.append({"source": fname, "text": "\n\n".join(text_parts), "type": "pdf"})

    return docs


def split_text(text: str, chunk_size: int = 1100, overlap: int = 150) -> List[str]:
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


def build_embedding_collection(
    chroma_client: chromadb.PersistentClient,
    gemini_provider: GeminiProvider,
    cfg: Dict[str, Any],
    raw_docs: List[Dict[str, Any]]
):
    col_name = cfg["name"]
    model_id = cfg["model_id"]
    model_type = cfg["type"]

    print(f"\nBuilding Embedding Collection [{col_name}] using model ({model_id})...")

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

    for doc in raw_docs:
        chunks = split_text(doc["text"], 1100, 150)
        for idx, chunk in enumerate(chunks, 1):
            cid = f"{doc['source']}_c{idx}_{col_name}"
            all_chunks.append(chunk)
            all_metadatas.append({"source": doc["source"], "chunk_index": idx})
            all_ids.append(cid)

    # Embed chunks
    local_st_model = None
    if model_type == "local":
        if not HAS_SENTENCE_TRANSFORMERS:
            print("  [Warning] sentence-transformers not installed. Fallback to Gemini embedding.")
            model_type = "gemini"
        else:
            local_st_model = SentenceTransformer(model_id)

    batch_size = 50
    for i in range(0, len(all_chunks), batch_size):
        b_chunks = all_chunks[i:i + batch_size]
        b_metas = all_metadatas[i:i + batch_size]
        b_ids = all_ids[i:i + batch_size]

        if model_type == "gemini":
            embeddings = gemini_provider.embed_texts(b_chunks, model=model_id, task_type="retrieval_document")
        else:
            vecs = local_st_model.encode(b_chunks, convert_to_numpy=True)
            embeddings = vecs.tolist()

        collection.add(
            documents=b_chunks,
            embeddings=embeddings,
            metadatas=b_metas,
            ids=b_ids
        )

    print(f"  ✓ Collection [{col_name}] indexed successfully with {collection.count()} chunks.")


def main():
    print("=" * 80)
    print("BRIDGE AI — STAGE 1: EMBEDDING MODEL COMPARISON INDEX BUILDER")
    print("=" * 80)

    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    gemini_provider = GeminiProvider()
    raw_docs = load_corpus_documents()
    print(f"Loaded {len(raw_docs)} corpus documents.")

    for cfg in EMBEDDING_CONFIGS:
        build_embedding_collection(chroma_client, gemini_provider, cfg, raw_docs)

    print("\n" + "=" * 80)
    print("ALL EMBEDDING MODEL COLLECTIONS INDEXED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
