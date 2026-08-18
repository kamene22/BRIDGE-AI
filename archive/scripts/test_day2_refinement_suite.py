"""
test_day2_refinement_suite.py — Verification suite for Day 2 UI & Conversation Refinements
"""

import sys
import os

sys.path.insert(0, os.path.abspath("src"))
from pipeline import BridgeAIPipeline

pipeline = BridgeAIPipeline()

test_cases = [
    {
        "name": "Observation 3: Greeting Trigger",
        "query": "Hello Amani",
        "expected_check": "Should introduce self ('Hi! I'm Amani...')"
    },
    {
        "name": "Observation 3: Direct Problem Query (No Self-Intro)",
        "query": "I think my manager hates me.",
        "expected_check": "Must NOT say 'Hi I'm Amani' or introduce self. Jump directly into helping."
    },
    {
        "name": "Observation 4 & 5: Zero Assumed Career Stage & Universal Advice",
        "query": "I don't know if I'm doing well at work.",
        "expected_check": "Must NOT assume user is intern/fresh graduate/probationer unless stated."
    },
    {
        "name": "Observation 6: Situational Reasoning 5-Step Flow",
        "query": "I accidentally sent an email to the wrong person.",
        "expected_check": "Follows Acknowledge -> Explore -> Reason -> Advice -> Follow-up flow."
    }
]

print("=" * 80)
print("DAY 2 CONVERSATION REFINEMENTS VERIFICATION SUITE")
print("=" * 80)

for test in test_cases:
    print(f"\n[Test: {test['name']}]")
    print(f"User Query: \"{test['query']}\"")
    print(f"Expectation: {test['expected_check']}")
    print("-" * 75)
    
    res = pipeline.run(test["query"])
    ans = res["answer"]
    
    print("💬 Amani Mentor Response:\n")
    print(ans)
    print("\n" + "-" * 75)

print("=" * 80)
print("DAY 2 REFINEMENT VERIFICATION COMPLETE ✓")
print("=" * 80)
