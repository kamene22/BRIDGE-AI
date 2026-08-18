# Bridge AI — Senior AI Engineer Technical Interview Defense

This document prepares engineers to defend every architectural choice, benchmark result, and system trade-off in Bridge AI during technical interviews.

---

### Q1: Why did you choose RAG instead of fine-tuning an LLM?
- **SHORT ANSWER:** Employment law and minimum wage figures require 100% strict factual precision and citation traceability. RAG prevents hallucinations, allows instant document updates without re-training costs, and provides deterministic evidence grounding.
- **DEEPER EXPLANATION:** Fine-tuningParametric memory in LLMs is prone to hallucination and cannot guarantee exact statutory section citations. Employment law guidelines (Cap. 226) and minimum wage figures change via government gazette notices; RAG allows updating ChromaDB in seconds without expensive model retraining.
- **EVIDENCE:** Corpus Gap Repair immediately raised Strict Fact Coverage from 87.9% $\rightarrow$ 97.0% without altering LLM weights.

---

### Q2: Why did you select ChromaDB as your vector store?
- **SHORT ANSWER:** ChromaDB provides lightweight, zero-overhead embedded vector storage with fast metadata filtering and local SQLite persistence, making it ideal for our 248-chunk production collection.
- **DEEPER EXPLANATION:** We needed an embedded vector database that runs in-process with minimal infrastructure overhead while supporting custom distance metrics (Cosine similarity) and rich metadata filtering (`source`, `chunk_index`).
- **EVIDENCE:** ChromaDB vector query latency averaged **`9.47 ms`** per lookup.

---

### Q3: Why `models/gemini-embedding-2` instead of `text-embedding-004`?
- **SHORT ANSWER:** `models/gemini-embedding-2` projects text into a 3072-dimensional space, capturing complex legal semantics significantly better than 768-dimensional models.
- **DEEPER EXPLANATION:** Higher vector dimensionality preserves subtle legal distinctions (e.g. voluntary resignation vs statutory redundancy).
- **EVIDENCE:** Benchmark showed `gemini-embedding-2` achieved **MRR = 0.6592** vs `text-embedding-004` (MRR = 0.5862) — a +12.5% relative quality gain.

---

### Q4: Why 1,500 characters with 200 character overlap for chunking?
- **SHORT ANSWER:** 1,500 characters (~375 tokens) provides optimal window size to hold complete legal sections without clause fragmentation.
- **DEEPER EXPLANATION:** Smaller chunks (500 chars) split statutory provisions (e.g., Section 42 probation limits) across chunk boundaries, resulting in incomplete evidence.
- **EVIDENCE:** 1,500/200 won the chunk quality sweep with **Fact Recall@3 = 0.2414** and **Precision@3 = 0.5517** (vs 500/50 Fact Recall@3 = 0.1609).

---

### Q5: Why implement Statutory Query Expansion?
- **SHORT ANSWER:** Users ask questions in informal conversational language, while legal documents use formal statutory phrasing. Query expansion bridges this vocabulary gap deterministically.
- **DEEPER EXPLANATION:** Appending domain-specific statutory terms (e.g., *"dock pay"* $\rightarrow$ *"unlawful salary deduction Section 19 penalty"*) aligns the query vector with authoritative statutory chunks.
- **EVIDENCE:** Increased **MRR from 0.6592 $\rightarrow$ 0.7126** (+8.1% gain) with **`<0.01 ms` latency cost**.

---

### Q6: Why test BM25 sparse retrieval?
- **SHORT ANSWER:** To test whether exact lexical keyword matching could recover statutory section numbers and 6-digit Paybill numbers that dense vector search ranked lower.
- **DEEPER EXPLANATION:** Dense embeddings can lose exact term density for specific numbers (e.g. *"Section 42"* or Paybill *"200800"*). BM25 provides exact TF-IDF term scoring.
- **EVIDENCE:** BM25 successfully recovered exact section numbers on 3 queries (10.3% of test set).

---

### Q7: Why did global BM25 + Dense RRF hybrid retrieval fail to become production?
- **SHORT ANSWER:** BM25 exact keyword matching frequently retrieved incomplete chunks containing high keyword density, diluting top-3 context and dropping Complete Answer Rate.
- **DEEPER EXPLANATION:** Combining BM25 ranks with Dense ranks via RRF ($k=60$) promoted chunks that contained the word "Section" or "wage" repeatedly but lacked full statutory explanations.
- **EVIDENCE:** Complete Answer Rate@3 dropped from **0.1379 (Dense Baseline) $\rightarrow$ 0.1034 (Hybrid RRF)**. Global BM25 was rejected.

---

### Q8: Why not use a cross-encoder reranker?
- **SHORT ANSWER:** Cross-encoders add +300-600ms latency per query, violating our strict sub-second voice UI latency budget while providing minimal gain over Statutory Expansion.
- **DEEPER EXPLANATION:** Cross-encoders process query-document pairs through full transformer attention layers. In real-time voice applications, +500ms overhead is unacceptable.
- **EVIDENCE:** Statutory Query Expansion achieved MRR = 0.7126 in `<0.01ms`, rendering heavy cross-encoders unnecessary.

---

### Q9: Why was Complete Answer Rate@3 initially so low (13.79%)?
- **SHORT ANSWER:** Evaluation cases expect an average of 2.3 required facts per query, whereas individual 1,500-character chunks hold only 1.2 facts.
- **DEEPER EXPLANATION:** Diagnostic analysis revealed that multi-fact legal queries have required evidence split across adjacent paragraphs (chunk boundaries) or multiple sections.
- **EVIDENCE:** Diagnostic failure analysis proved that 34.5% of failures were caused by chunk boundary evidence splitting.

