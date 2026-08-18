# Bridge AI — Architecture Decision Log (ADR)

This log records major architectural decisions, the empirical evidence evaluated, trade-offs accepted, and production status.

---

## Decision 1: Selection of Gemini Embedding 2 (`models/gemini-embedding-2`)

### Problem
We needed a high-capacity dense embedding model capable of encoding legal statutory language and conversational career queries into a unified vector space.

### Options Considered
- Option A: `text-embedding-004` (768 dimensions)
- Option B: `models/gemini-embedding-2` (3072 dimensions)

### Evidence
Head-to-head evaluation on 29 evaluation queries:
- `text-embedding-004`: MRR = 0.5862, Recall@3 = 0.3103, Precision@3 = 0.4828.
- `models/gemini-embedding-2`: **MRR = 0.6592**, Recall@3 = **0.3621**, Precision@3 = **0.5517**.

### Decision
Select `models/gemini-embedding-2` as the production embedding model.

### Why
Delivered a +12.5% relative gain in MRR and superior legal semantic capture.

### Trade-offs
Higher vector dimensionality (3072d vs 768d) increases vector index storage footprint.

### Status
`PRODUCTION`

---

## Decision 2: 1,500 Character / 200 Character Overlap Chunking

### Problem
Document chunking must balance context completeness against vector granularity. Small chunks split statutory sections; large chunks dilute vector similarity.

### Options Considered
- Option A: `500` chars / `50` overlap
- Option B: `1,000` chars / `150` overlap
- Option C: `1,500` chars / `200` overlap

### Evidence
- `500 / 50`: Fact Recall@3 = 0.1609, Precision@3 = 0.3678.
- `1,000 / 150`: Fact Recall@3 = 0.2184, Precision@3 = 0.4828.
- `1,500 / 200`: **Fact Recall@3 = 0.2414**, **Precision@3 = 0.5517**.

### Decision
Adopt `1,500` characters with `200` character overlap.

### Why
`1,500` characters (~375 tokens) fits complete legal clauses (e.g. Section 42 probation rules) without sentence fragmentation.

### Trade-offs
Fewer total chunks in index (248 chunks), slightly higher token payload per hit.

### Status
`PRODUCTION`

---

## Decision 3: Statutory Query Expansion

### Problem
User queries use informal colloquial language (*"dock pay for being late"*), whereas authoritative corpus documents use formal statutory terminology (*"unauthorized salary deduction Section 19"*).

### Options Considered
- Option A: Raw User Query Vector Search
- Option B: LLM-Based Query Expansion (adds +400ms latency)
- Option C: Rule-Based Statutory Synonym Expansion (`expand_query`)

### Evidence
- Raw Query: MRR = 0.6592, Precision@3 = 0.5517.
- Statutory Expansion: **MRR = 0.7126** (+8.1% gain), Latency overhead = **`<0.01 ms`**.

### Decision
Implement deterministic Statutory Query Expansion.

### Why
Improved retrieval rank of authoritative legal documents with zero measurable latency cost.

### Trade-offs
Requires maintaining domain keyword mapping table (`EXPANSION_MAP`).

### Status
`PRODUCTION`

---

## Decision 4: Rejection of Global BM25 + Dense RRF Hybrid Retrieval

### Problem
Testing whether adding lexical BM25 sparse retrieval via Reciprocal Rank Fusion (RRF $k=60$) recovers answer-bearing chunks missed by dense vector search.

### Options Considered
- Option A: Dense Gemini Vector Retrieval + Expansion
- Option B: Pure BM25 Sparse Retrieval
- Option C: Hybrid Dense + BM25 RRF Fusion ($k=60$)

### Evidence
- Dense Baseline: Complete Answer Rate@3 = **0.1379**, Fact Recall@3 = **0.2644**.
- BM25 Only: Complete Answer Rate@3 = 0.0690, Fact Recall@3 = 0.2529.
- Hybrid RRF: Complete Answer Rate@3 = **0.1034**, Fact Recall@3 = 0.2529.

### Decision
**REJECT GLOBAL BM25 + RRF.**

### Why
BM25 exact-keyword hits frequently retrieved incomplete chunks containing high keyword density (e.g. the word "Section"), diluting top-3 context and dropping Complete Answer Rate from 13.8% $\rightarrow$ 10.3%.

### Trade-offs
Sacrificed 3 BM25-only exact section number hits to protect global complete answer quality.

### Status
`REJECTED`

---

## Decision 5: Adaptive Neighbor Retrieval ($N \pm 1$)

### Problem
Complete Answer Rate@3 was low (13.8%) because statutory rules span adjacent paragraphs across chunk boundaries. Global Top-10 doubled completeness (27.6%) but consumed 3,633 tokens per turn.

### Options Considered
- Option A: Global Top-10 Retrieval (3,633 tokens)
- Option B: Always N±1 Expansion (2,438 tokens)
- Option C: Adaptive N±1 Expansion (Triggers: Statutory terms, sentence boundaries)

### Evidence
- Baseline Top-3: Complete Answer = 13.8%, Fact Recall = 0.2644, Avg Tokens = 1,093.
- Global Top-10: Complete Answer = 27.6%, Fact Recall = 0.4483, Avg Tokens = 3,633.
- Adaptive N±1: **Complete Answer = 20.7%**, **Fact Recall = 0.3851**, **Avg Tokens = 2,425**, **P95 Latency = 536.6 ms**.

### Decision
Adopt Adaptive Neighbor Retrieval ($N \pm 1$) with feature flag `ENABLE_NEIGHBOR_RETRIEVAL`.

### Why
Captures multi-clause statutory context while saving **1,208 tokens per query (33% token savings vs Top-10)** with **`<0.1ms` neighbor lookup latency**.

### Trade-offs
Increases context token payload from 1,093 $\rightarrow$ 2,425 tokens per query when triggers fire.

### Status
`PRODUCTION`
