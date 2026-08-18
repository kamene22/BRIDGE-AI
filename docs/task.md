# Task List: Bridge AI Conversational Assistant Implementation

This document outlines the step-by-step technical implementation task list for Bridge AI, a RAG-based conversational AI assistant helping young Kenyans navigate their early professional careers.

---

## Phase 1: Workspace Initialization & Environment Setup
**Goal:** Configure the directory structure, manage dependencies, and set up variables.

- [ ] **Task 1.1: Create Project Directory Structure**
  - [ ] Create the top-level folders:
    - [ ] `corpus/` (Knowledge Base documents)
    - [ ] `src/` (Core codebase)
    - [ ] `src/llm_provider/` (LLM wrappers)
    - [ ] `src/ingestion/` (Text processing and database indexing)
    - [ ] `src/retrieval/` (Retrieval pipeline)
    - [ ] `src/guardrails/` (Safety layer)
    - [ ] `src/generation/` (Prompt construction & LLM calling)
    - [ ] `src/memory/` (Session context management)
    - [ ] `interface/` (User interface code)
    - [ ] `evaluation/` (Evaluation framework)
    - [ ] `evaluation/guardrail_test_sets/` (Safety test datasets)
    - [ ] `evaluation/sessions/` (Layer 4 simulated conversation sets)
    - [ ] `evaluation/judges/` (Custom LLM-as-a-judge system prompts)
- [ ] **Task 1.2: Manage Python Dependencies**
  - [ ] Create `requirements.txt` with appropriate library versions:
    - `fastapi` & `uvicorn` (backend server)
    - `streamlit` (frontend demo app)
    - `chromadb` (vector database)
    - `google-generativeai` (Gemini model interface)
    - `pydantic` (data validation)
    - `python-dotenv` (environment variables config)
    - `pytest` & `requests` (testing)
  - [ ] Set up a virtual environment (`venv`) inside WSL and activate it.
  - [ ] Run `pip install -r requirements.txt` to install dependencies.
- [ ] **Task 1.3: Set Up Configuration & Environment Variables**
  - [ ] Create `.env` file containing local configurations:
    - `GEMINI_API_KEY`: API credentials for Google AI Studio.
    - `CHROMA_DB_PATH`: Local database storage directory.
    - `EMBEDDING_MODEL`: Name of the Gemini embeddings model.
    - `GENERATION_MODEL`: Gemini 2.5 Flash model identifier.

---

## Phase 2: Knowledge Base Compilation (Corpus)
**Goal:** Prepare and curate the 6 local Markdown files describing employment rules and professional standards in Kenya.

- [ ] **Task 2.1: Compile Kenyan Legal and Practical Guides**
  - [ ] Create `corpus/employment_act_2007.md`: Summarize sections on employment contracts, maximum probation length (6 months), extension rules, working hours, and termination procedures in Kenya.
  - [ ] Create `corpus/ajira_digital_guide.md`: Detail official government employment schemes, training offerings, and online job platforms.
  - [ ] Create `corpus/brightermonday_cv_interview.md`: List CV structures, optimization checklists, common interview types, and preparation tips.
  - [ ] Create `corpus/job_scam_red_flags.md`: List common indicators of job fraud in Kenya, including upfront payments (e.g., medical checks, registration fees), non-official domain emails, and unverifiable recruiters.
  - [ ] Create `corpus/first_salary_financial_literacy.md`: Include guidance on PAYE tax brackets, NHIF/NSSF statutory deductions, and basic personal budgeting.
  - [ ] Create `corpus/hidden_curriculum_kenya.md`: Author a guide for first-generation white-collar professionals covering workplace norms, dress codes, communication formats, and managing relationship hierarchies.

---

## Phase 3: Core Retrieval & Vector Database Ingestion
**Goal:** Extract text, split into semantic chunks, embed using Gemini, and index in ChromaDB.

- [ ] **Task 3.1: Implement Document Loader & Splitter**
  - [ ] Write `src/ingestion/build_index.py` loader parsing markdown/text files.
  - [ ] Set up semantic text splitting: chunks of ~250-300 tokens with a 10% overlap to preserve context at segment boundaries.
- [ ] **Task 3.2: Configure Embedding generation & Indexing**
  - [ ] Write integration logic with Gemini Embeddings API.
  - [ ] Construct the local vector storage database utilizing ChromaDB.
  - [ ] Store chunk metadata (source file name, relative line numbers, title).
  - [ ] Verify that running `build_index.py` correctly populates vectors.

---

## Phase 4: Core Pipeline & Thin LLM Provider Abstraction
**Goal:** Create a provider layer for model independence and implement basic retrieval workflows.

- [ ] **Task 4.1: Build Provider Wrapper**
  - [ ] Implement `src/llm_provider/provider.py` wrapping Gemini API calls.
  - [ ] Define customizable parameters: model selection, temperature, top_p, and max output tokens.
  - [ ] Implement a mock mode allowing pipeline verification without requiring a live API key.
