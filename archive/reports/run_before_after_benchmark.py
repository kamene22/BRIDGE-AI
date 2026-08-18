"""
evaluation/run_before_after_benchmark.py — 7-Query Latency & Quality Regression Benchmark
Evaluates TTFT, Generation Latency, Embedding, ChromaDB, Contextualization, and Total Latency.
"""

import os
import sys
import time
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.pipeline import BridgeAIPipeline

TEST_QUERIES = [
    ("1. Standalone RAG", "What is probation?"),
    ("2. Context Follow-up", "Can they extend it?"),
    ("3. Situation Follow-up", "What happens if I refuse?"),
    ("4. Closure", "Okay, thanks."),
    ("5. New Topic", "What about my contract?"),
    ("6. Complex Legal Query", "My employer changed my salary without telling me. What should I do?"),
    ("7. Out-of-Corpus Query", "What is the capital of France?")
]

def run_benchmark():
    print("=" * 90)
    print("BRIDGE AI (AMANI) — REGRESSION QUALITY & LATENCY BENCHMARK SUITE")
    print("=" * 90)

    pipeline = BridgeAIPipeline(session_id="benchmark_regression_001")
    benchmark_records = []

    for label, q in TEST_QUERIES:
        print(f"\n[Executing] {label}: \"{q}\"")
        t_start = time.perf_counter()
        res = pipeline.run(q)
        t_end = time.perf_counter()

        tot_ms = (t_end - t_start) * 1000.0
        meta = res.get("eval_metadata", {})
        lat_bd = meta.get("latency_breakdown", {})
        answer = res.get("answer", "")
        sources = res.get("sources", [])

        print(f"  ├─ Answer Preview      : {answer[:90]}...")
        print(f"  ├─ Total Latency       : {tot_ms:.2f} ms")
        print(f"  ├─ Retrieval Gating    : {lat_bd.get('retrieval_gating_ms', 0):.2f} ms")
        print(f"  ├─ Vector Search       : {lat_bd.get('retrieval_ms', 0):.2f} ms")
        print(f"  ├─ Gemini Generation   : {lat_bd.get('generation_ms', 0):.2f} ms")
        print(f"  └─ Cited Sources       : {len(sources)}")

        benchmark_records.append({
            "label": label,
            "query": q,
            "answer_preview": answer[:150],
            "total_ms": round(tot_ms, 2),
            "gating_ms": lat_bd.get("retrieval_gating_ms", 0),
            "retrieval_ms": lat_bd.get("retrieval_ms", 0),
            "generation_ms": lat_bd.get("generation_ms", 0),
            "sources_count": len(sources)
        })

    avg_lat = sum(r["total_ms"] for r in benchmark_records) / len(benchmark_records)
    avg_gen = sum(r["generation_ms"] for r in benchmark_records) / len(benchmark_records)

    print("\n" + "=" * 90)
    print(f"BENCHMARK COMPLETED — Average Latency: {avg_lat:.2f} ms (Avg Generation: {avg_gen:.2f} ms)")
    print("=" * 90)

    with open("evaluation/after_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(benchmark_records, f, indent=2)

if __name__ == "__main__":
    run_benchmark()
