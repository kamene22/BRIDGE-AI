# Bridge AI — Stage 1 & 2: Embedding Model Comparison Report

**Date:** 2026-08-14 16:02:45
**Target Benchmark:** 29 Ground-Truth Retrieval Test Cases
**Baseline Chunk Size:** 1,100 characters / 150 overlap

---

## 1. Executive Summary
This experiment benchmarks three candidate embedding models (`models/gemini-embedding-2`, `models/text-embedding-004`, and `sentence-transformers/all-MiniLM-L6-v2`) on vector search quality and latency. Based on Mean Reciprocal Rank (MRR) and Recall@3, **models/gemini-embedding-2** (`emb_gemini_embedding_2`) was programmatically selected as the optimal embedding model for Stage 3 chunk parameter sweep.

## 2. Comparative Benchmark Matrix

| Embedding Model | Model ID | Recall@3 | Precision@3 | MRR | Mean Embedding Latency (ms) | Mean Total Latency (ms) | P95 Latency (ms) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **emb_gemini_embedding_2** | `models/gemini-embedding-2` | 0.3247 | 0.5172 | **0.6592** | 541.68 ms | 555.66 ms | 809.86 ms |
| **emb_text_embedding_004** | `models/text-embedding-004` | 0.1488 | 0.2759 | **0.4310** | 368.09 ms | 386.95 ms | 581.78 ms |

## 3. Decision Rationale & Selection
- **Winner:** `models/gemini-embedding-2` achieved MRR = **0.6592** and Recall@3 = **0.3247**.
- **Latency Analysis:** Remote API embedding generation is the primary latency component (~150–500ms), whereas ChromaDB cosine distance calculation is ultra-fast (~10–25ms).

## 4. Next Stage Dependency
**Stage 3 Chunk-Size Sweep** will proceed using the selected winning model: **`models/gemini-embedding-2`**.