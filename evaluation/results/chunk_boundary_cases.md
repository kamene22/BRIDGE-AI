# Bridge AI — Concrete Chunk Boundary Case Traces

This document traces specific evaluation queries where required facts are split across chunk boundaries (Chunk $N$ and Chunk $N+1$) in `exp_chunks_1500_200`.

---

## 1. Case Study 1: `GE-004` (Statutory Minimum Wage Rates)

- **User Question:** *"What is the minimum wage in Kenya for someone working in Nairobi?"*
- **Source Document:** `kenya_minimum_wage_gazette_guide.md`
- **Chunk Boundary Trace:**
  - **Chunk $N$ (`c1`):** Details the legal framework under Labour Institutions Act and lists Zone 1 Nairobi general laborer minimum wage (`KES 15,201.65/month`).
  - **Chunk $N+1$ (`c2`):** Continues with artisan rates (`KES 17,200.50`), 15% statutory housing allowance rules, and Labour Inspectorate enforcement.
- **Impact:** Top-3 retrieval fetches Chunk $N$, but omits Chunk $N+1$. Neighbor retrieval ($N+1$) reunites the artisan rates and housing allowance rules with the general laborer baseline.

---

## 2. Case Study 2: `GE-005` (Written Statement of Particulars)

- **User Question:** *"What rights do I have if my employer hasn't given me a written contract after 3 months?"*
- **Source Document:** `Employment Act.pdf` & `bridge_ai_career_handbook_expanded.md`
- **Chunk Boundary Trace:**
  - **Chunk $N$ (`c5`):** Details Section 9 statutory requirement for written contract within 2 months of employment.
  - **Chunk $N+1$ (`c6`):** Details Section 10 statement of particulars content and reporting non-compliance to the Ministry of Labour Inspectorate.
- **Impact:** Retrieving Chunk $N$ alone provides the 2-month rule but misses the Ministry of Labour dispute reporting procedure. Neighbor retrieval ($N+1$) completes the required evidence.

---

## 3. Case Study 3: `GE-006` (Unlawful Wage Deductions & Tardiness Fines)

- **User Question:** *"Is it true that an employer in Kenya can dock my pay for being late?"*
- **Source Document:** `Employment Act.pdf`
- **Chunk Boundary Trace:**
  - **Chunk $N$ (`c12`):** Details Section 19 authorized statutory deductions (PAYE, NSSF, SHA).
  - **Chunk $N+1$ (`c13`):** Details Section 19(2) prohibition of unauthorized fines/tardiness deductions without employee consent.
- **Impact:** Chunk $N$ establishes general deduction rules; Chunk $N+1$ supplies the explicit prohibition of lateness fines. Neighbor retrieval ($N+1$) joins the primary rule with the specific exception.

---

## 4. Case Study 4: `GE-010` (Procedural Termination & Hearing Rights)

- **User Question:** *"Tell me about the rules around being let go from work in Kenya"*
- **Source Document:** `Employment Act.pdf`
- **Chunk Boundary Trace:**
  - **Chunk $N$ (`c22`):** Details Section 41 notice periods and valid grounds for termination.
  - **Chunk $N+1$ (`c23`):** Details Section 41(2) mandatory procedural hearing requirement and right to union representation.
- **Impact:** Top-3 fetches Section 41 grounds, but misses procedural hearing rights in Chunk $N+1$. Neighbor retrieval ($N+1$) restores complete termination evidence.
