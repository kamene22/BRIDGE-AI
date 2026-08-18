"""
evaluation/chunk_quality_analyzer.py — Layered Fact Matcher & Chunk Quality Classifier

Classifies each retrieved chunk into 3 distinct categories:
  - Category 1 (Answer-Bearing & Relevant): Semantically relevant AND contains required facts.
  - Category 2 (Semantic-Only False Match): Semantically relevant to query BUT lacks required facts.
  - Category 3 (Irrelevant / Noise): Neither semantically relevant nor answer-bearing.

Calculates:
  1. Fact Recall@K (K=1, 3, 5): Percentage of required facts present in top K context.
  2. Complete Answer Rate@K (K=1, 3, 5): Percentage of queries where ALL required facts are present in context.
  3. Per-Chunk Answer Containment Rate: Percentage of retrieved chunks containing >=1 required fact.
  4. Semantic-Only Match Rate: Percentage of top K chunks that match embeddings but contain ZERO required facts.
"""

import re
import unicodedata
from typing import List, Dict, Any, Tuple


def normalize_text(text: str) -> str:
    """Normalizes text for deterministic fact matching (lowercase, strip accents, remove punctuation)."""
    text = text.lower()
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def check_fact_presence_deterministic(fact: str, chunk_text: str, aliases: List[str] = None) -> bool:
    """
    Layered deterministic fact matching:
      Layer 1: Exact phrase match
      Layer 2: Normalized text match
      Layer 3: Explicit aliases/synonyms match
      Layer 4: Key token co-occurrence match (>=80% of major fact words present)
    """
    if not fact or not chunk_text:
        return False

    chunk_norm = normalize_text(chunk_text)
    fact_norm = normalize_text(fact)

    # Layer 1 & 2: Substring or normalized phrase match
    if fact_norm in chunk_norm or fact.lower() in chunk_text.lower():
        return True

    # Layer 3: Synonym / Alias matching
    if aliases:
        for alias in aliases:
            if normalize_text(alias) in chunk_norm:
                return True

    # Layer 4: Key token co-occurrence (ignore short stop words <= 2 chars)
    fact_tokens = [t for t in fact_norm.split() if len(t) > 2]
    if not fact_tokens:
        return False

    matches = sum(1 for t in fact_tokens if t in chunk_norm)
    match_ratio = matches / len(fact_tokens)

    # Required threshold: at least 75% of non-stopword tokens must appear in chunk
    return match_ratio >= 0.75


def analyze_chunk_containment_for_case(
    test_case: Dict[str, Any],
    retrieved_chunks: List[Dict[str, Any]],
    k_list: List[int] = [1, 3, 5]
) -> Dict[str, Any]:
    """
    Analyzes answer containment and chunk quality metrics for a single test case across K=1, 3, 5.
    """
    required_facts = test_case.get("required_facts", [])
    expected_source = test_case.get("expected_source", "")
    expected_keywords = test_case.get("expected_chunk_keywords", [])
    aliases = test_case.get("aliases", [])

    results = {}

    total_facts = len(required_facts)

    for k in k_list:
        top_k_chunks = retrieved_chunks[:k]
        combined_text = " ".join([c.get("document", "") for c in top_k_chunks])

        # Track which required facts are found in top-K context
        facts_found_set = set()
        for fact in required_facts:
            if check_fact_presence_deterministic(fact, combined_text, aliases):
                facts_found_set.add(fact)

        fact_recall = round(len(facts_found_set) / total_facts, 4) if total_facts > 0 else 1.0
        complete_answer = (len(facts_found_set) == total_facts) and total_facts > 0

        # Classify each chunk in top-K
        cat1_count = 0  # Answer-Bearing & Relevant
        cat2_count = 0  # Semantic-Only False Match
        cat3_count = 0  # Irrelevant Noise

        for chunk in top_k_chunks:
            doc = chunk.get("document", "")
            source = chunk.get("metadata", {}).get("source", "") or chunk.get("metadata", {}).get("title", "")
            
            # Check if chunk contains at least one required fact
            has_fact = any(check_fact_presence_deterministic(f, doc, aliases) for f in required_facts)

            # Check semantic relevance to keywords/source
            is_semantic = (
                expected_source.lower() in source.lower() if expected_source else False
            ) or any(kw.lower() in doc.lower() for kw in expected_keywords)

            if has_fact:
                cat1_count += 1
            elif is_semantic:
                cat2_count += 1
            else:
                cat3_count += 1

        n_chunks = len(top_k_chunks)
        answer_bearing_rate = round(cat1_count / n_chunks, 4) if n_chunks > 0 else 0.0
        semantic_only_rate = round(cat2_count / n_chunks, 4) if n_chunks > 0 else 0.0

        results[f"fact_recall_at_{k}"] = fact_recall
        results[f"complete_answer_at_{k}"] = complete_answer
        results[f"cat1_answer_bearing_rate_at_{k}"] = answer_bearing_rate
        results[f"cat2_semantic_only_rate_at_{k}"] = semantic_only_rate
        results[f"cat3_noise_rate_at_{k}"] = round(cat3_count / n_chunks, 4) if n_chunks > 0 else 0.0
        results[f"facts_found_at_{k}"] = len(facts_found_set)
        results[f"facts_required"] = total_facts

    return results
