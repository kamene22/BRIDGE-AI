"""
scam_detection.py — Input Guardrail 2: Job Scam Detection

Design principle (from design document):
  "Explicit, listed criteria produce more consistent and auditable results
  than an open-ended 'does this seem sketchy' judgment call. A vague prompt
  gives the model latitude to reason inconsistently across similar inputs;
  an explicit checklist constrains the decision space and makes the
  guardrail's behaviour something you can actually test and explain."

Implementation:
  - Prompt-based classifier that checks against an EXPLICIT list of
    scam indicators specific to the Kenyan job market.
  - Does NOT block the response — returns a warning instruction block
    to be APPENDED to the system prompt, so the user still gets their
    question answered with scam context layered in first.
  - The verbatim instruction block comes from the design document's
    'Guardrail-specific instruction blocks' section.
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from llm_provider.provider import GeminiProvider

# Verbatim from the design document — §System Prompt, guardrail-specific block.
SCAM_INSTRUCTION_BLOCK = """The user's message contains signs of a potential job scam (e.g., a request \
for upfront payment, an unverified recruiter, or an offer that seems too \
good to be true for the role described). Before answering their direct \
question, calmly and clearly walk them through why this specific pattern is \
a common warning sign in Kenya, using the retrieved scam-guidance context. \
Do not accuse the employer of being fraudulent with certainty — explain the \
pattern and recommend concrete verification steps. End by gently reminding \
them they can still ask their original question separately."""

# Explicit scam indicator checklist — sourced from job_scam_red_flags.md corpus.
_SCAM_INDICATORS = """
SCAM INDICATOR CHECKLIST (check EACH of these):
1. Upfront payment request — any fee before starting (uniform deposits, medical exam fees, training kits, registration fees, equipment bonds)
2. Salary too high for role described — e.g. KES 80,000+ for entry-level unskilled work with no stated qualifications
3. Unverified recruiter — personal email (Gmail/Yahoo/Hotmail) instead of a company domain, or contact via WhatsApp only
4. Immediate job offer without interview — offered a job without any assessment, CV review, or interview
5. Vague job description — no company name, no office address, no verifiable registration
6. Request for personal documents early — ID/passport copies, bank account details, or NSSF number before any formal onboarding
7. Work-from-home "agent" schemes — paid to recruit others, buy starter kits, or resell goods with promised commissions
"""

_SCAM_CLASSIFIER_PROMPT = """You are a job scam detection classifier for Bridge AI, a career guidance chatbot for young Kenyan professionals.

{indicators}

User message: "{query}"

Check whether the user's message describes ANY of the above scam indicators.

Respond with exactly one word:
- SCAM_DETECTED — if one or more indicators are clearly present
- NO_SCAM — if none of the indicators are present

No explanation. One word only."""


def check_scam(query: str, provider: GeminiProvider = None) -> str | None:
    """
    Checks whether the user's message describes a potential job scam.

    Returns:
        str: The SCAM_INSTRUCTION_BLOCK (from design doc) to append to the
             system prompt if scam indicators are found. This block instructs
             the LLM to explain the scam pattern before answering.
        None: If no scam indicators are detected.

    Note: Does NOT block the response. The user's question is still answered
    — the instruction block is layered in to add scam context first.
    """
    if provider is None:
        provider = GeminiProvider()

    # Fast heuristic pre-check for obvious scam indicators
    q_lower = query.lower()
    obvious_scams = ["pay kes", "registration fee", "uniform deposit", "training kit", "gmail account", "whatsapp only", "without any interview", "product starter kit"]
    if any(kw in q_lower for kw in obvious_scams):
        return SCAM_INSTRUCTION_BLOCK

    prompt = _SCAM_CLASSIFIER_PROMPT.format(
        indicators=_SCAM_INDICATORS.strip(),
        query=query.strip()
    )

    try:
        result = provider.generate_response(
            prompt=prompt,
            temperature=0.0,
            max_output_tokens=10
        )
        verdict = result.strip().upper()
        if "SCAM_DETECTED" in verdict:
            return SCAM_INSTRUCTION_BLOCK
        return None

    except Exception as e:
        # If guardrail fails, proceed without scam context (fail open).
        print(f"[scam_detection] Guardrail error — proceeding without scam flag: {e}")
        return None


if __name__ == "__main__":
    provider = GeminiProvider()
    test_cases = [
        # Should detect scam
        ("The company says I must pay KES 2,500 for a training kit before I start.", True),
        ("A recruiter on WhatsApp offered me KES 90,000/month to work from home selling products.", True),
        ("They want me to send a copy of my ID and NSSF details before the interview.", True),
        ("I got a job offer without any interview — they said I can start Monday.", True),
        # Should NOT detect scam
        ("How do I write a good CV for a bank job?", False),
        ("My probation is ending next month. What should I expect?", False),
        ("How do I negotiate a salary increase after 6 months?", False),
    ]

    print("=" * 65)
    print("SCAM DETECTION GUARDRAIL TEST")
    print("=" * 65)
    for query, expected_detect in test_cases:
        result = check_scam(query, provider)
        detected = result is not None
        status = "✓" if detected == expected_detect else "✗ MISMATCH"
        label = "SCAM" if detected else "SAFE"
        print(f"  [{label}] {status} | {query[:58]}")
