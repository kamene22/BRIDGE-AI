# Bridge AI — System Limitations & Trade-Off Analysis

This document provides an honest engineering assessment of the current system limitations, trade-offs, and operational boundaries of Bridge AI.

---

## 1. Corpus Coverage Limitations
- **Scope Restriction:** The knowledge base covers Kenyan statutory employment law (Cap. 226), minimum wage schedules, HELB compliance, payslip taxes, job scams, and general career advice. It does **not** cover specialized sector-specific collective bargaining agreements (CBAs), international labor conventions, or private corporate internal HR handbooks.
- **Freshness & Gazette Risk:** Minimum wage gazette notices and statutory tax rates (e.g. SHA 2.75%) are subject to government policy updates. Changes require periodic manual ingestion into `corpus/`.

---

## 2. Retrieval & Complete Answer Rate Limitations
- **Multi-Document Splitting:** Queries requiring facts distributed across distinct source files (e.g. combining statutory legal rights from `Employment Act.pdf` and salary negotiation advice from `BrighterMonday_Job_Search_Advice_RAG_Corpus.pdf`) require multi-query retrieval or document pre-routing.
- **Complete Answer Rate Ceiling:** Current production Complete Answer Rate@3 stands at **20.69%**. While Fact Recall is high (**0.3851**), 79.3% of queries retrieve a partial subset of required ground-truth facts.

---

## 3. Context Payload & Token Trade-Offs
- **Token Inflation under $N \pm 1$:** Adaptive Neighbor Retrieval expands context from **1,093 tokens $\rightarrow$ 2,425 tokens** per query when triggers fire. While significantly cheaper than Global Top-10 (3,633 tokens), it increases LLM prompt context length.
- **Irrelevant Sentence Ingestion:** Retrieving adjacent chunks ($N-1, N+1$) occasionally ingests neighboring sentences that are topically adjacent but not directly answer-bearing.

---

## 4. API Latency & External Dependency Risks
- **External Embedding API Latency:** `models/gemini-embedding-2` API calls represent **90%+ of total retrieval latency** (~455ms out of 536ms total P95 latency). Network latency to Google Gemini endpoints impacts real-time voice responsiveness.
- **Rate Limits:** System throughput is bound by Gemini API quota rate limits.

---

## 5. Ground-Truth Evaluation Set Limitations
- **Over-Specified Annotations:** 3 of the 12 incomplete evaluation cases expect secondary background facts (e.g. historical context) that are useful but not strictly necessary for a direct user answer.
- **Sample Size:** Evaluation set contains 29 test cases (66 facts). While sufficient for controlled benchmarking, larger 100+ case datasets are required for edge-case coverage.
