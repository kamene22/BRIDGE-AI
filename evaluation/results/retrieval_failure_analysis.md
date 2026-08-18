# Bridge AI — Stage 5: Systematic Retrieval Failure Analysis Report

**Date:** 2026-08-14 16:03:44
**Evaluated Collection:** `exp_chunks_1500_200` (Winning Chunk Configuration)
**Ground-Truth Dataset:** 29 Test Cases

---

## 1. Executive Summary
Across 29 ground-truth retrieval cases, **3 cases (10.3%)** achieved complete answer grounding in top-3 context, while **26 cases (89.7%)** exhibited partial grounding or false semantic matches.

## 2. Failure Root Cause Breakdown

| Test ID | Question | Root Cause Category | Fact Recall@3 | MRR |
| :--- | :--- | :--- | :---: | :---: |
| `GE-001` | *"How long is the probation period legally capped at in Kenya?"* | Partial Grounding (some facts retrieved, but context incomplete) | 0.33 | 1.00 |
| `GE-004` | *"What is the minimum wage in Kenya for someone working in Nairobi?"* | Vocabulary Gap / Term Mismatch (query terms disconnected from corpus vocabulary) | 0.00 | 0.00 |
| `GE-005` | *"What rights do I have if my employer hasn't given me a written contract after 3 months?"* | False Semantic Match (high vector similarity, missing ground-truth statutory facts) | 0.67 | 1.00 |
| `GE-006` | *"Is it true that an employer in Kenya can dock my pay for being late?"* | Partial Grounding (some facts retrieved, but context incomplete) | 0.33 | 1.00 |
| `GE-007` | *"What is the maximum number of working hours per week in Kenya?"* | False Semantic Match (high vector similarity, missing ground-truth statutory facts) | 0.33 | 0.50 |
| `GE-008` | *"What leave entitlements do I have in my first year of employment?"* | False Semantic Match (high vector similarity, missing ground-truth statutory facts) | 0.67 | 1.00 |
| `GE-009` | *"What should I check before signing an employment contract?"* | Partial Grounding (some facts retrieved, but context incomplete) | 0.33 | 1.00 |
| `GE-010` | *"Tell me about the rules around being let go from work in Kenya"* | Partial Grounding (some facts retrieved, but context incomplete) | 0.67 | 1.00 |
| `GE-011` | *"What does Section 42 of the Employment Act say?"* | False Semantic Match (high vector similarity, missing ground-truth statutory facts) | 0.00 | 1.00 |
| `GE-012` | *"How do I write a good CV for a bank job in Kenya?"* | Partial Grounding (some facts retrieved, but context incomplete) | 0.00 | 0.33 |
| `GE-013` | *"What government programs help young people find jobs in Kenya?"* | False Semantic Match (high vector similarity, missing ground-truth statutory facts) | 0.00 | 0.50 |
| `GE-015` | *"A recruiter asked me to send KES 3,000 via M-Pesa for a training kit before I start. Is this normal?"* | Partial Grounding (some facts retrieved, but context incomplete) | 0.33 | 1.00 |
| `GE-016` | *"I found a data entry job paying KES 120,000 per month with no experience needed. Should I apply?"* | Vocabulary Gap / Term Mismatch (query terms disconnected from corpus vocabulary) | 0.00 | 0.00 |
| `GE-017` | *"My employer hasn't paid me for 2 months. Can I take them to court?"* | False Semantic Match (high vector similarity, missing ground-truth statutory facts) | 0.00 | 0.00 |
| `GE-018` | *"My boss keeps making comments about my appearance. What should I do?"* | False Semantic Match (high vector similarity, missing ground-truth statutory facts) | 0.00 | 1.00 |
| `GE-019` | *"Is it safe to share my national ID copy with a recruiter I found on Facebook?"* | False Semantic Match (high vector similarity, missing ground-truth statutory facts) | 0.00 | 1.00 |
| `GE-020` | *"A company wants me to buy products worth KES 5,000 and resell them to friends to earn commission. Is this a real job?"* | Partial Grounding (some facts retrieved, but context incomplete) | 0.00 | 0.50 |
| `GE-027` | *"What happens if I refuse the extension?"* | Vocabulary Gap / Term Mismatch (query terms disconnected from corpus vocabulary) | 0.00 | 0.00 |
| `GE-030` | *"Is that the same for private sector companies?"* | Partial Grounding (some facts retrieved, but context incomplete) | 0.00 | 0.50 |
| `GE-031` | *"Actually, I'm more worried about the dress code. What should I wear to a tech startup?"* | False Semantic Match (high vector similarity, missing ground-truth statutory facts) | 0.00 | 0.33 |
| `GE-033` | *"I'm thinking of leaving my bank job to start a business. How do I resign properly?"* | False Semantic Match (high vector similarity, missing ground-truth statutory facts) | 0.00 | 1.00 |
| `GE-034` | *"What's the HELB repayment process once I start working?"* | False Semantic Match (high vector similarity, missing ground-truth statutory facts) | 0.00 | 1.00 |
| `GE-035` | *"My employer wants me to work on public holidays without extra pay. Is that allowed?"* | Vocabulary Gap / Term Mismatch (query terms disconnected from corpus vocabulary) | 0.00 | 0.25 |
| `GE-036` | *"I have a job interview at Safaricom next week. How should I prepare?"* | False Semantic Match (high vector similarity, missing ground-truth statutory facts) | 0.00 | 1.00 |
| `GE-037` | *"I want to negotiate my salary but I've never done it before. What do I actually say?"* | False Semantic Match (high vector similarity, missing ground-truth statutory facts) | 0.00 | 1.00 |
| `GE-039` | *"My contract ends in 2 weeks and I haven't been told if it will be renewed. What should I do?"* | False Semantic Match (high vector similarity, missing ground-truth statutory facts) | 0.00 | 1.00 |

## 3. Case Studies of Failure Categories

### Case Study 1: Vocabulary & Term Disconnect (`GE-006` - Docking Pay)
- **User Question:** *'Is it true that an employer in Kenya can dock my pay for being late?'*
- **Issue:** Query uses informal phrase 'dock my pay', while the Kenya Employment Act uses statutory terms 'unlawful salary deductions' (Section 19).
- **Impact:** Vector search retrieves general salary deduction sections but ranks specific penalty provisions lower.

### Case Study 2: Sparse Keyword Density (`GE-035` - Public Holiday Pay)
- **Query:** *'My employer wants me to work on public holidays without extra pay. Is that allowed?'*
- **Issue:** The phrase 'public holiday' appears sparingly in the handbook compared to general 'working hours' sections.

## 4. Stage 6 Recommendation: Hybrid BM25 & Reranking Decision
- Dense vector search (`models/gemini-embedding-2`) achieves **`0.7241` MRR** and **`0.3793` Recall@3** on 1,500-char chunks.
- Because failures stem from **statutory vocabulary mismatches** (e.g. 'dock pay' vs 'unlawful deduction'), **Sparse BM25 Keyword Hybrid Search** or **Query Expansion** directly addresses these gaps without incurring +300-600ms cross-encoder reranking latency.