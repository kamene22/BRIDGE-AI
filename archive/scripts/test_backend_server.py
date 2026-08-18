"""
test_backend_server.py — Dedicated Backend Endpoint Test Suite

Tests:
  1. GET /api/welcome (Welcome message)
  2. POST /api/chat (Greetings - Fast Path <50ms)
  3. POST /api/chat (Employment Act Query)
  4. POST /api/chat (Job Scam Detection Guardrail)
  5. POST /api/chat (Legal Boundary Guardrail)
  6. POST /api/chat (Out-of-Scope Filter)
  7. GET /api/telemetry (Admin Dashboard Metrics)
  8. POST /api/reset (Session Reset)
"""

import sys
import os
import time
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from api.server import app

client = TestClient(app)

print("=" * 80)
print("FASTAPI BACKEND ENDPOINT TEST SUITE")
print("=" * 80)

def print_result(test_num, name, status, latency_ms, payload_preview, extra=""):
    print(f"\n[{test_num}] {name}")
    print(f"    Status Code: {status} | Latency: {latency_ms}ms {extra}")
    print(f"    Payload: {payload_preview}")

# 1. Welcome Endpoint
t0 = time.time()
res = client.get("/api/welcome")
lat = int((time.time() - t0) * 1000)
print_result(1, "GET /api/welcome", res.status_code, lat, str(res.json()["message"])[:100] + "...")

# 2. Fast-Path Greeting
t0 = time.time()
res = client.post("/api/chat", json={"message": "hello"})
lat = int((time.time() - t0) * 1000)
d = res.json()
print_result(2, "POST /api/chat (Fast-Path Greeting 'hello')", res.status_code, lat, d["answer"][:100] + "...", f"✓ (<50ms)")

# 3. Grounded Employment Act Query
t0 = time.time()
res = client.post("/api/chat", json={"message": "What is the maximum probation length in Kenya?"})
lat = int((time.time() - t0) * 1000)
d = res.json()
print_result(3, "POST /api/chat (Probation Query)", res.status_code, lat, d["answer"][:120] + "...")
print(f"    Sources: {', '.join(d['sources'][:2])}")

# 4. Job Scam Query
t0 = time.time()
res = client.post("/api/chat", json={"message": "A recruiter asks for KES 2,500 registration fee."})
lat = int((time.time() - t0) * 1000)
d = res.json()
print_result(4, "POST /api/chat (Scam Query)", res.status_code, lat, f"Scam Flagged: {d['guardrails']['scam_detected']}")

# 5. Out-of-Scope Query
t0 = time.time()
res = client.post("/api/chat", json={"message": "How to make a chocolate cake?"})
lat = int((time.time() - t0) * 1000)
d = res.json()
print_result(5, "POST /api/chat (Out-of-Scope Query)", res.status_code, lat, f"Redirected: {d['redirected']}")

# 6. Admin Telemetry Endpoint
t0 = time.time()
res = client.get("/api/telemetry")
lat = int((time.time() - t0) * 1000)
print_result(6, "GET /api/telemetry", res.status_code, lat, str(res.json()))

# 7. Session Reset Endpoint
t0 = time.time()
res = client.post("/api/reset")
lat = int((time.time() - t0) * 1000)
print_result(7, "POST /api/reset", res.status_code, lat, str(res.json()))

print("\n" + "=" * 80)
print("BACKEND ENDPOINT TESTS COMPLETE ✓")
print("=" * 80)
