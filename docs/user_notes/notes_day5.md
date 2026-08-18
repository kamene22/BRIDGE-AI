# Day 4 — Latency Optimization — 10/08/2026

## Objective
Today I focused on identifying and reducing the latency of Bridge AI (Amani) while maintaining helpful, grounded conversational RAG responses.

## Initial Benchmark
My 10-turn benchmark showed an average latency of **5.82 seconds per turn**.

| Metric | Result |
|---|---:|
| Average turn latency | **5.82 s** |
| Average vector retrieval on RAG turns | **~257 ms** |
| Conversational turns with no RAG | **0 ms vector search** |
| Gemini generation contribution | **~89.1% of average latency** |

The benchmark showed that some conversational turns took **6–7 seconds even when vector search was 0 ms**. This confirmed that **Gemini generation, not ChromaDB, was the main bottleneck**.

## What I Investigated
I broke the pipeline into:

**Routing → Embedding → ChromaDB retrieval → Prompt construction → Gemini generation → Response**

I learned that ChromaDB retrieval was relatively fast (~100–140 ms), so replacing ChromaDB or changing the multi-index architecture was not the priority.

Other contributors I identified were:
- Large system/context prompts
- Output token generation
- Remote embedding calls on RAG turns
- Synchronous/non-streamed generation
- Potential duplicate pipeline execution in the Streamlit UI

## Model Optimization

I tested newer Gemini generation models:

| Model | Average Latency |
|---|---:|
| Original baseline | **5.82 s** |
| Gemini 2.5 Flash | **3.29 s** |
| Gemini 3.1 Flash Lite | **~2.8 s** |

Gemini 2.5 Flash reduced latency by approximately **43%** from baseline.

Gemini 3.1 Flash Lite reduced latency to approximately **2.8 seconds**, giving roughly a **52% improvement from the original 5.82-second baseline**.

## Streaming / UI Optimization
I also identified duplicate execution in the Streamlit flow, where `pipeline.run()` could be triggered twice for one turn.

I refactored the flow so that the response is streamed once and the conversation state is updated after streaming completes.

This reduced unnecessary generation and improved perceived responsiveness.

## Key Lesson
The biggest lesson today was:

> **Measure first, optimize second.**

I initially suspected RAG/ChromaDB, but the benchmark showed that LLM generation was responsible for most of the latency.

I learned to evaluate latency across the complete pipeline rather than optimizing one component in isolation.

### Final Result
**5.82 s → 3.29 s → ~2.8 s**

The system became significantly faster while keeping the existing conversational RAG and ChromaDB architecture.
