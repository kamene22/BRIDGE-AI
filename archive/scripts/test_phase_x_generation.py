"""
test_phase_x_generation.py — Phase X.2 Conversational Intelligence Evaluation Suite

Tests 5 Specialized Conversation Modes:
  1. Information Mode (Factual: SHA deduction rate)
  2. Reflection Mode (Career choice: "I feel stuck")
  3. Workplace Guidance Mode (Dress code: First day at bank)
  4. Legal Boundary Mode ("Can I sue my employer?")
  5. Scam Detection Mode ("Recruiter asks for KES 2,500 fee")
"""

import sys
import os

sys.path.insert(0, os.path.abspath("src"))
from pipeline import BridgeAIPipeline

pipeline = BridgeAIPipeline()

test_cases = [
    ("Information Mode (Factual)", "What percentage is the SHA statutory deduction in Kenya?"),
    ("Reflection Mode (Career Choice)", "I don't know what career path is right for me and I feel stuck."),
    ("Workplace Guidance Mode (Attire)", "I got my first job at a corporate bank. What should I wear on my first day?"),
    ("Legal Boundary Mode (Workplace Rights)", "Can I sue my employer if they terminate my probation after 2 weeks?"),
    ("Scam Detection Mode (Safety)", "A recruiter asks for KES 2,500 registration fee before my interview.")
]

print("=" * 80)
print("PHASE X.2 — 5 CONVERSATION MODES EVALUATION TEST")
print("=" * 80)

forbidden_preambles = ["based on", "according to the document", "retrieved context", "the knowledge base", "page ", "lines "]

for mode, query in test_cases:
    print(f"\n[EVALUATING: {mode}]")
    print(f"User Query: \"{query}\"")
    print("-" * 75)

    res = pipeline.run(query)
    answer = res["answer"]
    sources = res["sources"]

    has_preamble = any(fp in answer.lower() for fp in forbidden_preambles)
    word_count = len(answer.split())

    print(f"Invisible Retrieval Check : {'✓ PASS (Zero Preambles)' if not has_preamble else '✗ FAIL'}")
    print(f"Word Count              : {word_count} words")
    print(f"Sources Tracked          : {', '.join(sources[:2]) if sources else 'None'}")
    print(f"\n💬 Response Text:\n{answer}\n")

print("=" * 80)
print("PHASE X.2 EVALUATION COMPLETE ✓")
print("=" * 80)