---

### Q10: What did the corpus gap analysis reveal?
- **SHORT ANSWER:** Revealed that several low-recall queries failed because facts were missing from the raw corpus, not because retrieval failed.
- **DEEPER EXPLANATION:** Raw corpus text gap auditing identified missing Nairobi minimum wage tables, HELB Paybill details, and SHA tax rates.
- **EVIDENCE:** Repairing 4 missing corpus sections raised Strict Fact Coverage from **87.9% $\rightarrow$ 97.0%** and boosted Precision@3 to **0.6322 (+14.6% gain)**.

---

### Q11: What is chunk boundary failure?
- **SHORT ANSWER:** Occurs when a legal provision begins in Chunk $N$ and concludes in Chunk $N+1$, causing top-3 vector search to fetch only half the evidence.
- **DEEPER EXPLANATION:** Vector search evaluates chunks independently. If Chunk $N$ ranks #1 and Chunk $N+1$ ranks #6, top-3 retrieval truncates the legal rule.
- **EVIDENCE:** Concrete examples traced in `chunk_boundary_cases.md` (e.g. `GE-004` minimum wage rules split across `c1` and `c2`).

---

### Q12: Why does neighbor retrieval help?
- **SHORT ANSWER:** It automatically fetches adjacent chunks ($N-1, N+1$) from the same source document, reuniting split statutory clauses.
- **DEEPER EXPLANATION:** Restores structural document continuity without requiring global Top-10 vector searches across unrelated files.
- **EVIDENCE:** Neighbor Retrieval ($N \pm 1$) increased **Complete Answer Rate from 13.8% $\rightarrow$ 24.1%** (+75% relative increase).

---

### Q13: Why $N \pm 1$ neighbor expansion?
- **SHORT ANSWER:** $N \pm 1$ expands context symmetrically (previous paragraph + next paragraph), capturing preceding prerequisites and trailing exceptions.
- **DEEPER EXPLANATION:** Tested $N+1$, $N-1$, and $N \pm 1$. $N \pm 1$ achieved the highest Fact Recall (0.4368) by capturing both context directions.
- **EVIDENCE:** Config D ($N \pm 1$) achieved **Fact Recall = 0.4368** vs $N+1$ (0.3851) and $N-1$ (0.3276).

---

### Q14: Why Adaptive Neighbor Retrieval instead of Always retrieving neighbors?
- **SHORT ANSWER:** Always retrieving neighbors adds +1,345 tokens to every query unconditionally. Adaptive retrieval expands context only when triggers fire.
- **DEEPER EXPLANATION:** Deterministic triggers (`STATUTORY_LEGAL_SIGNAL`, `CHUNK_BOUNDARY_SIGNAL`) detect when legal clauses or truncated sentences require expansion.
- **EVIDENCE:** Adaptive N±1 achieved **Complete Answer Rate = 20.7%** and **Fact Recall = 0.3851** while preserving token efficiency.

---

### Q15: What was the latency impact of Adaptive Neighbor Retrieval?
- **SHORT ANSWER:** Virtually zero latency impact. Neighbor lookup executes in `0.101 ms` via in-memory chunk maps.
- **DEEPER EXPLANATION:** Because neighboring chunk IDs (`{source}_c{index+1}`) are pre-computed during initialization, zero extra ChromaDB or embedding calls are made.
- **EVIDENCE:** Total P95 latency remained fast at **`536.6 ms`** (well below 750ms target).

---

### Q16: What are the current system limitations?
- **SHORT ANSWER:** Multi-document evidence aggregation (combining facts from 2 different PDF files) remains challenging within top-3 context windows.
- **DEEPER EXPLANATION:** If a query requires combining statutory rights from `Employment Act.pdf` and career advice from `hidden_curriculum_kenya.md`, top-3 vector hits may favor one file over the other.
- **EVIDENCE:** Multi-document queries account for 10.3% of remaining incomplete cases.

---

### Q17: What would you improve next?
- **SHORT ANSWER:** Implement document-level pre-routing (routing legal queries to Employment Act and career queries to Handbook) and parent-child hierarchical chunking.
- **DEEPER EXPLANATION:** Document pre-routing ensures dual-index searches allocate quota equally between legal authorities and practical handbooks. Parent-child chunking indexes small 300-char child chunks for vector matching but retrieves 1,500-char parent blocks.

---

### Q18: How would this architecture scale to 100,000 documents?
- **SHORT ANSWER:** Migrate ChromaDB to a distributed vector store (e.g. Qdrant / Milvus), implement HNSW indexing, and add a document-level router.
- **DEEPER EXPLANATION:** At 100k documents, in-memory neighbor maps remain lightweight, but vector search requires sub-graph filtering and distributed HNSW index shards.

---

### Q19: How would you evaluate hallucination and grounding in production?
- **SHORT ANSWER:** Implement an automated LLM-as-a-Judge pipeline checking Groundedness (NLI entailment between generated text and retrieved context) and Citation Accuracy.
- **DEEPER EXPLANATION:** Extract generated claim sentences and check whether each sentence is logically entailed by the retrieved context chunks, flagging un-cited claims.

---

### Q20: How would you monitor this system in production?
- **SHORT ANSWER:** Monitor P50/P95 retrieval latency, embedding API error rates, context token payload lengths, and user thumbs-up/down feedback metrics.
- **DEEPER EXPLANATION:** Set up OpenTelemetry tracing across query expansion, Gemini embedding generation, ChromaDB vector lookup, and LLM synthesis to catch latency spikes immediately.
