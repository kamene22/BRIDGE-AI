import sys, os
sys.path.insert(0, "src")
from pipeline import BridgeAIPipeline

pipeline = BridgeAIPipeline()
res = pipeline.run("not yet what should I expect")
print("RESPONSE:\n", res["answer"])
