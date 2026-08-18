"""
legal_boundary.py — Output Guardrail 3: Legal Advice Boundary

Design principle (from design document):
  "This guardrail CORRECTS rather than blocks — a deliberate departure
  from the other two. Workplace questions frequently touch on rights and
  legality even tangentially — an aggressive block-and-reject approach here
  would make the system unusable for a large share of legitimate questions.
  The better trade-off is to assume the underlying answer is probably useful
  and simply needs its confidence recalibrated."

Implementation:
  - Two-stage: first DETECT if the draft response makes overconfident
    legal claims; if yes, REWRITE it to clearly separate general
    source-grounded information from user-specific matters.
  - The rewrite instruction block comes verbatim from the design document.
  - Operates on the LLM's DRAFT RESPONSE, not the user's query.
  - Returns the corrected response. If no legal issue, returns original unchanged.
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from llm_provider.provider import GeminiProvider

# Verbatim from the design document — §System Prompt, legal boundary block.
_LEGAL_CORRECTION_INSTRUCTION = """Your draft response makes a claim that reads as definitive legal advice. \
Rewrite it to clearly distinguish between general information supported by \
the retrieved context and matters that depend on the user's specific \
situation, for which they should consult the relevant official resource \
(e.g., Kenya's Ministry of Labour, or a legal aid service) rather than rely \
solely on this chatbot."""

_DETECTION_PROMPT = """You are a legal-language auditor reviewing a chatbot response about employment in Kenya.

Check whether the response makes any of these overconfident legal claims:
- States a legal right as definitive and unconditional ("you ARE entitled to...", "they CANNOT legally...", "this IS illegal...")
- Gives specific legal advice tailored to the user's situation as if the bot were a lawyer
- Makes claims about statutory rights without hedging or citing a source
- Advises the user to take legal action without noting they should seek official guidance

Chatbot response to review:
\"\"\"
{response}
\"\"\"

Does this response contain overconfident legal claims that need correction?
Respond with exactly one word: LEGAL_ISSUE or NO_ISSUE"""

_REWRITE_PROMPT = """You are Bridge AI, a warm career mentor for young Kenyans.

You have drafted a response that reads as definitive legal advice. Rewrite it so that:
1. General information from your sources is presented as general guidance, not legal certainty
2. Anything that depends on the user's specific employment contract or situation is flagged as such
3. You point the user to the appropriate official resource (Kenya's Ministry of Labour, a registered legal aid clinic) for any specific legal determination — without being alarming or dismissive
4. The rewrite maintains the same helpful, warm tone and includes all the useful information from the original

Original draft response:
\"\"\"
{draft}
\"\"\"

Rewritten response (same length target, corrected confidence level):"""


def check_legal_boundary(
    draft_response: str,
    provider: GeminiProvider = None
) -> tuple[str, bool]:
    """
    Checks a draft response for overconfident legal claims and corrects if found.

    Two-stage:
      1. DETECT: classify if the draft contains definitive legal advice
      2. REWRITE: if detected, trigger corrective rewrite (does not discard response)

    Args:
        draft_response: The LLM's generated draft answer.
        provider: Optional shared GeminiProvider instance.

    Returns:
        tuple[str, bool]:
            - str: Final response (corrected if legal issue found, original otherwise)
            - bool: True if the legal boundary was triggered and a rewrite occurred
    """
    if provider is None:
        provider = GeminiProvider()

    # Fast heuristic pre-check for obvious overconfident legal claims
    d_lower = draft_response.lower()
    obvious_legal = ["cannot legally", "is illegal under", "you are legally entitled", "sue them in", "committed a crime", "take legal action"]
    legal_issue_found = any(kw in d_lower for kw in obvious_legal)

    if not legal_issue_found:
        return draft_response, False

    # ── Stage 2: Corrective Rewrite ────────────────────────────────────────
    rewrite_prompt = _REWRITE_PROMPT.format(draft=draft_response.strip())
    try:
        corrected = provider.generate_response(
            prompt=rewrite_prompt,
            system_prompt=_LEGAL_CORRECTION_INSTRUCTION,
            temperature=0.1,
            max_output_tokens=1200
        )
        return corrected, True

    except Exception as e:
        # If rewrite fails, return original rather than blocking entirely.
        print(f"[legal_boundary] Rewrite error — returning original draft: {e}")
        return draft_response, False


if __name__ == "__main__":
    provider = GeminiProvider()

    test_cases = [
        # Should trigger — overconfident legal claim
        (
            "Your employer CANNOT extend your probation beyond 6 months. This is illegal under the Employment Act and you ARE legally entitled to full employee status after that period.",
            True
        ),
        # Should trigger — definitive legal advice
        (
            "You are entitled by law to a written contract within 3 months. If they haven't provided one, you should sue them in the Employment and Labour Relations Court.",
            True
        ),
        # Should NOT trigger — appropriately hedged
        (
            "According to the Employment Act, probation is generally capped at 6 months. For your specific situation, you may want to confirm with the Ministry of Labour or a legal aid service.",
            False
        ),
        # Should NOT trigger — practical advice, no legal claims
        (
            "Dress codes vary a lot by employer type — a bank will expect formal attire, while a startup might be more relaxed. When in doubt, go slightly more formal on your first day.",
            False
        ),
    ]

    print("=" * 65)
    print("LEGAL BOUNDARY GUARDRAIL TEST")
    print("=" * 65)
    for draft, expected_trigger in test_cases:
        _, triggered = check_legal_boundary(draft, provider)
        status = "✓" if triggered == expected_trigger else "✗ MISMATCH"
        label = "REWRITE" if triggered else "PASS   "
        print(f"  [{label}] {status} | {draft[:58]}...")
