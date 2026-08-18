"""
evaluation/test_optimized_latency.py — Empirical Latency Optimization Benchmark
Tests the impact of gemini-2.0-flash, heuristic query contextualization, and token caps.
"""

import os
import sys
import time
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.pipeline import BridgeAIPipeline

import google.generativeai as genai

def test_optimized():
    print("=" * 80)
    print("TESTING OPTIMIZED LATENCY BENCHMARK")
    print("=" * 80)

    pipeline = BridgeAIPipeline(session_id="opt_session_001")
    pipeline.provider.model_name = "models/gemini-flash-latest"
    pipeline.provider.model = genai.GenerativeModel("models/gemini-flash-latest")

    test_queries = [
        ("Greeting Fast Path", "Hujambo"),
        ("Standalone Knowledge Query", "What are the probation rules under the Kenya Employment Act?"),
        ("Context-Dependent Follow-up", "Can my employer extend it to 8 months?")
    ]

    for label, q in test_queries:
        t0 = time.perf_counter()
        res = pipeline.run(q)
        t1 = time.perf_counter()

        tot_ms = (t1 - t0) * 1000.0
        meta = res.get("eval_metadata", {})
        lat_bd = meta.get("latency_breakdown", {})

        print(f"\n[{label}] Query: \"{q}\"")
        print(f"  ├─ Total Latency        : {tot_ms:.2f} ms")
        print(f"  ├─ Retrieval Gating     : {lat_bd.get('retrieval_gating_ms', 0):.2f} ms")
        print(f"  ├─ Contextualization    : {lat_bd.get('contextualize_ms', 0):.2f} ms")
        print(f"  ├─ Vector Search        : {lat_bd.get('retrieval_ms', 0):.2f} ms")
        print(f"  └─ Gemini Generation    : {lat_bd.get('generation_ms', 0):.2f} ms")

if __name__ == "__main__":
    test_optimized()
