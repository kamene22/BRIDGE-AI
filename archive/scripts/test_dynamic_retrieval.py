import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pipeline import BridgeAIPipeline

pipeline = BridgeAIPipeline()

# Test 1: Dress Code Query
print("=" * 70)
print("TEST 1: DRESS CODE QUERY")
print("Query: I got my first internship what should I wear for my first day?")
print("=" * 70)
res1 = pipeline.run("I got my first internship what should I wear for my first day?")
print("Answer:\n", res1["answer"])
print("Sources:", res1["sources"])

# Test 2: Probation Query
print("\n" + "=" * 70)
print("TEST 2: PROBATION QUERY")
print("Query: how long should probation last?")
print("=" * 70)
res2 = pipeline.run("how long should probation last?")
print("Answer:\n", res2["answer"])
print("Sources:", res2["sources"])
