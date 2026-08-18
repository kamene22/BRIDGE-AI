"""
evaluation/profile_latency_breakdown.py — Real Latency Profiling Instrument
Measures exact stage durations (in ms) using time.perf_counter().
"""

import os
import sys
import time
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.pipeline import BridgeAIPipeline

def profile_requests():
    print("=" * 80)
    print("EMPIRICAL LATENCY PROFILING SUITE (BRIDGE AI)")
    print("=" * 80)

    pipeline = BridgeAIPipeline(session_id="profile_session_001")

    test_queries = [
        ("Greeting", "Hujambo"),
        ("Standalone Knowledge Query", "What are the probation rules under the Kenya Employment Act?"),
        ("Context-Dependent Follow-up", "Can my employer extend it to 8 months?")
    ]

    results = []

    for label, q in test_queries:
        print(f"\n[Profiling] {label}: \"{q}\"")
        t_start = time.perf_counter()
        res = pipeline.run(q)
        t_end = time.perf_counter()

        tot_ms = (t_end - t_start) * 1000.0
        meta = res.get("eval_metadata", {})
        lat_bd = meta.get("latency_breakdown", {})

        print(f"  ├─ Total Request Latency: {tot_ms:.2f} ms")
        print(f"  ├─ Intent & Planning    : {lat_bd.get('intent_ms', 0):.2f} ms")
        print(f"  ├─ Retrieval Gating     : {lat_bd.get('retrieval_gating_ms', 0):.2f} ms")
        print(f"  ├─ Contextualization    : {lat_bd.get('contextualize_ms', 0):.2f} ms")
        print(f"  ├─ Vector Retrieval     : {lat_bd.get('retrieval_ms', 0):.2f} ms")
        print(f"  ├─ Gemini Generation    : {lat_bd.get('generation_ms', 0):.2f} ms")
        print(f"  └─ Guardrails           : {lat_bd.get('guardrails_ms', 0):.2f} ms")

        results.append({
            "label": label,
            "query": q,
            "total_ms": round(tot_ms, 2),
            "breakdown": lat_bd
        })

    print("\n" + "=" * 80)
    print("PROFILING COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    profile_requests()
