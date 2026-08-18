import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from pipeline import BridgeAIPipeline

pipe = BridgeAIPipeline()
res = pipe.conversational_rag_query("I just got my first job. What should I know before my first day?")

print("\n=== ANSWER RETURNED ===")
print(res["answer"])
print("=======================")
print(f"Answer Length: {len(res['answer'])} chars")
