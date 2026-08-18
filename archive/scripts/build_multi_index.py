"""
src/ingestion/build_multi_index.py — Dual Multi-Index Vector Ingestion Engine (REAPER Architecture)

Creates 2 specialized ChromaDB collections:
  1. `kenya_employment_act_index` (Statutory rules, Employment Act Cap 226)
  2. `kenya_career_handbook_index` (Workplace norms, soft skills, scam guides)
"""

import os
import re
import sys
import time
from typing import List, Dict, Any
from pypdf import PdfReader
import chromadb
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from llm_provider.provider import GeminiProvider

load_dotenv()

CORPUS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../corpus"))
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "/home/monic/projects/BridgeAI/db")

# Document Partition Mapping
LEGAL_FILES = [
    "Employment Act (Cap 226).pdf",
    "Labour Relations Act",
    "Regulation of Wages"
]

def parse_markdown_with_line_numbers(md_path: str) -> List[Dict[str, Any]]:
    segments = []
    current_lines = []
    start_line = 1
    
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for idx, line in enumerate(lines):
            line_num = idx + 1
            if line.strip() == "":
                if current_lines:
                    text = "".join(current_lines).strip()
                    if text:
                        segments.append({
                            "text": text,
                            "start_line": start_line,
                            "end_line": line_num - 1,
                            "type": "markdown"
                        })
                    current_lines = []
                start_line = line_num + 1
            else:
                if not current_lines:
                    start_line = line_num
                current_lines.append(line)
                
        if current_lines:
            text = "".join(current_lines).strip()
            if text:
                segments.append({
                    "text": text,
                    "start_line": start_line,
                    "end_line": len(lines),
                    "type": "markdown"
                })
    except Exception as e:
        print(f"Error parsing markdown {md_path}: {e}")
        
    return segments


def parse_pdf_with_page_numbers(pdf_path: str) -> List[Dict[str, Any]]:
    segments = []
    try:
        reader = PdfReader(pdf_path)
        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            text = page.extract_text()
            if not text:
                continue
                
            paragraphs = text.split("\n\n")
            for para in paragraphs:
                para = para.strip()
                if para:
                    segments.append({
                        "text": para,
                        "page": page_num,
                        "type": "pdf"
                    })
    except Exception as e:
        print(f"Error parsing PDF {pdf_path}: {e}")
        
    return segments


def group_and_chunk_segments(segments: List[Dict[str, Any]], chunk_size: int = 1100, overlap: int = 150) -> List[Dict[str, Any]]:
    chunks = []
    current_batch = []
    current_len = 0
    start_line = None
    end_line = None
    pages = set()

    for seg in segments:
        text = seg["text"]
        if seg.get("start_line") is not None:
            if start_line is None:
                start_line = seg["start_line"]
            end_line = seg["end_line"]
        if seg.get("page") is not None:
            pages.add(seg["page"])

        if current_len + len(text) > chunk_size and current_batch:
            chunk_str = "\n\n".join(current_batch).strip()
            chunk_meta = {}
            if start_line is not None:
                chunk_meta["start_line"] = start_line
                chunk_meta["end_line"] = end_line
            if pages:
                chunk_meta["page"] = sorted(list(pages))[0]

            chunks.append({"text": chunk_str, **chunk_meta})
            
            # Reset batch with overlap
            current_batch = [text]
            current_len = len(text)
            start_line = seg.get("start_line")
            end_line = seg.get("end_line")
            pages = {seg["page"]} if seg.get("page") is not None else set()
        else:
            current_batch.append(text)
            current_len += len(text)

    if current_batch:
        chunk_str = "\n\n".join(current_batch).strip()
        chunk_meta = {}
        if start_line is not None:
            chunk_meta["start_line"] = start_line
            chunk_meta["end_line"] = end_line
        if pages:
            chunk_meta["page"] = sorted(list(pages))[0]
        chunks.append({"text": chunk_str, **chunk_meta})

    return chunks


def build_multi_index():
    print("=" * 60)
    print("BUILDING DUAL MULTI-INDEX CHROMADB COLLECTIONS (REAPER ARCHITECTURE)")
    print("=" * 60)
    
    provider = GeminiProvider()
    client = chromadb.PersistentClient(
        path=CHROMA_DB_PATH,
        settings=chromadb.config.Settings(anonymized_telemetry=False)
    )

    legal_collection = client.get_or_create_collection(
        name="kenya_employment_act_index",
        metadata={"hnsw:space": "l2", "description": "Kenya Employment Act & Statutory Rights"}
    )
    
    handbook_collection = client.get_or_create_collection(
        name="kenya_career_handbook_index",
        metadata={"hnsw:space": "l2", "description": "Bridge AI Career Handbook & Soft Skills"}
    )

    legal_chunks, legal_metas, legal_ids = [], [], []
    handbook_chunks, handbook_metas, handbook_ids = [], [], []

    files = [f for f in os.listdir(CORPUS_DIR) if f.endswith((".pdf", ".md", ".txt"))]

    for filename in files:
        filepath = os.path.join(CORPUS_DIR, filename)
        is_legal = any(k.lower() in filename.lower() for k in ["employment act", "labour", "wages"])

        if filename.endswith(".pdf"):
            segments = parse_pdf_with_page_numbers(filepath)
        else:
            segments = parse_markdown_with_line_numbers(filepath)

        file_chunks = group_and_chunk_segments(segments)
        title = filename.replace(".pdf", "").replace(".md", "").replace(".txt", "").replace("_", " ").title()

        for idx, chunk_data in enumerate(file_chunks):
            chunk_id = f"doc_{filename.replace('.', '_')}_{idx}"
            metadata = {
                "source": filename,
                "title": title,
                "category": "statutory_legal" if is_legal else "career_handbook",
                "chunk_index": idx
            }
            if chunk_data.get("start_line") is not None:
                metadata["start_line"] = chunk_data["start_line"]
                metadata["end_line"] = chunk_data["end_line"]
            if chunk_data.get("page") is not None:
                metadata["page"] = str(chunk_data["page"])

            if is_legal:
                legal_chunks.append(chunk_data["text"])
                legal_metas.append(metadata)
                legal_ids.append(chunk_id)
            else:
                handbook_chunks.append(chunk_data["text"])
                handbook_metas.append(metadata)
                handbook_ids.append(chunk_id)

    def embed_and_store(collection, chunks, metadatas, ids, name):
        if not chunks:
            return
        print(f"\nEmbedding {len(chunks)} chunks for collection `{name}`...")
        batch_size = 20
        embeddings = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            print(f"  Batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}...")
            embeddings.extend(provider.embed_texts(batch))
            time.sleep(2)

        collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=chunks)
        print(f"✓ Collection `{name}` indexed {len(ids)} chunks.")

    embed_and_store(legal_collection, legal_chunks, legal_metas, legal_ids, "kenya_employment_act_index")
    embed_and_store(handbook_collection, handbook_chunks, handbook_metas, handbook_ids, "kenya_career_handbook_index")

    print("\n============================================================")
    print("DUAL MULTI-INDEX VECTOR STORE SUCCESSFULLY BUILT ✓")
    print("============================================================")

if __name__ == "__main__":
    build_multi_index()
