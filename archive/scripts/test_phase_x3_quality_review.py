"""
test_phase_x3_quality_review.py — Phase X.3 Principal Conversational Engineering Audit
"""

import sys
import os

sys.path.insert(0, os.path.abspath("src"))
from pipeline import BridgeAIPipeline

pipeline = BridgeAIPipeline()

test_cases = [
    ("Situation 1: First Job Orientation", "I got my first job."),
    ("Situation 2: Direct Attire Query", "What should I wear?"),
    ("Situation 3: Fear of Job Loss", "I'm scared I might lose my job."),
    ("Situation 4: Manager Ignored Email", "My manager ignored my email.")
]

print("=" * 80)
print("PHASE X.3 PRINCIPAL CONVERSATIONAL QUALITY REVIEW AUDIT")
print("=" * 80)

for title, q in test_cases:
    print(f"\n[{title}]")
    print(f"User Query: \"{q}\"")
    print("-" * 75)
    res = pipeline.run(q)
    ans = res["answer"]
    print(f"💬 Bridge AI Mentor Response:\n\n{ans}\n")
    print("-" * 75)

print("=" * 80)
print("PHASE X.3 AUDIT COMPLETE ✓")
print("=" * 80)
