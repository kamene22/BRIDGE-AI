# Day 1 — Backend Testing & Engineering  Notes - 5/8/2026

**Objective**

Today was dedicated to testing the backend end-to-end before moving on to additional features. My goal wasn't to add new functionality, but to understand how the current RAG pipeline behaves with realistic user questions and identify where the system breaks down.

The questions I asked throughout the day weren't random—they were designed to mimic what a recent graduate, intern, or young professional in Kenya would actually ask.

By the end of today, I realised that building a conversational AI is much more about designing knowledge than writing prompts.

---

# Initial Pipeline

At the start of the day, the backend pipeline looked like this:

User Question
→ Retrieval
→ Guardrail
→ Gemini
→ Gu[text](file:///c%3A/Users/user/Downloads/bridge_ai_career_handbook_expanded.md)ardrail
→ Response

On paper this seemed straightforward. If retrieval returned relevant chunks and Gemini generated a grounded response, I assumed the system would naturally produce useful conversations.

Testing quickly proved otherwise.

---

# Test 1 — Is Retrieval Actually Working?

The first thing I wanted to verify was whether ChromaDB was retrieving relevant information.

I tested questions that I knew existed inside the corpus.

Example:

> "What should I wear on my first day at an NGO?"

The response retrieved the Hidden Curriculum guide discussing dress codes across different employer types.

**Observation**

Retrieval was working correctly.

The embedding model was finding relevant sections.

At this point I became more confident that the retrieval pipeline itself wasn't the weak link.

---

# Test 2 — The Conversation Didn't Feel Human

Although retrieval was correct, the responses immediately felt robotic.

Typical response:

> "Based on Kenyan career & workplace guidelines..."

or

> "According to Hidden Curriculum Kenya..."

Technically nothing was wrong.

From a user experience perspective, however, it felt like I was talking to a document search engine rather than a mentor.

This became my first UX problem.

**Lesson**

Users shouldn't feel retrieval happening.

Retrieval is an implementation detail.

The conversation should feel natural while citations remain available internally for evaluation and debugging.

---

# Test 3 — Improving the System Prompt

I spent some time redesigning the system prompt.

My goal wasn't to make the AI "friendlier."

Instead, I wanted Bridge AI to behave like an experienced colleague rather than a search engine.

The updated prompt encouraged the model to:

- acknowledge the user's situation
- synthesize information instead of copying chunks
- provide practical next steps
- ask one thoughtful follow-up question
- avoid exposing retrieval mechanics

The responses became noticeably warmer.

However, another issue appeared.

---

# Test 4 — Gemini Still Copied Retrieved Text

Despite the new prompt, some responses still looked like this:

> "Section 42..."

followed by large portions of the retrieved chunk.

This surprised me.

I initially assumed the prompt wasn't strong enough.

After several tests I realised something important.

Gemini was faithfully using the retrieved context because that was exactly what it had been given.

The model wasn't necessarily failing.

It simply had nothing better to work with.

---

# Test 5 — The Biggest Surprise

I asked a simple question:

> "How do I become really good at my job?"

Instead of discussing things like:

- learning quickly
- asking questions
- building trust
- communicating well
- taking initiative

Bridge AI responded with information about job scams.

At first I thought retrieval had failed.

After checking the retrieved chunks, I realised something different had happened.

The retriever searched for the closest available information.

Unfortunately, my corpus didn't actually contain much guidance on succeeding in a first job.

It returned the closest employment-related content instead.

This completely changed how I thought about RAG.

---

# Biggest Discovery

I realised that a RAG system can never retrieve knowledge that doesn't exist.

The prompt wasn't broken.

Gemini wasn't broken.

The vector database wasn't broken.

The corpus was incomplete.

This was probably the biggest lesson of the day.

---

# Test 6 — Emotional Questions

I then started asking more emotional questions.

For example:

> "I got fired without a conversation and unfairly."

The response immediately quoted sections of the Employment Act.

Legally, the answer wasn't wrong.

Emotionally, it completely missed the user.

If someone asks that question, they are probably frustrated, confused, or worried.

The AI should recognise that before explaining legal guidance.

This helped me realise that Bridge AI isn't just answering questions.

It's supporting people through career transitions.

---

# Test 7 — Hidden Retrieval vs User Experience

Another design decision emerged.

Initially I wanted every response to say things like:

> "According to the Employment Act..."

or

> "According to Hidden Curriculum Kenya..."

After reading the conversations aloud, they felt unnatural.

I decided that document references should stay behind the scenes.

The user should experience a conversation.

The system should still record:

- retrieved chunks
- similarity scores
- source documents
- evaluation metadata

These belong in the admin dashboard—not the user interface.

---

# Test 8 — Reviewing the Chunking Strategy

I also reviewed my ingestion pipeline.

Initially I thought I was using semantic chunking.

After examining the implementation, I realised I was actually using structural chunking.

The pipeline:

- groups paragraphs
- falls back to sentence splitting
- preserves document structure
- uses overlap to maintain context

Initially I thought this might be a weakness.

After reflecting on it, I actually think it's a good engineering decision for legal and guidance documents because those documents are already organised into meaningful sections.

---

# Test 9 — Prompt Engineering Isn't Everything

At the beginning of the day I believed the quality of the conversation depended mostly on the system prompt.

By the end of the day I had completely changed my mind.

Conversation quality depends on several components working together:

- the corpus
- retrieval quality
- chunking strategy
- prompt engineering
- Gemini's reasoning
- conversation memory
- guardrails

A prompt cannot compensate for weak or missing knowledge.

---

# Final Decision

The biggest architectural decision I made today was to redesign the knowledge base.

Instead of collecting multiple unrelated documents, I will build one comprehensive **Bridge AI Career Handbook** covering almost every realistic question a university student, intern, graduate trainee, or early-career professional in Kenya might ask.

The Employment Act will remain as a separate legal reference because it serves a different purpose.

This approach should improve retrieval consistency, reduce knowledge gaps, and create more natural conversations.

---

# Personal Reflection

Today completely changed how I think about building AI systems.

I started the day believing I was building a chatbot.

I ended the day realising I'm actually building a conversational knowledge system.

The most important insight I gained is that the intelligence of a RAG system is not determined by the language model alone.

It emerges from the interaction between the knowledge base, retrieval pipeline, prompt design, memory, safety guardrails, and the overall user experience.

For me, today marked the point where I stopped thinking like someone integrating an LLM API and started thinking like an AI product engineer.

---

# Test 10 — Prompt Engineering Has Limits

Throughout the day I kept iterating on the system prompt, expecting that a better prompt would naturally produce better conversations.

Each iteration improved the responses slightly, but after several revisions the improvements became smaller. Eventually, I realized that the prompt was no longer the bottleneck.

The limiting factor had shifted to the quality of the knowledge available for retrieval and the overall conversation architecture.

## Lesson

Prompt engineering improves **how** knowledge is communicated.

It cannot compensate for:

- missing knowledge
- poor retrieval
- weak conversation design
- incomplete corpora

At some point, improving the prompt produces diminishing returns, and engineering effort is better spent improving the system around the LLM.

---

# Test 11 — Broad Questions Need a Different Strategy

I tested intentionally broad questions such as:

> "I got my first job. What should I know?"

The initial response asked me to clarify my question before offering any guidance.

Although technically acceptable, it wasn't a satisfying user experience.

Someone asking this question is looking for orientation, confidence, and practical advice—not another question.

I redesigned the conversation strategy so that Bridge AI now:

- provides immediate value
- summarizes the most important guidance
- asks a follow-up question only after helping the user

## Lesson

Users expect help first.

Clarifying questions should improve the conversation, not delay useful guidance.

---

# Test 12 — The User Prompt Is Just as Important as the System Prompt

Initially I spent most of my time improving the system prompt.

Later, I realised that the user prompt is equally important.

The system prompt defines Bridge AI's identity.

The user prompt defines how the model reasons for each request.

Instead of simply telling the model:

> "Answer using the retrieved context."

I redesigned the user prompt to encourage Gemini to:

- determine the user's underlying need
- synthesize multiple retrieved chunks
- prioritize practical guidance
- avoid copying retrieved text
- adapt its response based on the user's intent

## Lesson

The best conversations come from good reasoning instructions—not just a good persona.

---

# Test 13 — Retrieval Diversity Matters

While reviewing responses, I noticed that retrieval often returned several consecutive chunks from the same section of the handbook.

Although relevant, these chunks frequently repeated similar information.

This limited the variety of ideas available to the model.

## Observation

Five similar chunks are often less useful than three complementary chunks covering different aspects of the user's question.

## Future Improvements

Research and experiment with:

- Maximal Marginal Relevance (MMR)
- diversity-aware retrieval
- chunk deduplication
- section-aware retrieval

---

# Test 14 — Guardrails Are More Than Safety Rules

I tested several scenarios involving:

- legal questions
- workplace disputes
- potential job scams
- emotional situations
- general greetings
- out-of-scope questions

The guardrails correctly classified these requests and routed them through the appropriate parts of the pipeline.

However, I also noticed that once guardrails were triggered, responses sometimes became overly policy-focused or emotionally distant.

This highlighted an important design challenge.

Guardrails should enforce safety without making the conversation feel robotic.

## Lesson

Good guardrails are almost invisible.

Users should feel supported rather than blocked.

Safety should guide the conversation—not interrupt it.

---

# Test 15 — Separating User Experience from Engineering Experience

One architectural decision I became much more confident about today was separating what the user sees from what the engineering team needs.

The user should experience a natural conversation.

The engineering team needs visibility into how the system arrived at each answer.

The backend should continue recording:

- retrieved chunks
- similarity scores
- latency
- model used
- embedding model
- guardrail decisions
- conversation memory
- evaluation metrics

These belong in the admin dashboard and evaluation tools—not inside the conversation.

## Lesson

A production AI system serves two audiences:

- the user
- the engineers maintaining it

Those experiences should remain completely separate.

---

# Final Engineering Takeaways

Today fundamentally changed how I think about conversational AI systems.

At the beginning of the day, I believed that improving responses mainly meant improving prompts.

By the end of the day, I understood that conversation quality is an emergent property of the entire system.

Every layer contributes:

- Knowledge Base (Corpus)
- Chunking Strategy
- Retrieval Pipeline
- Prompt Architecture
- LLM Reasoning
- Conversation Memory
- Guardrails
- Evaluation & Telemetry
- User Experience Design

The biggest mindset shift I had today was moving from asking:

> "How do I get Gemini to answer better?"

to asking:

> "How do I design a system that consistently enables Gemini to answer well?"

That shift—from thinking about prompts to thinking about systems—was probably the most valuable lesson I learned today.

---

# Next Steps

Based on today's discoveries, my priorities are now much clearer.

## Immediate Priorities

- Expand and refine the **Bridge AI Career Handbook** to cover realistic graduate and early-career scenarios.
- Continue improving conversational quality while avoiding over-engineering the prompts.
- Introduce retrieval diversity to reduce repetitive context.
- Improve conversation memory so Bridge AI naturally remembers previous parts of the discussion.
- Strengthen the evaluation framework by testing more real-world user journeys instead of isolated questions.

## Long-Term Goal

Bridge AI should eventually feel less like an AI assistant answering questions and more like a trusted mentor who helps young professionals navigate the uncertainty of starting their careers—while remaining completely grounded in verified knowledge.