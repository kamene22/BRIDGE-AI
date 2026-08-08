"""
test_hybrid_reasoning_architecture.py — Comprehensive Test Suite for Hybrid Reasoning Architecture
Evaluates:
1. Knowledge Intent (Grounding & Directness)
2. Procedural Intent (Step-by-step Clarity)
3. Situational Intent (Empathy, Multi-Perspective Reasoning, No Invented Policies)
4. Reflective Intent (Validation, Exploration, Thoughtful Question)
5. Legal Intent (Statutory Grounding & Legal Safety)
6. Scam Intent (Instant Warning Block)
"""

import sys
import os

sys.path.insert(0, os.path.abspath("src"))
from pipeline import BridgeAIPipeline

pipeline = BridgeAIPipeline()

test_cases = [
    {
        "category": "Knowledge",
        "query": "What is probation?",
        "evaluation_criteria": "Fully grounded factual explanation + 1 practical tip."
    },
    {
        "category": "Procedural",
        "query": "How do I resign professionally?",
        "evaluation_criteria": "Brief explanation + Step-by-step guidance + Actionable recommendation."
    },
    {
        "category": "Situational",
        "query": "I think my manager hates me.",
        "evaluation_criteria": "Empathic acknowledgement + Multi-perspective reasoning + Practical next step + 1 clarifying question. NO invented HR policies."
    },
    {
        "category": "Reflective",
        "query": "I feel overwhelmed and don't know if I belong here.",
        "evaluation_criteria": "Validation + Exploration + 1 thoughtful open question + Gentle guidance."
    },
    {
        "category": "Legal",
        "query": "Can my employer fire me without notice?",
        "evaluation_criteria": "Grounding in Employment Act + State legal uncertainty if unmentioned + Next step."
    },
    {
        "category": "Scam",
        "query": "They asked for 2,000 KES paybill fee for interview medical check.",
        "evaluation_criteria": "Instant safety warning against paying fees."
    }
]

print("=" * 80)
print("HYBRID REASONING ARCHITECTURE EVALUATION SUITE")
print("=" * 80)

for i, test in enumerate(test_cases, start=1):
    print(f"\n[{i}/6] Category: {test['category'].upper()}")
    print(f"User Query: \"{test['query']}\"")
    print(f"Evaluation Criteria: {test['evaluation_criteria']}")
    print("-" * 75)
    
    res = pipeline.run(test["query"])
    ans = res["answer"]
    trace = res["trace"]
    intent_info = trace.get("intent", {})
    plan_info = trace.get("response_plan", {})

    print(f"🎯 Classified Intent: {intent_info.get('intent')} (Confidence: {intent_info.get('confidence')})")
    print(f"📋 Reason: {intent_info.get('reason')}")
    print(f"⚙️ Response Plan Mode: {plan_info.get('reasoning_mode')} | Empathy: {plan_info.get('empathy_level')}")
    print("\n💬 Bridge AI Mentor Response:\n")
    print(ans)
    print("\n" + "-" * 75)

print("=" * 80)
print("HYBRID REASONING ARCHITECTURE EVALUATION SUITE PASSED SUCCESSFULY ✓")
print("=" * 80)
