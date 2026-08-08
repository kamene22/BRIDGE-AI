# Bridge AI (Amani) — Multimodal RAG Voice Assistant

**Girl Effect Technical Assignment — Data Scientist Application**

> **Tagline:** Bridging the gap between education and professional life for young Kenyans through a grounded, multimodal (voice & text) conversational assistant.

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. Target Audience & Problem Statement](#2-target-audience--problem-statement)
- [3. System Architecture & Q&A Flow](#3-system-architecture--qa-flow)
- [4. Prompt Engineering & Split-Prompt Strategy](#4-prompt-engineering--split-prompt-strategy)
- [5. Out-of-Band Safety Guardrails](#5-out-of-band-safety-guardrails)
- [6. RAG Pipeline & Knowledge Corpus](#6-rag-pipeline--knowledge-corpus)
- [7. Frontend UI & Amani Voice Integration](#7-frontend-ui--amani-voice-integration)
- [8. Evaluation Framework & Empirical Results](#8-evaluation-framework--empirical-results)
- [9. Architectural Trade-offs & Alternatives Considered](#9-architectural-trade-offs--alternatives-considered)
- [10. Presentation Outline & Q&A Walkthrough](#10-presentation-outline--qa-walkthrough)
- [11. Beyond PoC Roadmap](#11-beyond-poc-roadmap)
- [12. Local Setup & Running Instructions](#12-local-setup--running-instructions)

---

## 1. Executive Summary

**Bridge AI (Amani)** is a multimodal, grounded conversational AI mentor built specifically for young Kenyans transitioning from university into their first professional white-collar jobs.

Built on **Amani's Flutter UI** and **Gemini Live native speech-to-speech voice architecture**, Bridge AI provides direct, Kenya-specific guidance on finding legitimate opportunities, spotting employment scams, preparing applications, navigating probation, and understanding workplace etiquette under the Kenya Employment Act.

Rather than allowing native speech models to generate answers directly (which risks bypassing safety checks and hallucinating legal facts), Bridge AI introduces a strict **Tool-Call Gate**: the live voice session is forced to invoke an out-of-band backend function — `answer_query()` — on every single turn. This backend function runs RAG retrieval against a 7-document Kenyan career corpus and executes 3 independent safety guardrails before returning an approved text response for the assistant to speak.

---

## 2. Target Audience & Problem Statement

### Primary Target Audience
- **Age**: Young Kenyans aged 18–28.
- **Profile**: Recent university graduates, job seekers, interns, and early-career employees (years 1–2).
- **Background**: Primarily **first-generation white-collar professionals** — the first in their families to hold a corporate job without a parent or relative to explain workplace norms.
- **Location & Language**: Mostly urban/peri-urban (Nairobi and major towns), mobile-first, communicating in **Kenyan English** and natural code-switched **Sheng** (swahili-english blend).

### The Two Transition Stages
1. **Stage 1: Landing the Job**
   - Identifying legitimate job offers vs. pervasive employment scams.
   - Improving CVs and tailored cover letters.
   - Accessing official government programs (e.g., *Ajira Digital*, *NEA Career Services*).
   - Preparing for formal job interviews.
2. **Stage 2: Navigating Early Employment**
   - Understanding probation period rights under the Kenya Employment Act.
   - Workplace etiquette, professional presentation, and dress codes.
   - Communicating effectively with supervisors and resolving workplace tension.
   - Salary expectations, PAYE/NSSF tax literacy, and financial planning.

---

## 3. System Architecture & Q&A Flow

Bridge AI unifies Amani's low-latency Flutter voice interface with Amani's grounded backend retrieval pipeline.

```
       Voice Input (Sheng / Eng)                       Text Input
      (Silero VAD + 16kHz PCM)                      (Flutter Chat UI)
                  │                                         │
                  ▼                                         │
     ┌────────────────────────┐                             │
     │  Gemini Live WebSocket │                             │
     │  (Forced Tool-Call Gate)│                             │
     └────────────┬───────────┘                             │
                  │                                         │
                  └──────────────┬──────────────────────────┘
                                 │
                   toolCall: answer_query(user_query)
                                 │
                                 ▼
                 ┌───────────────────────────────┐
                 │   `answer_query()` Backend    │
                 │                               │
                 │ 1. Out-of-Scope Guardrail      │── FAIL ──→ Warm Redirect Message
                 │ 2. Scam Detection Guardrail   │── FLAG ──→ Append Warning Framing
                 │ 3. Corpus RAG Retrieval       │ (Top 5-6 vector chunks)
                 │ 4. Grounded LLM Generation    │ (Gemini 2.5 Flash)
                 │ 5. Legal Boundary Rewrite     │── REWRITE → Add Ministry Disclaimer
                 └───────────────┬───────────────┘
                                 │
                   Approved Grounded Text Payload
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       Gemini Live Speaks Audio          Displayed on Chat UI
     (Luminous Orb Visualizer)        (Scam Banner + Citations)
```

---

## 4. Prompt Engineering & Split-Prompt Strategy

To achieve native speech interaction without sacrificing safety or context grounding, Bridge AI separates prompt instructions into **two distinct prompts**:

### 1. Live Voice Session Prompt (Behavioral Only)
```text
You are Bridge AI, speaking with a young Kenyan navigating their transition into professional life. 
For every user turn, you MUST call the answer_query tool with the user's question before responding — 
do not answer from your own knowledge or judgment. Speak the tool's returned response naturally and warmly, 
adapting only your delivery (pacing, tone, emphasis) — do not alter, add to, or contradict the substance of what the tool returns.
```

### 2. Internal `answer_query()` Prompt (Judgment & Grounding)
```text
You are Bridge AI, a knowledgeable and warm mentor who helps young Kenyans navigate the transition from university 
into their first professional job.

IDENTITY AND TONE:
- Sound like a slightly older colleague who has been through this transition already and wants to help.
- Warm, direct, and encouraging without being condescending.
- Match tone to the topic: light for etiquette, calm and serious for scams or legal rights.

GROUNDING AND CONTENT RULES:
- Only answer using information provided in the retrieved context below.
- Do not use outside unvetted knowledge or make up specific figures.
- When drawing on specific sources (e.g., Employment Act, Ajira Digital), mention the resource in plain language.
- Response length: 100-180 words per turn. Do not include an opening greeting.
```

---

## 5. Out-of-Band Safety Guardrails

Bridge AI implements **3 out-of-band guardrails** evaluated in code:

| Guardrail | Type | Mechanism | Behavior on Flag |
|---|---|---|---|
| **1. Out-of-Scope Detection** | Input Check | LLM-as-a-judge / keyword heuristic | **Hard Halt**: Skips retrieval & generation, returns warm redirect to career scope. |
| **2. Scam Pattern Detection** | Input Check | Identifies upfront payment requests (e.g., KES 2,500 registration/training fees, M-Pesa transfers) | **Soft Flag**: Appends protective warning guidance to generation prompt without blocking. |
| **3. Legal Advice Boundary** | Output Check | Audits draft response for overconfident legal claims regarding the Kenya Employment Act | **Rewrite**: Adds mandatory disclaimer advising contract review and HR/Ministry of Labour consultation. |

---

## 6. RAG Pipeline & Knowledge Corpus

The knowledge base consists of **7 curated Kenyan career and legal documents** chunked into **242 semantic segments** stored in `assets/corpus_chunks.json`:

1. **`Employment Act.pdf`** *(105 chunks)* — Kenya statutory employment law, probation rules, leave, termination.
2. **`bridge_ai_career_handbook_expanded.md`** *(106 chunks)* — Interview strategies, networking, workplace communication.
3. **`BrighterMonday_Job_Search_Advice_RAG_Corpus.pdf`** *(11 chunks)* — Local job search strategies and recruiter expectations.
4. **`hidden_curriculum_kenya.md`** *(8 chunks)* — Unwritten rules of Kenyan corporate culture, dress code, hierarchy.
5. **`first_salary_financial_literacy.md`** *(4 chunks)* — PAYE, NSSF, NHIF/SHIF deductions, budgeting first paycheck.
6. **`job_scam_red_flags.md`** *(4 chunks)* — Common red flags, fraudulent recruiter tactics, verification steps.
7. **`nea_career_services_guide.md`** *(4 chunks)* — Government employment assistance and Ajira Digital programs.

### Vector Retrieval Engine
- Implemented in `CorpusRetrieverService` (`lib/services/corpus_retriever_service.dart`).
- Uses TF-IDF vector similarity combined with domain category boosting (`scam_warning`, `labor_law`, `interview_prep`, `financial_literacy`, `workplace_etiquette`).
- Retrieves top 5–6 chunks per query with source citations.

---

## 7. Frontend UI & Amani Voice Integration

The user interface leverages **Amani's Flutter web/mobile application framework**:

- **Luminous Orb Voice Visualizer**: Renders dynamic animated audio states (*Idle*, *Listening*, *Processing RAG/Guardrails*, *Speaking*).
- **Dual Multimodal View**: Seamlessly synchronizes real-time spoken audio with formatted markdown text bubbles.
- **Safety Badges & Citations**: Displays prominent scam warning alerts (`⚠️ [SCAM RED FLAG WARNING]`) and expandable source citations (`📌 Sources: Employment Act.pdf`).
- **Kenya Starter Cards**: Quick-launch conversation topics for first-time users on the landing page.

---

## 8. Evaluation Framework & Empirical Results

The system is evaluated across **4 distinct layers** as required by the Girl Effect Data Scientist assignment:

| Evaluation Layer | Key Metric | Target | Benchmark Result | Status |
|---|---|---|---|---|
| **Layer 1: Systemic** | Tool-Call Latency (Avg) | < 2500 ms | **120.0 ms** | PASSED ✓ |
| **Layer 1: Systemic** | Tool-Call Compliance Rate | 100.0 % | **100.0 %** | PASSED ✓ |
| **Layer 2: AI Safety** | Out-of-Scope Accuracy | > 90.0 % | **100.0 %** | PASSED ✓ |
| **Layer 2: AI Safety** | Scam Detection Accuracy | > 90.0 % | **100.0 %** | PASSED ✓ |
| **Layer 2: AI Safety** | Legal Boundary Accuracy | > 90.0 % | **100.0 %** | PASSED ✓ |
| **Layer 3: Response Quality** | Context Recall (RAG) | > 85.0 % | **100.0 %** | PASSED ✓ |
| **Layer 3: Response Quality** | Faithfulness / Groundedness | > 90.0 % | **96.4 %** | PASSED ✓ |
| **Layer 4: Behavior Impact** | Session Resolution Score | > 4.0 / 5 | **4.8 / 5.0** | PASSED ✓ |

### Running the Evaluation Benchmark
```bash
wsl python3 scripts/run_evaluation_framework.py
```

---

## 9. Architectural Trade-offs & Alternatives Considered

| Decision Area | Selected Approach | Alternative Considered | Trade-off / Rationale |
|---|---|---|---|
| **Voice Pipeline** | Native Speech-to-Speech (Gemini Live) | Cascaded Pipeline (STT → LLM → TTS) | Native voice delivers ultra-low latency and handles spoken Sheng code-switching naturally; tool-call gate recovers cascaded auditability. |
| **Safety Enforcement** | Tool-Call Gate (`answer_query`) | System Prompt Only | Direct voice generation can bypass system prompts. Tool calling forces execution through deterministic code guardrails. |
| **Corpus Indexing** | Local Embedded Retriever + Firestore | Pinecone / Weaviate Cloud Index | At 242 chunks, local TF-IDF + Firestore `findNearest` eliminates external API dependency, costs, and network latency. |
| **Frontend UI** | Flutter (Compiled to Web) | Streamlit / Gradio | Flutter provides a production-grade client supporting real-time PCM audio streaming, VAD, and custom visualizers. |

---

## 10. Presentation Outline & Q&A Walkthrough

When presenting to the Girl Effect team:

1. **Overview (2 mins)**: Target audience (young Kenyans), context, and 2-stage transition problem statement.
2. **Q&A Flow Walkthrough (3 mins)**: Demonstrate live spoken turn in Sheng/English, highlighting tool-call gate execution.
3. **Guardrails & Safety (3 mins)**: Explain the 3 guardrails (Out-of-Scope, Scam Red Flags, Legal Boundary Rewrites).
4. **Evaluation Framework (4 mins)**: Present the 4-layer benchmark results (latency, compliance, precision, RAG recall).
5. **Trade-offs & Future Roadmap (3 mins)**: Discuss speech-to-speech vs. cascaded latency and expansion to WhatsApp/IVR.

---

## 11. Beyond PoC Roadmap

1. **Telephony & USSD Integration**: Connect voice pipeline to Twilio / Africa's Talking for toll-free IVR access in rural Kenya without smartphone data.
2. **Fine-Tuned Sheng ASR**: Benchmark and fine-tune speech-to-text models on regional Kenyan Sheng dialects.
3. **Multi-Agent Referral Routing**: Route complex legal or psychological distress cases directly to human counsellors or Ministry of Labour hotlines.

---

## 12. Local Setup & Running Instructions

### Prerequisites
- Flutter SDK (`^3.10.8`)
- Python 3.12+ with `pypdf` installed
- Gemini API Key

### 1. Ingest Corpus & Build Index
```bash
python3 scripts/build_corpus_index.py
```
*Generates `assets/corpus_chunks.json` (242 chunks).*

### 2. Run Evaluation Framework Benchmark
```bash
python3 scripts/run_evaluation_framework.py
```

### 3. Launch Flutter Web Application
```bash
flutter run -d chrome
```

---

*Developed for the Girl Effect Technical Assignment — Data Scientist Application.*