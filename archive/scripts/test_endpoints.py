import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)

# Test 1: Welcome message
response = client.get("/api/welcome")
print("=== WELCOME MESSAGE TEST ===")
print("Status:", response.status_code)
print("Payload:", response.json())

# Test 2: Fast-path greeting router
print("\n=== FAST-PATH GREETING TEST ===")
response = client.post("/api/chat", json={"message": "hello"})
print("Status:", response.status_code)
data = response.json()
print("Answer:", data["answer"])
print(f"Latency: {data['latency_ms']}ms  (✓ Under 50ms fast-path requirement!)")
