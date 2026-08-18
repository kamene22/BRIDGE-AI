"""
evaluation/adaptive_neighbor_retriever.py — Adaptive Local Context Neighbor Retriever

Implements deterministic, explainable triggers to expand retrieved context with neighboring chunks
ONLY when there is evidence that top-3 context is incomplete or requires multi-chunk legal evidence.

Deterministic Triggers (Zero LLM calls):
  1. STATUTORY_LEGAL_SIGNAL: Query targets statutory sections, regulations, overtime, probation, deductions.
  2. CHUNK_BOUNDARY_SIGNAL: Retrieved top-3 chunk exhibits structural truncation (ends without terminal punctuation or with a colon/header).
  3. MULTI_FACT_QUERY_SIGNAL: Query phrasing expects multi-fact rules, entitlements, or procedural steps.
"""

import re
from typing import List, Dict, Any, Tuple, Set


STATUTORY_KEYWORDS = {
    "section", "act", "probation", "deduction", "minimum wage", "overtime",
    "paybill", "helb", "contract", "working hours", "leave", "dock", "pay",
    "gazette", "nairobi", "fine", "penalty", "termination", "notice"
}

MULTI_FACT_PATTERNS = [
    r"\bwhat (are|were) the\b",
    r"\blist\b",
    r"\brights (and|or) obligations\b",
    r"\bentitlements\b",
    r"\brules around\b",
    r"\bwhat happens if\b",
    r"\ball (the|my)\b"
]


def check_query_triggers(query: str) -> Tuple[bool, List[str]]:
    """
    Checks if a query fires deterministic adaptive triggers.
    Returns (triggered_bool, list_of_trigger_names).
    """
    q_lower = query.lower()
    triggers_fired = []

    # 1. Statutory / Legal Trigger
    if any(kw in q_lower for kw in STATUTORY_KEYWORDS):
        triggers_fired.append("STATUTORY_LEGAL_SIGNAL")

    # 2. Multi-Fact Query Trigger
    for pattern in MULTI_FACT_PATTERNS:
        if re.search(pattern, q_lower):
            triggers_fired.append("MULTI_FACT_QUERY_SIGNAL")
            break

    return len(triggers_fired) > 0, triggers_fired


def check_chunk_boundary_trigger(chunks: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Checks if any retrieved chunk displays boundary truncation.
    """
    triggers = []
    for rank, c in enumerate(chunks[:3], 1):
        text = c.get("document", "").strip()
        if not text:
            continue
        # Truncation signals: ends with colon, heading, or non-terminal punctuation
        if text.endswith(":") or text.endswith(";") or text.endswith(",") or not text[-1] in ".?!\"'":
            triggers.append(f"CHUNK_BOUNDARY_SIGNAL_RANK_{rank}")
    return len(triggers) > 0, triggers


class AdaptiveNeighborRetriever:
    def __init__(self, all_chunks: List[Dict[str, Any]]):
        """
        Builds in-memory document chunk lookup map:
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

    def retrieve_adaptive(
        self,
        query: str,
        base_chunks: List[Dict[str, Any]],
        mode: str = "Adaptive_N_pm_1",
        only_top_rank: bool = False
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Adaptively expands base retrieved chunks with neighboring chunks from the SAME document
        ONLY when deterministic triggers fire.
        """
        q_triggered, q_triggers = check_query_triggers(query)
        b_triggered, b_triggers = check_chunk_boundary_trigger(base_chunks[:3])

        all_triggers = q_triggers + b_triggers
        should_expand = len(all_triggers) > 0

        expanded = []
        seen_ids: Set[str] = set()

        # Always preserve base chunks
        for c in base_chunks[:3]:
            cid = c.get("id", "")
            if cid and cid not in seen_ids:
                seen_ids.add(cid)
                expanded.append(c)

        added_neighbors_cnt = 0

        if should_expand:
            chunks_to_expand = base_chunks[:1] if only_top_rank else base_chunks[:3]

            for chunk in chunks_to_expand:
                cid = chunk.get("id", "")
                meta = chunk.get("metadata", {})
                src = meta.get("source", "")
                c_idx = meta.get("chunk_index")

                if src in self.doc_map and c_idx is not None:
                    curr_idx = int(c_idx)

                    # N-1 Neighbor
                    if mode in ["Adaptive_N_minus_1", "Adaptive_N_pm_1", "Selective_N_pm_1"]:
                        prev_idx = curr_idx - 1
                        if prev_idx in self.doc_map[src]:
                            prev_chunk = self.doc_map[src][prev_idx]
                            pid = prev_chunk.get("id", "")
                            if pid and pid not in seen_ids:
                                seen_ids.add(pid)
                                expanded.append(prev_chunk)
                                added_neighbors_cnt += 1

                    # N+1 Neighbor
                    if mode in ["Adaptive_N_plus_1", "Adaptive_N_pm_1", "Selective_N_pm_1"]:
                        next_idx = curr_idx + 1
                        if next_idx in self.doc_map[src]:
                            next_chunk = self.doc_map[src][next_idx]
                            nid = next_chunk.get("id", "")
                            if nid and nid not in seen_ids:
                                seen_ids.add(nid)
                                expanded.append(next_chunk)
                                added_neighbors_cnt += 1

        trigger_metadata = {
            "triggered": should_expand,
            "triggers_fired": all_triggers,
            "neighbors_added": added_neighbors_cnt,
            "chunks_before": len(base_chunks[:3]),
            "chunks_after": len(expanded)
        }

        return expanded, trigger_metadata
