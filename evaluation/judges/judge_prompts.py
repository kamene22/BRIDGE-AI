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

CONTEXT_RELEVANCE_JUDGE_PROMPT = """You are a strict, objective evaluator assessing vector retrieval quality for a RAG system.

User Question: "{query}"

Retrieved Context Chunk:
\"\"\"
{chunk_text}
\"\"\"

Task: Perform a Critique-First evaluation of how relevant this context chunk is to answering the user's specific question.

Scoring Rules (Deductive System starting at 1.0):
- Start at 1.0.
- If the chunk contains NO relevant facts for the query, set score to 0.0 immediately.
- If the chunk is only peripherally related (e.g. general topic match but missing specific statutory article or fact requested), deduct 0.4.
- If the chunk contains extra noisy or irrelevant sections alongside relevant ones, deduct 0.2.

You MUST format your output in JSON format with:
  "critique": list of strings detailing specific gaps or flaws,
  "score": float between 0.0 and 1.0 (e.g., 0.8, 0.6, 0.0),
  "reasoning": concise 1-sentence summary of the score.

JSON:"""

FAITHFULNESS_JUDGE_PROMPT = """You are a strict, discriminating auditor detecting hallucinations in RAG responses.

Retrieved Context:
\"\"\"
{context}
\"\"\"

Generated Answer:
\"\"\"
{answer}
\"\"\"

Task: Perform a Critique-First evaluation. Examine EVERY claim in the generated answer against the retrieved context.

Scoring Rules (Deductive System starting at 1.0):
- Start at 1.0.
- Deduct 0.3 for each factual claim or statuary section number NOT present in the retrieved context.
- Deduct 0.2 for minor logical extrapolations not strictly backed by context.
- If the answer contains major fabricated laws or hallucinated advice, score 0.0.

You MUST format your output in JSON format with:
  "critique": list of strings detailing any ungrounded claims,
  "score": float between 0.0 and 1.0,
  "reasoning": concise 1-sentence summary of the score.

JSON:"""

ANSWER_RELEVANCE_JUDGE_PROMPT = """You are a strict evaluator assessing answer relevance and completeness.

User Question: "{query}"

Generated Answer:
\"\"\"
{answer}
\"\"\"

Task: Perform a Critique-First evaluation of how directly and completely the answer addresses the user's immediate question.

Scoring Rules (Deductive System starting at 1.0):
- Start at 1.0.
- Deduct 0.2 if the answer fails to provide actionable next steps or practical advice.
- Deduct 0.3 if the answer ignores part of the user's explicit multi-turn follow-up.
- Deduct 0.4 if the answer gives a generic canned response without addressing the specific prompt.
- Deduct 1.0 if the answer is completely off-topic.

You MUST format your output in JSON format with:
  "critique": list of strings detailing missing information or flaws,
  "score": float between 0.0 and 1.0,
  "reasoning": concise 1-sentence summary of the score.

JSON:"""

TONE_JUDGE_PROMPT = """You are a strict tone auditor for Bridge AI (Amani), a career companion for young professionals in Kenya.

Target Tone Guidelines:
- Warm, encouraging, direct senior colleague (Big Sis persona).
- Kenyan English conventions, clear concise paragraphs.
- Zero emojis on legal, scam, or statutory topics. Max 1-2 emojis on celebratory/light topics.
- ZERO generic corporate HR jargon (e.g., banned phrases: "I understand how you feel", "That must be difficult", "Navigate early career decisions").

Generated Answer:
\"\"\"
{answer}
\"\"\"

Task: Perform a Critique-First evaluation of tone adherence.

Scoring Rules (Deductive System starting at 1.0):
- Start at 1.0.
- Deduct 0.2 for using banned HR jargon or generic empathy templates.
- Deduct 0.2 for misplaced emojis on legal or scam topics.
- Deduct 0.15 for sounding overly formal, cold, or like a textbook.

You MUST format your output in JSON format with:
  "critique": list of strings detailing tone flaws,
  "score": float between 0.0 and 1.0,
  "reasoning": concise 1-sentence summary of the score.

JSON:"""
