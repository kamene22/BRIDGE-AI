"""
evaluation/neighbor_retriever.py — Experimental Local Context Neighbor Retriever

Implements deterministic adjacent chunk retrieval (N-1, N+1) within the SAME document boundaries.
Zero extra vector embedding or ChromaDB API calls — uses pre-indexed document chunk maps.
"""

from typing import List, Dict, Any, Set, Tuple


class NeighborRetriever:
    def __init__(self, all_chunks: List[Dict[str, Any]]):
        """
        Builds an in-memory document chunk lookup map:
        doc_map[source][chunk_index] -> chunk_dict
        """
        self.doc_map = {}
        self.chunk_by_id = {}

        for chunk in all_chunks:
            cid = chunk.get("id", "")
            meta = chunk.get("metadata", {})
            src = meta.get("source", "")
            c_idx = meta.get("chunk_index")

            if cid:
                self.chunk_by_id[cid] = chunk

            if src and c_idx is not None:
                if src not in self.doc_map:
                    self.doc_map[src] = {}
                self.doc_map[src][int(c_idx)] = chunk

    def get_neighbors(
        self,
        base_chunks: List[Dict[str, Any]],
        mode: str = "N_plus_minus_1",
        only_top_rank: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Expands base retrieved chunks with neighboring chunks from the SAME document.
        Supported modes:
          - 'N_plus_1': Add chunk N+1
          - 'N_minus_1': Add chunk N-1
          - 'N_plus_minus_1': Add both N-1 and N+1
        """
        expanded = []
        seen_ids: Set[str] = set()

        chunks_to_expand = base_chunks[:1] if only_top_rank else base_chunks

        for chunk in base_chunks:
            cid = chunk.get("id", "")
            meta = chunk.get("metadata", {})
            src = meta.get("source", "")
            c_idx = meta.get("chunk_index")

            # Always preserve base chunk
            if cid and cid not in seen_ids:
                seen_ids.add(cid)
                expanded.append(chunk)

            # Check if this chunk should have neighbors added
            if chunk in chunks_to_expand and src in self.doc_map and c_idx is not None:
                curr_idx = int(c_idx)

                # N-1 Neighbor
                if mode in ["N_minus_1", "N_plus_minus_1"]:
                    prev_idx = curr_idx - 1
                    if prev_idx in self.doc_map[src]:
                        prev_chunk = self.doc_map[src][prev_idx]
                        pid = prev_chunk.get("id", "")
                        if pid and pid not in seen_ids:
                            seen_ids.add(pid)
                            expanded.append(prev_chunk)

                # N+1 Neighbor
                if mode in ["N_plus_1", "N_plus_minus_1"]:
                    next_idx = curr_idx + 1
                    if next_idx in self.doc_map[src]:
                        next_chunk = self.doc_map[src][next_idx]
                        nid = next_chunk.get("id", "")
                        if nid and nid not in seen_ids:
                            seen_ids.add(nid)
                            expanded.append(next_chunk)

        return expanded