- [ ] **Task 4.2: Build Retrieval Module**
  - [ ] Implement search logic in `src/retrieval/retrieval.py` querying ChromaDB.
  - [ ] Configure query embedding lookup and extract top 5-6 nearest-neighbor chunks.
  - [ ] Format retrieved sources into structured metadata for prompt consumption.

---

## Phase 5: Input & Output Guardrails
**Goal:** Implement the validation filters wrapping query input and generation output.

- [x] **Task 5.1: Implement Out-of-Scope Input Guardrail**
  - [x] Write `src/guardrails/out_of_scope.py` check.
  - [x] Set up classification prompt checking if input matches defined topics (job search, early career, scams, workplace rules).
  - [x] Tune safety parameters to prioritize permissive routing over strict rejection.
- [x] **Task 5.2: Implement Scam Detection Input Guardrail**
  - [x] Write `src/guardrails/scam_detection.py` check.
  - [x] Set up a checklist classifier scanning for requests for money, suspicious contract details, or unofficial recruiters.
  - [x] If flagged, append warning instruction blocks to the downstream prompt context.
- [x] **Task 5.3: Implement Legal Boundary Output Guardrail**
  - [x] Write `src/guardrails/legal_boundary.py` check.
  - [x] Inspect generated LLM draft answers for definitive legal claims.
  - [x] If flagged, route draft through correction rewrite prompt replacing assertions with safe references to official bodies (Ministry of Labour).

---

## Phase 6: Session Memory & Orchestrated Pipeline
**Goal:** Manage conversation history and orchestrate execution flow.

- [x] **Task 6.1: Manage Conversation Memory**
  - [x] Implement `src/memory/memory.py` managing historical sliding window of last 5 turns.
  - [x] Construct user profile builder capturing career details (e.g. current target, experience level) explicitly stated in the conversation.
- [x] **Task 6.2: Build Orchestration Pipeline**
  - [x] Write main pipeline driver in `src/pipeline.py`.
  - [x] Implement the sequence:
    1. Parse query and load conversation memory.
    2. Check Out-of-Scope (Exit and return redirect response if triggered).
    3. Check Scam Detection (Flag and prepare custom context instructions if triggered).
    4. Retrieve relevant chunks from ChromaDB and merge context.
    5. Construct final prompt combining: System Prompt + Scam Prompt (if active) + Memory Context + Retrieved Chunks.
    6. Generate draft response using LLM Provider.
    7. Check Legal Boundary (Execute corrective rewrite if triggered).
    8. Return response along with source list and trace metadata.

---

## Phase 7: Streamlit Chat Interface
**Goal:** Design and build the front-end demonstration application.

- [x] **Task 7.1: Build Chat Application**
  - [x] Create `interface/app.py` utilizing Streamlit.
  - [x] Configure standard interactive chat interface components.
  - [x] Display source attribution cards linking back to the relevant corpus files.
- [x] **Task 7.2: Style and Polish Interface**
  - [x] Style the app with custom CSS (modern styling, clean typography, responsive layout).
  - [x] Create side panels detailing system metadata:
    - Active guardrail flags (triggered/passed).
    - Source chunks returned by retrieval.
    - Current session user profile and sliding window memory.
    - Performance metrics (response latency in ms).

---

## Phase 8: Evaluation Framework Implementation
**Goal:** Implement the multi-layered evaluation suite verifying systemic, safety, quality, and behavior impact.

- [x] **Task 8.1: Create Benchmark Test Sets**
  - [x] Create `evaluation/benchmark_questions.json` with 30-50 curated test cases covering each corpus document.
  - [x] Create `evaluation/guardrail_test_sets/` with 15-20 balanced pass/fail test items for each guardrail classifier.
  - [x] Create `evaluation/sessions/` with 5-8 multi-turn conversation simulation scripts.
- [x] **Task 8.2: Build Evaluation Runner & Judges**
  - [x] Create `evaluation/run_evaluation.py` script.
  - [x] Implement Layer 1 (Systemic): Log response time, stability, and token footprint.
  - [x] Implement Layer 2 (Safety): Compute accuracy, precision, and recall metrics for all guardrail classifiers.
  - [x] Implement Layer 3 (Response Quality): Set up LLM-as-a-judge prompts verifying Context Recall, Context Relevance, Faithfulness, and Answer Relevance.
  - [x] Implement Layer 4 (Behavior Impact): Simulate conversation sessions and score outcomes.
  - [x] Implement sweep logic to run evaluation against different chunk sizes (e.g. 150 vs 250 vs 400 tokens) and retrieval counts (K=4 vs K=6) to optimize parameters.

---

## Phase 9: Verification & System Audit
**Goal:** Conduct final testing and system validation.

- [x] **Task 9.1: Run Quality Sweeps**
  - [x] Execute `python evaluation/run_evaluation.py` and analyze generated metrics reports.
  - [x] Audit response speed (latency), safety triggers, and hallucination rates.
  - [x] Iteratively tune prompt wording and retrieval parameters if scores are lower than expected.
- [x] **Task 9.2: Perform Final Walkthrough**
  - [x] Run Streamlit interface, chat through multiple realistic scenarios, and verify output correctness.
  - [x] Document all results in `walkthrough.md`.
