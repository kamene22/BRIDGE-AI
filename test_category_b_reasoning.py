"""
test_category_b_reasoning.py — Evaluates Phase X.2 Conversational Reasoning for "I got my first job. What should I know?"
"""

import sys
import os

sys.path.insert(0, os.path.abspath("src"))
from pipeline import BridgeAIPipeline

pipeline = BridgeAIPipeline()

q = "I got my first job. What should I know?"

print("=" * 80)
print("PHASE X.2 CONVERSATIONAL REASONING TEST")
print("=" * 80)

out = pipeline.run(q)

print(f"\nUser Query: \"{q}\"")
print("-" * 75)
print(f"💬 Bridge AI Response:\n\n{out['answer']}\n")
print("=" * 80)

# Success criteria audit:
ans = out['answer'].lower()

has_congrats = "congratulations" in ans or "congrats" in ans
has_immediate_value = len(ans.split()) > 40 and not ans.startswith("what specific")
has_synthesis = "learning" in ans and "communication" in ans and "dress" in ans
has_next_step = "practical next step" in ans or "notebook" in ans
no_early_clarification = not (ans.startswith("it's natural") or ans.startswith("what specific"))

print("\nSUCCESS CRITERIA AUDIT:")
print(f"  1. Congratulations / Natural Acknowledgement : {'✓ PASS' if has_congrats else '✗ FAIL'}")
print(f"  2. Immediate Practical Advice                : {'✓ PASS' if has_immediate_value else '✗ FAIL'}")
print(f"  3. Multi-Chunk Topic Synthesis               : {'✓ PASS' if has_synthesis else '✗ FAIL'}")
print(f"  4. One Practical Next Step                   : {'✓ PASS' if has_next_step else '✗ FAIL'}")
print(f"  5. No Premature Clarification                : {'✓ PASS' if no_early_clarification else '✗ FAIL'}")
print("=" * 80)
