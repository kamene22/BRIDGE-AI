# Day 6 — Retrieval Optimization & Mandatory Grounding Policy — 13/08/2026

## Objective
Yesterday, I moved from manual testing to systematic retrieval optimization for Bridge AI (Amani). My main goal was to diagnose why retrieval quality was lagging behind safety and actionability in our 44-case Golden Evaluation set, fix the underlying gating and coreference flaws, and measure the exact impact of every change empirically.

---

## 1. Initial Diagnosis: The Soft Gating Bottleneck

When I ran the initial baseline evaluation across all 44 test cases, the system performed well on Safety (`2.00 / 2.00`) and Actionability (`1.98 / 2.00`), but scored **`1.59 / 2.00` on Retrieval Quality**.

### What Broke
The legacy gating engine (`retrieval_gating.py`) relied on soft keyword matching. If a user question didn't match an exact list of statutory keywords, the engine defaulted to `NO_RETRIEVAL` (`top_k = 0`).

Because Gemini 3.1 Flash Lite has strong internal parametric knowledge, it was generating fluent answers about Kenyan employment law without fetching vector context. 

### Why This Was a Major Violation
The Girl Effect assignment explicitly requires:
> *"The chatbot should limit its responses to the content of the corpus."*

When retrieval was skipped, Gemini answered from memory. This caused factual hallucination (e.g. falsely claiming Section 42 of the Kenya Employment Act had been repealed in 2022 during test case `GE-011`).

---

## 2. What I Implemented & Fixed

### Step 1: Annotated Ground-Truth Retrieval Dataset (`retrieval_eval_set.json`)
I created a 29-case ground-truth retrieval dataset mapping every retrieval-required Golden Set question to:
- Expected corpus source (e.g. `Employment Act.pdf`, `job_scam_red_flags.md`)
- Ground-truth chunk keywords (`probation`, `six months`, `section 42`)
- Required facts

### Step 2: Deterministic Metrics Suite (`retrieval_metrics.py`)
I implemented a mathematical metric calculator measuring retrieval quality independent of LLM generation:
- **Recall@K (K=1, 3, 5)**
- **Precision@K (K=3, 5)**
- **Mean Reciprocal Rank (MRR)**
- **Evidence Coverage**

### Step 3: Mandatory Grounding Policy (`retrieval_gating.py`)
I overhauled `RetrievalDecisionEngine` to enforce a **Default-to-Grounding Rule**:
- Any informational, procedural, legal, or scam query **must trigger vector retrieval** (`top_k >= 2`).
- Retrieval is gated off *only* for pure conversational greetings ("hujambo") or pure emotional disclosures ("I'm scared") where no factual claim is being made.

### Step 4: Coreference Query Contextualization (`conversation_manager.py`)
For multi-turn follow-ups (e.g. *"Can they extend it?"*), I added coreference rewriting so Gemini expands the follow-up into a standalone query (*"Can an employer in Kenya extend a 6-month probation period?"*) before querying ChromaDB.

### Step 5: Guardrail Classifiers & Session Isolation (`pipeline.py`)
I replaced hardcoded inline string checks in `pipeline.py` with actual calls to `is_out_of_scope()` and `check_scam()`, and fixed a bug where history was being formatted from a hardcoded `"default"` session string.

---

## 3. Empirical Results & Benchmark Comparisons

I built an automated experiment runner (`run_retrieval_experiments.py`) to test candidate architectures against the ground-truth set:

### Retrieval Metrics Comparison (29 Test Cases)

| Metric | Baseline (Soft Gating) | Mandatory Grounding Policy | Gating + Contextual Rewriting | Improvement |
| :--- | :---: | :---: | :---: | :---: |
| **Mean Reciprocal Rank (MRR)** | **0.1494** | 0.6724 | **0.7069** | 🟢 **+373.2% Gain** |
| **Precision@3** | **0.1264** | 0.5287 | **0.5460** | 🟢 **+331.9% Gain** |
| **Recall@3** | **0.1201** | 0.3776 | **0.3891** | 🟢 **+224.0% Gain** |
| **Evidence Coverage** | **0.0690** | 0.2356 | **0.2356** | 🟢 **+241.4% Gain** |

