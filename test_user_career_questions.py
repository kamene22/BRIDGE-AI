"""
test_user_career_questions.py — Evaluation Test Suite for 10 User Career Questions

Runs all 10 user questions through Bridge AI RAG Pipeline and records:
  - Answer & Tone Alignment
  - ChromaDB Grounded Sources
  - Safety Guardrails Status (OOS, Scam, Legal Rewrite)
  - Latency (ms)
"""

import sys
import os
import time
from typing import List, Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from pipeline import BridgeAIPipeline

pipeline = BridgeAIPipeline(top_k=5)

questions = [
    "I'm about to graduate, but I don't know what career is right for me.",
    "I'm thinking about changing careers, but I'm afraid I'll regret it.",
    "How can I discover my strengths and choose work that fits me?",
    "I keep setting goals but never achieve them. What am I doing wrong?",
    "I failed an interview yesterday, and now I've lost my confidence.",
    "I feel overwhelmed because I have too many options. How do I make a good decision?",
    "I'm starting my first job soon. What should I expect, and how can I prepare?",
    "I struggle to speak up during meetings. How can I become more confident at work?",
    "I've been rejected from several jobs. How do I stay motivated and keep going?",
    "I feel lost and uncertain about my future. Can you help me think through my next steps?"
]

print("=" * 80)
print("BRIDGE AI — CAREER MENTORSHIP EVALUATION TEST (10 USER QUESTIONS)")
print("=" * 80)

results = []

for i, q in enumerate(questions, start=1):
    print(f"\n[{i}/10] QUERY: \"{q}\"")
    print("-" * 75)
    
    t0 = time.time()
    out = pipeline.run(q)
    lat = int((time.time() - t0) * 1000)
    
    answer = out["answer"]
    sources = out["sources"]
    guardrails = out["trace"]["guardrails"]
    
    print(f"⏱ Latency: {lat}ms")
    print(f"🛡 Guardrails: OOS={guardrails['out_of_scope']} | Scam={guardrails['scam_detected']} | Legal={guardrails['legal_boundary_triggered']}")
    print(f"📌 Grounded Sources ({len(sources)}): {', '.join(sources[:2]) if sources else 'General Mentorship Context'}")
    print(f"\n💬 Bridge AI Answer:\n{answer}\n")
    
    results.append({
        "num": i,
        "question": q,
        "answer": answer,
        "sources": sources,
        "latency_ms": lat,
        "guardrails": guardrails
    })

print("=" * 80)
print("SUMMARY: ALL 10 CAREER QUESTIONS PROCESSED SUCCESSFULLY ✓")
print("=" * 80)
