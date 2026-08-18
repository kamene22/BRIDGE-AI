# 🇰🇪 Bridge AI — Systematic Evaluation Notes

```text
Bridge AI Evaluation Taxonomy
│
├── Layer 1: Knowledge & RAG
│   ├── Grounding / Accuracy (Baseline: 1.95 / 2.00)
│   └── Retrieval Quality (Baseline: 1.59 / 2.00)
│
├── Layer 2: Safety
│   └── Safety & Legal Boundaries (Baseline: 2.00 / 2.00)
│
├── Layer 3: Conversation & Human Experience
│   ├── Tone & Empathy (Baseline: 1.93 / 2.00)
│   └── Conversational Continuity (Baseline: 1.95 / 2.00)
│
└── Layer 4: User Value
    ├── Target Audience Fit (Baseline: 1.95 / 2.00)
    └── Actionability (Baseline: 1.98 / 2.00)
```

---

## Layer 1: Knowledge & RAG

### 1. Grounding / Accuracy
* **Baseline Performance:** `1.95 / 2.00` (97.5% Accuracy — 🟢 Excellent)
* **Core Function:** Ensures every factual claim regarding Kenyan labour law, statutory deductions, and employment rights is directly supported by verified corpus documents (`Employment Act.pdf`, `first_salary_financial_literacy.md`, `nea_career_services_guide.md`).
* **Key Evaluation Findings:**
  * **Zero Hallucination on Retrieved Context:** When ChromaDB context is retrieved, Gemini faithfully reflects statutory facts (e.g., 6-month probation cap, 21-day annual leave, PAYE/NSSF/SHIF deductions).
  * **Fact Verification vs. Internal Knowledge:** The system correctly avoids fabricating specific statutory section numbers or wage figures when they are not present in the retrieved context.
  * **Identified Gap:** Occasional hallucination occurs only when retrieval is bypassed completely (e.g., falsely claiming Section 42 of the Employment Act was repealed in GE-011).

### 2. Retrieval Quality
* **Baseline Performance:** `1.59 / 2.00` $\rightarrow$ **Post-Optimization: `1.91 / 2.00`** (🟢 Bottleneck Resolved)
* **Core Function:** Evaluates whether retrieval gating (`retrieval_gating.py`) correctly fetches vector chunks from ChromaDB when a query requires factual grounding.
* **Key Evaluation & Optimization Findings:**
  * **Self-RAG Gating Bottleneck Fixed:** Replaced soft keyword heuristics with a Mandatory Grounding Policy (`CORPUS_REQUIRED`). All statutory, legal, contract, probation, pay, and scam queries now **always trigger vector retrieval** (`top_k >= 2`).
  * **Coreference Resolution:** Added query contextualization in `conversation_manager.py`, resolving ambiguous pronouns in multi-turn follow-ups (*"Can they extend it?"*) before querying ChromaDB.
  * **Final Controlled Benchmark:** Raised MRR to **`0.7241`** (+8.7% over baseline), Fact Recall@3 to **`0.2299`** (+25.0% gain), and reduced P95 latency to **`663.5ms`** (-10.2% speedup).

---

## Layer 2: Safety

### 3. Safety & Legal Boundaries
* **Baseline Performance:** `2.00 / 2.00` (100% Compliance — 🟢 Perfect)
* **Core Function:** Protects vulnerable young job seekers from employment scams, unauthorized legal practice, and overclaiming.
* **Key Evaluation Findings:**
  * **Scam Red Flag Detection:** Instant identification of recruitment fraud, including WhatsApp fee requests, upfront M-Pesa registration fees, and unrealistic salary offers.
  * **Legal Disclaimer Ingestion:** Mandatory, non-intrusive legal disclaimers are automatically appended whenever rights or contracts are discussed: *"This is general guidance, not legal advice. For your specific situation, consult a licensed advocate or the Ministry of Labour."*
  * **Non-Overclaiming & Hedging:** The system avoids giving definitive legal declarations (e.g., "you can definitely sue") and instead advises evidence gathering and formal HR alignment.

---

## Layer 3: Conversation & Human Experience

### 4. Tone & Empathy
* **Baseline Performance:** `1.93 / 2.00` (🟢 Excellent)
* **Core Function:** Evaluates adherence to the **Kenyan Big Sis** persona — warm, encouraging, direct, and culturally resonant, while avoiding robotic corporate HR jargon.
* **Key Evaluation Findings:**
  * **Situational Empathy over Therapy-Speak:** Replaces generic empathy templates ("I understand how you feel") with situation-aware validation tailored to early-career workplace anxiety.
  * **Strict Reassurance Penalty:** Automatically penalizes canned phrases like "everyone goes through this" or false promises ("you'll definitely be fine").
  * **Tone Adaptation:** Uses natural Kenyan English & Swahili greetings ("Hujambo!") without sounding overly formal or academic.

### 5. Conversational Continuity
* **Baseline Performance:** `1.95 / 2.00` (🟢 Excellent)
* **Core Function:** Evaluates multi-turn session memory retention, coreference resolution, and topic progression across 3–5 turn conversations.
* **Key Evaluation Findings:**
  * **Coreference Resolution:** Successfully resolves ambiguous pronouns across turns (e.g., resolving *"What happens if I refuse the extension?"* to the probation extension discussed in prior turns).
  * **Multi-Turn Escalation:** When a user provides follow-up context (e.g., manager ignoring a meeting request), the system builds on previous advice without repeating identical steps or resetting the conversation state.
  * **Clean Topic Pivot:** Seamlessly handles user-initiated topic shifts (e.g., pivoting from contract terms to tech startup dress codes).

---

## Layer 4: User Value

### 6. Target Audience Fit
* **Baseline Performance:** `1.95 / 2.00` (🟢 Excellent)
* **Core Function:** Ensures guidance is realistic, accessible, and relevant to young job seekers navigating the Kenyan employment landscape.
* **Key Evaluation Findings:**
  * **Unbiased Baseline Profiling:** Does NOT make unfounded assumptions about the user's background (e.g., assuming they are an intern, fresh graduate, or working at an NGO) unless explicitly stated in the conversation.
  * **Out-of-Scope Guardrails:** Correctly detects and politely redirects off-topic requests (e.g., crypto, sports betting, coding tutorials) back to career mentorship.

### 7. Actionability
* **Baseline Performance:** `1.98 / 2.00` (🟢 Excellent)
* **Core Function:** Verifies that advice provides practical, concrete, and actionable steps the user can execute immediately.
* **Key Evaluation Findings:**
  * **Practical Scripting & Frameworks:** Provides clear verbal scripts for 1-on-1 check-ins, salary negotiation framing, and professional email recovery.
  * **Balanced Next Steps:** Delivers actionable advice naturally without forcing unnecessary bulleted checklists into simple conversational exchanges.
