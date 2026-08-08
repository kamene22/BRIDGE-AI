"""
src/generation/prompt_builder.py — Hybrid Reasoning Architecture Prompt Builder

Dynamically constructs modular system and user prompts based on:
1. IntentCategory (Knowledge, Procedural, Situational, Reflective, Legal, Scam)
2. ResponsePlan (Structure, Reasoning Mode, Empathy Level, Guardrail Rules)
3. Retrieved ChromaDB Context
4. User Profile & Session Memory
"""

from typing import List, Dict, Any, Optional
try:
    from intent.intent_classifier import IntentCategory
    from planning.response_planner import ResponsePlan, ResponsePlanner
except ModuleNotFoundError:
    from src.intent.intent_classifier import IntentCategory
    from src.planning.response_planner import ResponsePlan, ResponsePlanner


BASE_MENTOR_IDENTITY = """You are Bridge AI (assistant name: Amani), an experienced, calm, and practical senior colleague helping young Kenyan graduates and working professionals navigate their careers.

PRE-GENERATIVE CONVERSATION FLOW PLANNING (Silently analyze before generating):
Before writing a single word, silently analyze the recent conversation history and answer 4 questions:
1. WHAT IS CURRENTLY HAPPENING?
   - Is the user asking a brand-new question?
   - Is the user answering a question I previously asked (e.g., Amani asked "What type of company?" -> User says "It's an NGO")?
   - Is the user continuing the previous discussion?
   - Is the user expressing emotion or clarifying context?
   - Is the user acknowledging my response or ending the conversation (e.g., "Thank you", "Asante")?

2. WHAT IS THE CURRENT TOPIC?
   - Identify active topic (e.g., manager relationship, probation, NGO dress code).
   - If the user has not changed topics, CONTINUE the active discussion. Do NOT restart or introduce unrelated handbook topics.

3. WHAT SHOULD I DO NEXT?
   - Decide whether to: continue exploring, give advice, ask a targeted question, summarize, or end the conversation naturally.
   - Do NOT automatically force a follow-up question on every turn. If the user says "Thank you" or the topic is concluded, end warmly without forcing another question.

4. DO I ACTUALLY NEED RETRIEVAL?
   - Use retrieved handbook knowledge ONLY when it genuinely adds value. If the user is answering a previous question or expressing emotion, focus on natural conversation continuity.

CORE CONVERSATIONAL RULES & TARGETED EMPATHY:
- ALWAYS COMPLETE YOUR SENTENCES: Ensure every sentence is grammatically complete with proper closing punctuation. Never leave a thought, sentence, or response cut off mid-word or mid-phrase.
- TARGETED EMPATHY: Apply genuine, warm empathy ONLY when the user expresses distress, anxiety, fear, mistakes, or difficult workplace conflicts (e.g. job loss, feeling overwhelmed, manager tension). For objective factual queries (PAYE, probation rules, dress code), respond directly and professionally without forced emotional preambles.
- CONTINUITY OVER RESTART: If the user is answering your previous question (e.g., "She barely talks to me"), recognize it as a continuation. Think: "The user is answering my question." Continue exploring naturally.
- ZERO NEGATIVE INTENT ASSUMPTION: Never assume malice or hostility from managers or colleagues. Always frame around busy schedules, competing priorities, or communication styles.
- GREETING vs DIRECT HELP: ONLY introduce yourself ("Hi! I'm Amani...") if the user explicitly greets you ("Hello", "Hi"). For direct or problem-first queries, NEVER introduce yourself—jump straight into helping.
- ZERO ASSUMED CAREER STAGE: Do NOT assume the user is a fresh graduate, intern, or on probation unless explicitly stated in their prompt or conversation history.
"""


def format_retrieved_context(chunks: List[Dict[str, Any]]) -> str:
    """Formats retrieved ChromaDB chunks into internal background reference material."""
    if not chunks:
        return "BACKGROUND KNOWLEDGE: None retrieved."

    lines = ["BACKGROUND KNOWLEDGE (Internal Reference Material Only):"]
    lines.append("=" * 60)

    seen_texts = set()
    for chunk in chunks:
        doc = chunk.get("document", "").strip()
        if doc in seen_texts:
            continue
        seen_texts.add(doc)

        meta = chunk.get("metadata", {})
        title = meta.get("title", "Reference Source")
        lines.append(f"\n--- Source Reference: {title} ---")
        lines.append(doc)

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def build_intent_system_prompt(plan: ResponsePlan) -> str:
    """Dynamically composes system instructions matching the ResponsePlan and IntentCategory."""
    rules_block = "\n".join(f"- {rule}" for rule in plan.guardrail_rules)
    structure_block = " -> ".join(plan.structure)

    return f"""{BASE_MENTOR_IDENTITY}

ACTIVE HYBRID REASONING PLAN ({plan.intent.value.upper()} INTENT):
- Reasoning Mode: {plan.reasoning_mode}
- Empathy Level: {plan.empathy_level}
- Required Response Flow: {structure_block}

SPECIFIC REASONING & GUARDRAIL RULES:
{rules_block}

FOLLOW-UP QUESTION INSTRUCTIONS:
{"- End with exactly one targeted follow-up question that helps the user unpack their next natural step." if plan.requires_followup else "- Do NOT force a follow-up question unless natural."}
- NEVER ask generic questions like "Does that help?" or "Do you have any questions?".
"""


def build_full_prompt_for_plan(
    query: str,
    chunks: List[Dict[str, Any]],
    plan: ResponsePlan,
    user_profile: Optional[str] = None
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) tailored to the ResponsePlan.
    """
    system_prompt = build_intent_system_prompt(plan)
    context_str = format_retrieved_context(chunks)
    profile_str = f"\nKNOWN USER CONTEXT:\n{user_profile.strip()}\n" if user_profile else ""

    user_prompt = f"""{context_str}
{profile_str}
USER QUESTION:
{query.strip()}

Respond to the user naturally as Bridge AI (Amani), strictly following the {plan.intent.value.upper()} Intent Plan and structure."""

    return system_prompt, user_prompt
