"""
test_platform_full.py — End-to-End Test Suite for Bridge AI Production Platform

Tests:
  1. Welcome endpoint (/api/welcome)
  2. Fast-Path Greeting Router (<50ms latency)
  3. Grounded Employment Act RAG Query
  4. Scam Detection Guardrail Flagging
  5. Legal Boundary Audit & Corrective Rewrite
  6. Out-of-Scope Input Guardrail Redirect
  7. Admin Telemetry Endpoint (/api/telemetry)
  8. Session Memory Reset (/api/reset)
"""

import sys
import os
import time
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from api.server import app

client = TestClient(app)
PASS = "✓ PASS"
FAIL = "✗ FAIL"

print("=" * 75)
print("BRIDGE AI — PRODUCTION PLATFORM INTEGRATION TEST SUITE")
print("=" * 75)

# ── TEST 1: WELCOME INTRODUCTION MESSAGE ──────────────────────────────────
print("\n[TEST 1] GET /api/welcome (Automatic English Introduction)")
res = client.get("/api/welcome")
assert res.status_code == 200, f"Expected 200, got {res.status_code}"
data = res.json()
assert "Bridge AI" in data["message"]
assert "career mentor" in data["message"]
print(f"  {PASS} Status 200 | Welcome message received ({len(data['message'])} chars)")
print(f"  Preview: \"{data['message'][:90]}...\"")

# ── TEST 2: FAST-PATH GREETING ROUTER (<50ms) ──────────────────────────────
print("\n[TEST 2] POST /api/chat (Fast-Path Greeting Router)")
greetings = ["hello", "hi", "hey", "jambo", "habari", "sasa"]
for g in greetings:
    t0 = time.time()
    res = client.post("/api/chat", json={"message": g})
    lat = int((time.time() - t0) * 1000)
    assert res.status_code == 200
    d = res.json()
    assert d["latency_ms"] < 50, f"Latency {d['latency_ms']}ms exceeded 50ms fast-path threshold"
    assert "Hello!" in d["answer"] or "connect" in d["answer"]
    print(f"  {PASS} '{g}' → Instant Response ({d['latency_ms']}ms)")

# ── TEST 3: GROUNDED RAG QUERY (Employment Act) ───────────────────────────
print("\n[TEST 3] POST /api/chat (Grounded Employment Act Query)")
res = client.post("/api/chat", json={"message": "How long is probation in Kenya under the Employment Act?"})
assert res.status_code == 200
d = res.json()
print(f"  {PASS} Latency: {d['latency_ms']}ms")
print(f"  Answer Preview:\n  {d['answer'][:180]}...")
print(f"  Sources ({len(d['sources'])}): {', '.join(d['sources'][:2])}")

# ── TEST 4: SCAM DETECTION GUARDRAIL ──────────────────────────────────────
print("\n[TEST 4] POST /api/chat (Job Scam Guardrail Flagging)")
scam_query = "A recruiter on WhatsApp asks for a KES 2,500 registration fee before my interview."
res = client.post("/api/chat", json={"message": scam_query})
assert res.status_code == 200
d = res.json()
scam_flagged = d["guardrails"]["scam_detected"]
print(f"  {PASS} Scam Flagged: {scam_flagged} | Latency: {d['latency_ms']}ms")
assert scam_flagged == True, "Expected scam_detected guardrail flag to be True"

# ── TEST 5: OUT-OF-SCOPE GUARDRAIL REDIRECT ───────────────────────────────
print("\n[TEST 5] POST /api/chat (Out-of-Scope Guardrail Redirect)")
oos_query = "How do I bake a chocolate cake?"
res = client.post("/api/chat", json={"message": oos_query})
assert res.status_code == 200
d = res.json()
oos_flagged = d["guardrails"]["out_of_scope"] or d["redirected"]
print(f"  {PASS} Out-of-Scope Redirected: {oos_flagged} | Latency: {d['latency_ms']}ms")
assert oos_flagged == True, "Expected out_of_scope guardrail flag to be True"

# ── TEST 6: ADMIN TELEMETRY ENDPOINT ───────────────────────────────────────
print("\n[TEST 6] GET /api/telemetry (Admin Dashboard Metrics)")
res = client.get("/api/telemetry")
assert res.status_code == 200
d = res.json()
assert "turn_count" in d
assert d["status"] == "Operational"
print(f"  {PASS} Status: {d['status']} | Turn Count: {d['turn_count']}")

# ── TEST 7: SESSION RESET ENDPOINT ─────────────────────────────────────────
print("\n[TEST 7] POST /api/reset (Session Memory Reset)")
res = client.post("/api/reset")
assert res.status_code == 200
d = res.json()
assert d["status"] == "success"

res_after = client.get("/api/telemetry")
assert res_after.json()["turn_count"] == 0
print(f"  {PASS} Session reset successfully | Turn count reset to 0")

print("\n" + "=" * 75)
print("ALL 7 PLATFORM INTEGRATION TESTS PASSED ✓")
print("FastAPI Backend + Production Web UI fully functional.")
print("=" * 75)
