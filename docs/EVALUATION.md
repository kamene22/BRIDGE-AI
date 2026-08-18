# Bridge AI — Retrieval Evaluation Methodology & Metrics Guide

This document explains the evaluation framework, metrics, and ground-truth evaluation set (`evaluation/retrieval_eval_set.json`) used to benchmark Bridge AI.

---

## 1. Ground-Truth Evaluation Dataset Overview

- **File Path:** `evaluation/retrieval_eval_set.json`
- **Total Test Cases:** 29 curated evaluation questions.
- **Total Required Facts:** 66 annotated ground-truth facts.
- **Domain Coverage:** Employment Act regulations, minimum wage schedules, HELB repayments, payslip tax deductions, job scams, workplace etiquette, and interview preparation.

### Example Evaluation Case Structure
```json
{
  "test_id": "GE-001",
  "question": "How long is the probation period legally capped at in Kenya?",
  "category": "legal_statutory",
  "expected_source": "Employment Act.pdf",
  "expected_chunk_keywords": ["probation", "6 months", "Section 42"],
  "required_facts": [
    "Maximum probation period is 6 months",
    "Can be extended for another 6 months with employee consent"
  ]
}
```

---

## 2. Comprehensive Metrics Guide

### 1. Recall@K (Recall at Top-K)
- **What it measures:** The fraction of expected keyword targets or source chunks retrieved within the top-K hits.
- **Why it matters:** Ensures the retrieval engine doesn't completely miss expected source documents.
- **High/Low Value:** High (1.0) means target document is present in top-K; Low (0.0) means complete retrieval failure.
- **Decision Impact:** Used during initial embedding model screening (`gemini-embedding-2` won with Recall@3 = 0.3621).

---

### 2. Precision@K (Precision at Top-K)
- **What it measures:** The proportion of retrieved top-K chunks that are semantically relevant to the query topic.
- **Why it matters:** Prevents retrieval of irrelevant noise chunks that distract the generation model.
- **High/Low Value:** High (0.64+) indicates clean, highly focused top-K context.
- **Decision Impact:** Confirmed that $N \pm 1$ neighbor retrieval did not degrade context quality (Precision@3 improved from 0.6092 $\rightarrow$ 0.6437).

---

### 3. MRR (Mean Reciprocal Rank)
- **What it measures:** The average of reciprocal ranks ($\frac{1}{\text{rank}}$) of the first relevant chunk returned.
- **Why it matters:** Evaluates whether the best answer chunk appears at rank #1 vs rank #3.
- **High/Low Value:** 1.0 means relevant answer is always at rank #1.
- **Decision Impact:** Selected **Statutory Query Expansion** (MRR increased from 0.6592 $\rightarrow$ 0.7126).

---

### 4. Fact Recall@K
- **What it measures:** The percentage of required ground-truth facts (out of all annotated facts) present in the retrieved context window.
- **Why it matters:** Measures raw evidence completeness for multi-fact questions.
- **High/Low Value:** High (0.38+) means most required facts are fetched; Low (<0.20) means incomplete facts.
- **Decision Impact:** Selected **Adaptive Neighbor Retrieval ($N \pm 1$)** (Fact Recall increased from 0.2644 $\rightarrow$ 0.3851).

---

### 5. Complete Answer Rate@K (Primary Decision Metric)
- **What it measures:** The percentage of evaluation questions for which ALL required ground-truth facts are present in the retrieved context.
- **Why it matters:** Determines whether the LLM has 100% of the evidence required to answer without hallucinating.
- **High/Low Value:** High (0.20+) means complete grounding; Low (<0.10) forces generation guesswork.
- **Decision Impact:** **Rejected global BM25 RRF** (Complete Answer dropped from 0.1379 $\rightarrow$ 0.1034) and **promoted Adaptive N±1** (Complete Answer increased from 0.1379 $\rightarrow$ 0.2069).

---

### 6. Semantic-Only Match Rate
- **What it measures:** Percentage of retrieved chunks that are semantically related to the topic but contain NONE of the required ground-truth facts.
- **Why it matters:** Identifies "false friend" chunks that sound relevant but lack specific legal facts.
- **Decision Impact:** Identified why BM25 failed (BM25 fetched high-keyword semantic chunks lacking exact statutory rules).

---

### 7. Token Efficiency ($\frac{\text{Complete Answer Rate}}{\text{Avg Context Tokens}} \times 1000$)
- **What it measures:** Ratio of complete answer quality relative to context token payload.
- **Why it matters:** Prevents solving retrieval completeness by simply dumping 3,600+ tokens into every prompt.
- **Decision Impact:** Proven that $N \pm 1$ neighbor retrieval is far more token-efficient than global Top-10 search.

---

### 8. Latency Audit Metrics (Mean, P50, P95)
- **What it measures:** Total end-to-end retrieval latency, itemized into Query Expansion ($L_{qexp}$), Embedding ($L_{emb}$), Vector Search ($L_{chroma}$), and Neighbor Lookup ($L_{neighbor}$).
- **Why it matters:** Ensures real-time voice UI responsiveness.
- **Target:** P95 total latency `<750ms`. Adaptive N±1 achieved **P95 = 536.6 ms**.
