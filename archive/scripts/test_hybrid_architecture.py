"""
test_hybrid_architecture.py — Comprehensive Hybrid RAG & Conversation Evaluation Test Suite

Tests the 11 specific evaluation questions (4 Knowledge, 7 Situational)
plus the 4-turn multi-turn conversation continuity test.
Prints a detailed breakdown of latency, retrieval decisions, top_k used, and answer summaries.
"""

import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from pipeline import BridgeAIPipeline


def run_evaluation():
    print("\n" + "=" * 90)
    print("  BRIDGE AI — HYBRID ARCHITECTURE & PERFORMANCE EVALUATION SUITE")
    print("=" * 90)

    pipeline = BridgeAIPipeline()

    # ── Part 1: Knowledge Questions (Retrieval SHOULD be used) ────────────────
    knowledge_questions = [
        "I just got my first job. What should I know before my first day?",
        "What should I look for before signing my employment contract in Kenya?",
        "How long can an employer keep me on probation in Kenya?",
        "I'm starting work at an NGO. What should I wear on my first day?"
    ]

    print("\n" + "─" * 90)
    print("  PART 1: KNOWLEDGE QUESTIONS (RAG Retrieval Required)")
    print("─" * 90)

    for idx, q in enumerate(knowledge_questions, 1):
        print(f"\n[Q{idx}] \"{q}\"")
        res = pipeline.run(q)
        meta = res.get("eval_metadata", {})
        breakdown = meta.get("latency_breakdown", {})

        print(f"  ├─ Retrieval Required: {meta.get('retrieval_required')} | Used: {meta.get('retrieval_used')} (top_k={meta.get('top_k_used')})")
        print(f"  ├─ Retrieval Reason: {meta.get('retrieval_reason')}")
        print(f"  ├─ Latency: {breakdown.get('total_latency_ms')}ms (Intent: {breakdown.get('intent_ms')}ms, Gating: {breakdown.get('retrieval_gating_ms')}ms, RAG: {breakdown.get('retrieval_ms')}ms, Gen: {breakdown.get('generation_ms')}ms)")
        if res.get("sources"):
            print(f"  ├─ Sources: {' | '.join(res['sources'][:2])}")
        print(f"  └─ Answer Snippet: {res['answer'][:180]}...\n")

    # ── Part 2: Situational Questions (Retrieval NOT required) ───────────────
    situational_questions = [
        "I made a mistake at work and I'm scared my manager thinks I'm incompetent.",
        "I don't think I'm doing well at my new job. How can I tell?",
        "My manager barely talks to me. Does that mean they don't like me?",
        "What are some things young professionals in Kenya often don't realise about workplace culture?",
        "My employer wants me to sign something I don't fully understand. What should I do?",
        "What should I do if I feel like I'm being treated unfairly at work?",
        "What would you do if you were me?"
    ]

    print("\n" + "─" * 90)
    print("  PART 2: SITUATIONAL & CONVERSATIONAL QUESTIONS (Direct Gemini Fallback)")
    print("─" * 90)

    for idx, q in enumerate(situational_questions, 5):
        print(f"\n[Q{idx}] \"{q}\"")
        res = pipeline.run(q)
        meta = res.get("eval_metadata", {})
        breakdown = meta.get("latency_breakdown", {})

        print(f"  ├─ Retrieval Required: {meta.get('retrieval_required')} | Used: {meta.get('retrieval_used')} (top_k={meta.get('top_k_used')})")
        print(f"  ├─ Retrieval Reason: {meta.get('retrieval_reason')}")
        print(f"  ├─ Latency: {breakdown.get('total_latency_ms')}ms (Intent: {breakdown.get('intent_ms')}ms, Gating: {breakdown.get('retrieval_gating_ms')}ms, Gen: {breakdown.get('generation_ms')}ms)")
        print(f"  └─ Answer Snippet: {res['answer'][:180]}...\n")

    # ── Part 3: Multi-Turn Conversation Continuity Test ──────────────────────
    print("\n" + "─" * 90)
    print("  PART 3: MULTI-TURN CONVERSATION CONTINUITY TEST")
    print("─" * 90)

    session_pipeline = BridgeAIPipeline()
    continuity_script = [
        "My manager barely talks to me.",
        "She only talks to me when she needs something.",
        "Maybe I'm just overthinking it.",
        "What would you do if you were me?"
    ]

    for turn_idx, turn_q in enumerate(continuity_script, 1):
        print(f"\n[Turn {turn_idx}] User: \"{turn_q}\"")
        res = session_pipeline.run(turn_q)
        meta = res.get("eval_metadata", {})
        breakdown = meta.get("latency_breakdown", {})

        print(f"  ├─ Retrieval Used: {meta.get('retrieval_used')} (top_k={meta.get('top_k_used')}) | Reason: {meta.get('retrieval_reason')}")
        print(f"  ├─ Latency: {breakdown.get('total_latency_ms')}ms (Gen: {breakdown.get('generation_ms')}ms)")
        print(f"  └─ Assistant: {res['answer'][:180]}...\n")

    print("=" * 90)
    print("  EVALUATION SUITE COMPLETED SUCCESSFULLY ✓")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    run_evaluation()
