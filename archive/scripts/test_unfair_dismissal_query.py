"""
test_unfair_dismissal_query.py — Test human mentor response to unfair dismissal
"""

import sys
import os

sys.path.insert(0, os.path.abspath("src"))
from pipeline import BridgeAIPipeline

pipeline = BridgeAIPipeline()

q = "I got fired without a conversation and unfairly"

print("=" * 80)
print("TESTING UNFAIR DISMISSAL HUMAN MENTOR RESPONSE")
print("=" * 80)

out = pipeline.run(q)

print(f"\nUser Query: \"{q}\"")
print("-" * 75)
print(f"💬 Bridge AI Response:\n\n{out['answer']}\n")
print("=" * 80)
