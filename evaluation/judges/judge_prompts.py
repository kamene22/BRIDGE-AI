"""
judge_prompts.py — Custom LLM-as-a-Judge Prompts (Layer 3 & 4)

Design principle from design document:
  "An LLM-as-a-judge prompt is itself untested logic, not a ground truth —
  trusting its verdicts without checking them first risks an evaluation
  framework whose scores look authoritative but don't actually mean anything."

These prompts judge:
  1. Context Relevance: Are retrieved chunks actually relevant to the query?
  2. Faithfulness: Is the answer 100% grounded in retrieved chunks (no hallucination)?
  3. Answer Relevance: Does the answer directly address the user's question?
  4. Tone Appropriateness: Does the tone match Big Sis / Bridge AI mentor guidelines?
  5. Session Impact (Layer 4): Did the multi-turn session resolve with a clear next step?
"""

CONTEXT_RELEVANCE_JUDGE_PROMPT = """You are an expert evaluator assessing retrieval quality for a RAG system.

User Question: "{query}"

Retrieved Context Chunk:
\"\"\"
{chunk_text}
\"\"\"

Task: Rate how relevant this context chunk is to answering the user's question on a scale of 0 to 1:
- 1.0 = Highly relevant; directly contains facts needed to answer the question.
- 0.5 = Partially relevant; contains peripheral context or related topic.
- 0.0 = Irrelevant; does not relate to the question.

Respond in JSON format with keys "score" (float) and "reasoning" (string short explanation).
JSON:"""

FAITHFULNESS_JUDGE_PROMPT = """You are an expert auditor assessing hallucination in RAG responses.

Retrieved Context:
\"\"\"
{context}
\"\"\"

Generated Answer:
\"\"\"
{answer}
\"\"\"

Task: Check if EVERY claim in the generated answer is directly supported by the retrieved context.
- 1.0 = Fully faithful; zero hallucinated facts outside the context.
- 0.5 = Partially faithful; minor extrapolations but mostly grounded.
- 0.0 = Unfaithful; contains unsupported claims or hallucinated facts.

Respond in JSON format with keys "score" (float) and "reasoning" (string short explanation).
JSON:"""

ANSWER_RELEVANCE_JUDGE_PROMPT = """You are an expert evaluator checking answer quality.

User Question: "{query}"

Generated Answer:
\"\"\"
{answer}
\"\"\"

Task: Rate how directly and completely the answer addresses the user's question:
- 1.0 = Directly answers the question in clear, helpful detail.
- 0.5 = Indirect or incomplete answer.
- 0.0 = Off-topic or fails to answer the question.

Respond in JSON format with keys "score" (float) and "reasoning" (string short explanation).
JSON:"""

TONE_JUDGE_PROMPT = """You are an expert tone evaluator for Bridge AI, a mentor chatbot for young Kenyan professionals.

Target Tone Guidelines:
- Warm, encouraging, direct, and non-condescending (sounds like a slightly older colleague).
- Kenyan English conventions, concise paragraphs.
- Max 1-2 emojis on light topics; ZERO emojis on scam, legal, or workplace-rights topics.
- No formal corporate HR jargon, no overly casual slang.

Generated Answer:
\"\"\"
{answer}
\"\"\"

Task: Rate the tone appropriateness on a scale of 0 to 1:
- 1.0 = Perfect tone alignment with all guidelines.
- 0.5 = Acceptable but slightly too corporate or overly casual.
- 0.0 = Inappropriate tone (condescending, overly formal HR manual, or misplaced emojis).

Respond in JSON format with keys "score" (float) and "reasoning" (string short explanation).
JSON:"""
