import json

path = "/mnt/c/Users/user/.gemini/antigravity-ide/brain/dfa7cd28-d487-4ce7-9cd6-0cd3826f1bf1/.system_generated/logs/transcript.jsonl"
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        content = data.get("content", "")
        if data.get("type") == "PLANNER_RESPONSE" and content:
            print(f"=== Step {data.get('step_index')} ===")
            print(content)
            print("-" * 60)
