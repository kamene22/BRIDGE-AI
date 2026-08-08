"""
out_of_scope.py — Input Guardrail 1: Out-of-Scope Detection

Design principle (from design document):
  "Lean permissive, not strict. A false rejection (turning away a legitimate
  question) actively damages user trust and can make someone feel judged or
  dismissed, while a false acceptance usually just results in a slightly less
  precise answer."

Implementation:
  - Single prompt-based LLM classifier.
  - Checks against Bridge AI's explicit scope: job search, applications,
    scams, and early-employment workplace navigation for young Kenyans.
  - Returns True (out of scope) only when the question is CLEARLY unrelated
    — not when it is topic-adjacent or ambiguous.
  - Topic-adjacent questions ("should I freelance instead?") should NOT
    trigger this guardrail.
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from llm_provider.provider import GeminiProvider

# The verbatim scope definition — mirrors the design document's scope list.
_SCOPE_DEFINITION = """
Bridge AI helps young Kenyans with:
- Finding legitimate job opportunities and using job boards
- Identifying and avoiding job scams
- CV writing, application letters, and interview preparation
- Understanding employment contracts, probation, and statutory rights (PAYE, NSSF, SHA)
- Workplace norms, professional communication, dress codes, and hierarchy navigation
- Managing the transition from university to a first professional job in Kenya
- Salary expectations, deductions, and basic financial literacy for first earners
"""

_CLASSIFIER_PROMPT = """You are a topic classifier for Bridge AI, a career guidance chatbot for young Kenyan professionals.

Bridge AI's scope covers:
{scope}

Your task: Decide if the user's message is OUT OF SCOPE.

IMPORTANT RULES:
- Return OUT_OF_SCOPE only if the question is CLEARLY unrelated to work, careers, or employment.
- When in doubt, return IN_SCOPE. It is better to attempt a grounded answer than to wrongly reject a genuine question.
- Questions that are topic-adjacent (e.g., entrepreneurship vs employment, salary negotiation, mental health at work) should be classified IN_SCOPE.
- Obvious out-of-scope examples: cooking recipes, sports, romantic relationships, coding tutorials, medical advice unrelated to work.

User message: "{query}"

Respond with exactly one word — either IN_SCOPE or OUT_OF_SCOPE. No explanation."""


def is_out_of_scope(query: str, provider: GeminiProvider = None) -> bool:
    """
    Returns True if the query is clearly outside Bridge AI's scope.
    Uses ultra-fast heuristic check first to avoid extra API latency.
    """
    q_lower = query.lower().strip()

    # Fast heuristic check: career/workplace/greetings are 100% IN_SCOPE
    fast_in_scope_keywords = [
        "job", "work", "career", "interview", "cv", "resume", "manager", "boss",
        "salary", "pay", "probation", "contract", "deduction", "paye", "nssf", "sha",
        "hired", "fired", "scam", "fee", "wear", "dress", "hello", "hi", "hey", "thanks", "thank"
    ]
    if any(k in q_lower for k in fast_in_scope_keywords) or len(q_lower.split()) <= 4:
        return False

    # Check for obvious out-of-scope triggers
    obvious_out_keywords = ["recipe", "football", "soccer", "movie", "weather in", "bitcoin"]
    if any(k in q_lower for k in obvious_out_keywords):
        return True

    if provider is None:
        provider = GeminiProvider()

    prompt = _CLASSIFIER_PROMPT.format(
        scope=_SCOPE_DEFINITION.strip(),
        query=query.strip()
    )

    try:
        result = provider.generate_response(
            prompt=prompt,
            temperature=0.0,          # Deterministic — classification, not generation
            max_output_tokens=5        # Only need one word back
        )
        verdict = result.strip().upper()
        return verdict == "OUT_OF_SCOPE"

    except Exception as e:
        # If the guardrail fails, default to IN_SCOPE (fail open, not closed).
        # Design doc: permissive is safer than blocking when uncertain.
        print(f"[out_of_scope] Guardrail error — defaulting to IN_SCOPE: {e}")
        return False


if __name__ == "__main__":
    provider = GeminiProvider()
    test_cases = [
        # Should be IN_SCOPE
        ("How long is probation in Kenya?", False),
        ("Can my boss fire me without notice?", False),
        ("How do I negotiate my first salary?", False),
        ("A recruiter is asking me to pay KES 3,000 for a uniform deposit.", False),
        ("Should I take this NGO job or start freelancing?", False),
        # Should be OUT_OF_SCOPE
        ("How do I bake a chocolate cake?", True),
        ("Who won the 2022 World Cup?", True),
        ("Write me a Python sorting algorithm.", True),
    ]

    print("=" * 60)
    print("OUT-OF-SCOPE GUARDRAIL TEST")
    print("=" * 60)
    for query, expected in test_cases:
        result = is_out_of_scope(query, provider)
        status = "✓" if result == expected else "✗ MISMATCH"
        label = "OUT" if result else "IN "
        print(f"  [{label}] {status} | {query[:55]}")
