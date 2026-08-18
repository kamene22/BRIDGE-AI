# Bridge AI — Top-K Retrieval Sensitivity Report

**Date:** 2026-08-14 17:56:36
**Evaluated K Values:** Top-1, Top-3, Top-5, Top-10

---

## 1. Top-K Performance Matrix

| K | Recall@K | Precision@K | MRR | Fact Recall@K | Complete Answer Rate@K | Avg Context Tokens |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Top-1** | 0.2828 | 0.6207 | 0.6207 | 0.2069 | **0.0690** | 368.8 |
| **Top-3** | 0.4362 | 0.6207 | 0.7126 | 0.2644 | **0.1379** | 1093.3 |
| **Top-5** | 0.5362 | 0.6000 | 0.7126 | 0.2874 | **0.1379** | 1825.9 |
| **Top-10** | 0.6190 | 0.5517 | 0.7253 | 0.4483 | **0.2759** | 3633.1 |

## 2. Sensitivity Key Takeaways
- **Top-3 to Top-5 Change:** Complete Answer Rate moves from `0.1379` $\rightarrow$ **`0.1379`** (+0.0% relative gain).
- **Top-3 to Top-10 Change:** Complete Answer Rate reaches **`0.2759`** (Token payload increases from 1093.3 $\rightarrow$ 3633.1 tokens).