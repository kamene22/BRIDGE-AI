"""
src/retrieval/hybrid_retriever.py — Reciprocal Rank Fusion (RRF) Hybrid Retriever Module

Combines Dense Vector Candidates and BM25 Sparse Candidates using Reciprocal Rank Fusion (RRF):
  RRF_score(d) = 1 / (k + rank_dense(d)) + 1 / (k + rank_bm25(d))

Configurable k parameter (default = 60).
"""

from typing import List, Dict, Any, Tuple


def apply_reciprocal_rank_fusion(
    dense_candidates: List[Dict[str, Any]],
    bm25_candidates: List[Dict[str, Any]],
    rrf_k: float = 60.0,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Fuses dense vector candidates and BM25 sparse candidates using RRF.
    Deduplicates candidates by chunk ID and sorts by fused RRF score descending.
    """
    fused_scores = {}
    chunk_map = {}

    # 1. Process Dense Candidates
    for rank, chunk in enumerate(dense_candidates, 1):
        cid = chunk.get("id", "")
        if not cid:
            continue
        rrf_contrib = 1.0 / (rrf_k + rank)
        fused_scores[cid] = fused_scores.get(cid, 0.0) + rrf_contrib

        if cid not in chunk_map:
            chunk_copy = chunk.copy()
            chunk_copy["dense_rank"] = rank
            chunk_copy["bm25_rank"] = None
            chunk_map[cid] = chunk_copy
        else:
            chunk_map[cid]["dense_rank"] = rank

    # 2. Process BM25 Candidates
    for rank, chunk in enumerate(bm25_candidates, 1):
        cid = chunk.get("id", "")
        if not cid:
            continue
        rrf_contrib = 1.0 / (rrf_k + rank)
        fused_scores[cid] = fused_scores.get(cid, 0.0) + rrf_contrib

        if cid not in chunk_map:
            chunk_copy = chunk.copy()
            chunk_copy["dense_rank"] = None
            chunk_copy["bm25_rank"] = rank
            chunk_map[cid] = chunk_copy
        else:
            chunk_map[cid]["bm25_rank"] = rank

    # 3. Sort by Fused RRF Score
    sorted_cids = sorted(fused_scores.keys(), key=lambda cid: fused_scores[cid], reverse=True)

    fused_results = []
    for final_rank, cid in enumerate(sorted_cids[:top_k], 1):
        chunk = chunk_map[cid]
        chunk["rrf_score"] = round(fused_scores[cid], 6)
        chunk["final_rank"] = final_rank

        # Hit Source Classification
        has_dense = chunk.get("dense_rank") is not None
        has_bm25 = chunk.get("bm25_rank") is not None
        if has_dense and has_bm25:
            chunk["hit_source"] = "Both"
        elif has_dense:
            chunk["hit_source"] = "Dense_Only"
        else:
            chunk["hit_source"] = "BM25_Only"

        fused_results.append(chunk)

    return fused_results
