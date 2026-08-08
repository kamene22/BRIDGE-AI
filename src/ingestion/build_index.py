import os
import re
from typing import List, Dict, Any
from pypdf import PdfReader
import chromadb
from dotenv import load_dotenv

# Import our GeminiProvider
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from llm_provider.provider import GeminiProvider

load_dotenv()

CORPUS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../corpus"))
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "/home/monic/projects/BridgeAI/db")

def parse_markdown_with_line_numbers(md_path: str) -> List[Dict[str, Any]]:
    """
    Parses a markdown file line-by-line. Groups lines into paragraph blocks
    and tracks their 1-based start and end line numbers.
    """
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
                
        # Handle trailing segment
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
        print(f"Error parsing markdown {md_path} with line numbers: {e}")
        
    return segments

def parse_pdf_with_page_numbers(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Parses a PDF file page-by-page. For each page, extracts paragraphs
    and tracks the page number (1-based).
    """
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
        print(f"Error parsing PDF {pdf_path} page-by-page: {e}")
        
    return segments

def group_and_chunk_segments(segments: List[Dict[str, Any]], chunk_size: int = 1100, overlap: int = 150) -> List[Dict[str, Any]]:
    """
    Groups smaller paragraph segments into larger logical chunks targeting approximately 1,100 characters.
    Maintains overlap and splits overly long segments into sentence-level sub-blocks.
    Tracks relative line numbers (for markdown) or page numbers (for PDFs).
    """
    chunks = []
    current_batch = []
    current_length = 0
    
    for seg in segments:
        text = seg["text"]
        
        # If a single segment is larger than target chunk_size, split it at sentence boundaries
        if len(text) > chunk_size:
            # Commit whatever is in the current batch first
            if current_batch:
                chunks.append(compile_chunk(current_batch))
                current_batch = []
                current_length = 0
                
            sentences = re.split(r'(?<=[.!?])\s+', text)
            sentence_batch = []
            sentence_len = 0
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                if sentence_len + len(sentence) > chunk_size and sentence_batch:
                    # Create a chunk from the sentence batch
                    chunks.append({
                        "text": " ".join(sentence_batch),
                        "start_line": seg.get("start_line"),
                        "end_line": seg.get("end_line"),
                        "page": seg.get("page")
                    })
                    # Maintain sentence overlap
                    overlap_tokens = []
                    overlap_len = 0
                    for s in reversed(sentence_batch):
                        if overlap_len + len(s) < overlap:
                            overlap_tokens.insert(0, s)
                            overlap_len += len(s)
                        else:
                            break
                    sentence_batch = overlap_tokens
                    sentence_len = sum(len(x) for x in sentence_batch)
                    
                sentence_batch.append(sentence)
                sentence_len += len(sentence)
                
            if sentence_batch:
                chunks.append({
                    "text": " ".join(sentence_batch),
                    "start_line": seg.get("start_line"),
                    "end_line": seg.get("end_line"),
                    "page": seg.get("page")
                })
        else:
            # Normal segment packing
            if current_length + len(text) > chunk_size and current_batch:
                chunks.append(compile_chunk(current_batch))
                # Maintain overlap from trailing elements of the current batch
                overlap_batch = []
                overlap_len = 0
                for item in reversed(current_batch):
                    if overlap_len + len(item["text"]) < overlap:
                        overlap_batch.insert(0, item)
                        overlap_len += len(item["text"])
                    else:
                        break
                current_batch = overlap_batch
                current_length = sum(len(x["text"]) for x in current_batch)
                
            current_batch.append(seg)
            current_length += len(text)
            
    if current_batch:
        chunks.append(compile_chunk(current_batch))
        
    return chunks

def compile_chunk(batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Helper function to concatenate segment texts and compile metadata (line ranges or page ranges).
    """
    text = "\n\n".join([x["text"] for x in batch])
    chunk_data = {"text": text}
    
    # Compile metadata ranges
    types = [x.get("type") for x in batch]
    if "markdown" in types:
        start_lines = [x["start_line"] for x in batch if "start_line" in x]
        end_lines = [x["end_line"] for x in batch if "end_line" in x]
        if start_lines and end_lines:
            chunk_data["start_line"] = min(start_lines)
            chunk_data["end_line"] = max(end_lines)
    elif "pdf" in types:
        pages = list(set([x["page"] for x in batch if "page" in x]))
        if len(pages) == 1:
            chunk_data["page"] = pages[0]
        elif len(pages) > 1:
            chunk_data["page"] = f"{min(pages)}-{max(pages)}"
            
    return chunk_data

def build_vector_index():
    print("Initializing Gemini Provider...")
    provider = GeminiProvider()
    
    print(f"Connecting to ChromaDB at {CHROMA_DB_PATH}...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    # Re-create the collection to ensure a clean index
    collection_name = "bridge_ai_corpus"
    try:
        chroma_client.delete_collection(collection_name)
        print(f"Deleted existing collection '{collection_name}' for re-indexing.")
    except Exception:
        pass
        
    collection = chroma_client.create_collection(name=collection_name)
    
    print(f"Scanning corpus directory: {CORPUS_DIR}...")
    if not os.path.exists(CORPUS_DIR):
        raise FileNotFoundError(f"Corpus directory not found: {CORPUS_DIR}")
        
    files = os.listdir(CORPUS_DIR)
    
    all_chunks = []
    all_metadatas = []
    all_ids = []
    
    for filename in files:
        if filename.startswith(".") or "Zone.Identifier" in filename:
            continue
            
        file_path = os.path.join(CORPUS_DIR, filename)
        print(f"Processing file: {filename}...")
        
        segments = []
        if filename.endswith(".pdf"):
            segments = parse_pdf_with_page_numbers(file_path)
        elif filename.endswith(".md") or filename.endswith(".txt"):
            segments = parse_markdown_with_line_numbers(file_path)
        else:
            print(f"Skipping unsupported file type: {filename}")
            continue
            
        if not segments:
            print(f"Warning: No text extracted from {filename}")
            continue
            
        file_chunks = group_and_chunk_segments(segments)
        print(f"Split {filename} into {len(file_chunks)} chunks.")
        
        title = filename.replace(".pdf", "").replace(".md", "").replace(".txt", "").replace("_", " ").title()
        
        for idx, chunk_data in enumerate(file_chunks):
            chunk_id = f"doc_{filename.replace('.', '_')}_{idx}"
            
            # Formulate metadata dictionary
            metadata = {
                "source": filename,
                "title": title,
                "chunk_index": idx
            }
            # Append line numbers or page numbers if available
            if chunk_data.get("start_line") is not None:
                metadata["start_line"] = chunk_data["start_line"]
            if chunk_data.get("end_line") is not None:
                metadata["end_line"] = chunk_data["end_line"]
            if chunk_data.get("page") is not None:
                metadata["page"] = str(chunk_data["page"])
                
            all_chunks.append(chunk_data["text"])
            all_metadatas.append(metadata)
            all_ids.append(chunk_id)
            
    if not all_chunks:
        print("No chunks to index. Exiting.")
        return
        
    print(f"Generating embeddings for {len(all_chunks)} chunks (this may take a moment)...")
    
    # Process in batches of 20 with sleeps to respect free-tier quotas
    import time
    batch_size = 20
    embeddings = []
    total_batches = (len(all_chunks) - 1) // batch_size + 1
    
    for i in range(0, len(all_chunks), batch_size):
        batch_chunks = all_chunks[i:i+batch_size]
        batch_num = i // batch_size + 1
        print(f"Embedding batch {batch_num}/{total_batches}...")
        
        batch_embeddings = provider.embed_texts(batch_chunks)
        embeddings.extend(batch_embeddings)
        
        if batch_num < total_batches:
            print("Sleeping 5 seconds between embedding requests...")
            time.sleep(5)
            
    print("Writing index to ChromaDB...")
    collection.add(
        ids=all_ids,
        embeddings=embeddings,
        metadatas=all_metadatas,
        documents=all_chunks
    )
    
    print("Vector index successfully built!")
    print(f"Indexed {len(all_ids)} chunks from the corpus.")

if __name__ == "__main__":
    build_vector_index()
