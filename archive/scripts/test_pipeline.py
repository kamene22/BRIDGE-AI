#!/usr/bin/env python3
"""Quick single-query smoke test for the Phase 4 pipeline."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pipeline import BridgeAIPipeline

pipeline = BridgeAIPipeline(top_k=5)
result = pipeline.run("How long is probation in Kenya and can my employer extend it?")

print("=== ANSWER ===")
print(result["answer"])
print()
print("=== SOURCES ===")
for s in result["sources"]:
    print(" •", s)
print()
print(f"Latency: {result['trace']['latency_ms']}ms | Chunks: {result['trace']['chunks_retrieved']}")
