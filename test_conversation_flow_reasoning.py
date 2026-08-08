"""
test_conversation_flow_reasoning.py — Multi-Turn Conversation Flow Reasoning Test Suite
"""

import sys
import os

sys.path.insert(0, os.path.abspath("src"))
from pipeline import BridgeAIPipeline

pipeline = BridgeAIPipeline()

turns = [
    {
        "turn": 1,
        "query": "I got my first job.",
        "description": "Initial career milestone query"
    },
    {
        "turn": 2,
        "query": "It's an NGO in Nairobi.",
        "description": "User answering Amani's previous question about employer type (Must NOT restart conversation!)"
    },
    {
        "turn": 3,
        "query": "I think my manager hates me.",
        "description": "Situational conflict query"
    },
    {
        "turn": 4,
        "query": "She barely talks to me.",
        "description": "User answering Amani's question about manager behavior (Must NOT restart conversation!)"
    },
    {
        "turn": 5,
        "query": "Thank you so much Amani!",
        "description": "User concluding conversation (Must respond warmly WITHOUT forcing a follow-up question!)"
    }
]

print("=" * 80)
print("MULTI-TURN CONVERSATION FLOW REASONING EVALUATION SUITE")
print("=" * 80)

for item in turns:
    print(f"\n[TURN {item['turn']}] User Input: \"{item['query']}\"")
    print(f"Goal: {item['description']}")
    print("-" * 75)
    
    res = pipeline.run(item["query"])
    ans = res["answer"]
    
    print("💬 Amani Mentor Response:\n")
    print(ans)
    print("\n" + "-" * 75)

print("=" * 80)
print("MULTI-TURN CONVERSATION FLOW REASONING EVALUATION COMPLETE ✓")
print("=" * 80)
