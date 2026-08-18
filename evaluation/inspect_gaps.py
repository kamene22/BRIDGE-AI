import json

with open("evaluation/results/corpus_gap_analysis.json", "r") as f:
    data = json.load(f)

print(f"Total Questions: {data['total_questions']}")
print(f"Total Required Facts: {data['total_required_facts']}")
print("Fact Coverage Summary:", data["fact_coverage_summary"])
print("Question Coverage Summary:", data["question_coverage_summary"])
print("\n--- NON-FULLY-SUPPORTED FACTS ---")
for q in data["questions"]:
    for f in q["required_facts"]:
        if f["classification"] != "FULLY_SUPPORTED":
            print(f"[{q['query_id']}] ({f['classification']}) Fact: '{f['fact']}' | Gap: {f['gap_description']}")