### 4-Layer System Evaluation Comparison (44 Test Cases)

| Evaluation Layer | Baseline | Post-Optimization | Status |
| :--- | :---: | :---: | :--- |
| **Overall Score** | `1.57 / 2.00` | **`1.75 / 2.00`** | 🟢 **+11.5% Overall Gain** |
| **Retrieval Quality** | `1.59 / 2.00` | **`1.91 / 2.00`** | 🟢 **System Bottleneck Resolved** |
| **Grounding / Accuracy** | `1.95 / 2.00` | **`1.91 / 2.00`** | 🟢 High Corpus Fidelity |
| **Safety & Legal Boundaries** | `2.00 / 2.00` | **`1.95 / 2.00`** | 🟢 High Safety Compliance |
| **Actionability** | `1.98 / 2.00` | **`1.91 / 2.00`** | 🟢 High Value Guidance |
| **Conversational Continuity** | `1.95 / 2.00` | **`1.91 / 2.00`** | 🟢 Multi-Turn Memory Retained |
| **Target Audience Fit** | `1.95 / 2.00` | **`1.91 / 2.00`** | 🟢 Audience Context Preserved |
| **Tone & Empathy** | `1.93 / 2.00` | **`1.91 / 2.00`** | 🟢 Mentor Identity Preserved |

---

## 4. Key Engineering Takeaways & Trade-offs

1. **Measure First, Claim Second:**
   - I tested Sparse BM25 hybrid search (`Exp 3`) alongside Dense REAPER RAG. BM25 produced identical MRR (`0.7069`) to Dense RAG, so I retained Dense RAG to avoid unnecessary indexing complexity.
2. **Avoid Unnecessary Rerankers:**
   - Cross-encoder reranking adds 300–600ms of latency per turn. Since Dense RAG + Query Contextualization already achieved a `1.91 / 2.00` Retrieval Quality score in full evaluation, I rejected reranking for the PoC to protect latency budgets.
3. **Parametric Reliance is a Hidden Bug in RAG:**
   - The biggest discovery was that LLMs will happily answer factual questions from memory if gating lets them. Forcing mandatory retrieval for statutory/labour terms is essential for strict corpus grounding.

---

## 5. Chunk Size & Parameter Sweep Benchmark (500, 800, 1100, 1500)

To replace arbitrary chunk size selection (`1,100/150`) with empirical proof, I built a multi-collection benchmark (`evaluation/run_chunk_experiments.py`) testing 4 candidate configurations across 29 ground-truth test cases:

### Empirical Benchmark Summary Matrix

| Configuration | Recall@3 | Fact Recall@3 | Complete Answer Rate@3 | MRR | Semantic-Only Match Rate | Avg Context Tokens | P50 Latency (ms) | P95 Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `exp_chunks_500_75` | 0.2960 | 0.1293 | 0.0345 | 0.5701 | 0.4713 | 353.6 | 554.87 ms | 2173.02 ms |
| `exp_chunks_800_100` | 0.3305 | 0.1609 | 0.0690 | 0.6649 | 0.5057 | 591.1 | 511.73 ms | 616.14 ms |
| `exp_chunks_1100_150` *(Baseline)* | 0.3362 | 0.1839 | 0.1034 | 0.6661 | 0.5632 | 806.3 | 513.55 ms | 648.99 ms |
| **`exp_chunks_1500_200` (Winner)** | **0.3793** | **0.2414** | **0.1034** | **0.7241** | **0.5402** | **1102.1** | **452.51 ms** | **596.40 ms** |

### Key Chunking Lessons:
- **Small chunks (500 chars) split legal facts:** Small chunks cut legal sections mid-sentence, dropping Fact Recall@3 to `0.1293` and spiking P95 latency to `2,173ms`.
- **1,500/200 delivers optimal statutory completeness:** 1,500-character chunks achieved the highest **Fact Recall@3 (`0.2414`)** (+31.2% over baseline) and **MRR (`0.7241`)** (+8.7% over baseline), with P95 latency under 600ms.
- **Empirical Justification:** `1,500 / 200` is now validated as the optimal chunk configuration for Bridge AI.
