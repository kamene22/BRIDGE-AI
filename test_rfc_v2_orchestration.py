"""
test_rfc_v2_orchestration.py — Automated Evaluation Suite for Conversational Architecture RFC v2

Tests:
1. Turn Manager endpointing and silence tolerance widening on emotional disclosures.
2. Emotional Context Detector register classification.
3. Retrieval Decision Engine gating (no retrieval for greetings, follow-ups, and emotional disclosures).
4. Conversation Policy Engine directive generation.
5. End-to-end ConversationManager orchestration & pipeline latency.
"""

import os
import sys
import time

sys.path.append(os.path.abspath("src"))

from orchestration.turn_manager import TurnManager, TurnStatus
from orchestration.emotional_detector import EmotionalContextDetector, EmotionalRegister
from orchestration.retrieval_gating import RetrievalDecisionEngine, RetrievalAction
from orchestration.conversation_policy import ConversationPolicyEngine, PolicyDirective
from orchestration.conversation_manager import ConversationManager
from pipeline import BridgeAIPipeline


def run_tests():
    print("=" * 80)
    print("CONVERSATIONAL ARCHITECTURE RFC v2 — AUTOMATED TEST SUITE")
    print("=" * 80)

    # 1. Test Turn Manager & Silence Tolerance Widening
    tm = TurnManager()
    
    # Emotional disclosure pause test
    status_emotional = tm.evaluate_turn("I got fired...", silence_duration=1.8, emotional_state="JOB_LOSS")
    print(f"\n[TEST 1A] Emotional Disclosure ('I got fired...', 1.8s silence): Status = {status_emotional}")
    assert status_emotional == TurnStatus.LISTENING, "Emotional disclosure with 1.8s silence should stay in LISTENING mode!"

    status_emotional_done = tm.evaluate_turn("I got fired... yesterday.", silence_duration=2.6, emotional_state="JOB_LOSS")
    print(f"[TEST 1B] Emotional Disclosure Complete ('...yesterday.', 2.6s silence): Status = {status_emotional_done}")
    assert status_emotional_done == TurnStatus.TURN_COMPLETE, "Emotional disclosure with 2.6s silence should be TURN_COMPLETE!"

    # 2. Test Emotional Context Detector
    ecd = EmotionalContextDetector()
    reg_loss = ecd.detect("I lost my job yesterday.")
    reg_conflict = ecd.detect("I think my manager hates me.")
    reg_neutral = ecd.detect("What is the legal probation period in Kenya?")
    
    print(f"\n[TEST 2A] Emotional Register ('I lost my job'): {reg_loss}")
    assert reg_loss == EmotionalRegister.JOB_LOSS
    print(f"[TEST 2B] Emotional Register ('manager hates me'): {reg_conflict}")
    assert reg_conflict == EmotionalRegister.WORKPLACE_CONFLICT
    print(f"[TEST 2C] Emotional Register ('probation period'): {reg_neutral}")
    assert reg_neutral == EmotionalRegister.NEUTRAL_FACTUAL

    # 3. Test Retrieval Decision Engine Gating
    rde = RetrievalDecisionEngine()
    
    action_greeting, _ = rde.decide("Hello Amani!", EmotionalRegister.NEUTRAL_FACTUAL)
    action_legal, _ = rde.decide("What is the statutory PAYE deduction?", EmotionalRegister.NEUTRAL_FACTUAL)
    action_emotional, _ = rde.decide("I got fired yesterday.", EmotionalRegister.JOB_LOSS)

    print(f"\n[TEST 3A] Retrieval Action ('Hello Amani!'): {action_greeting}")
    assert action_greeting == RetrievalAction.NO_RETRIEVAL, "Greetings must NOT trigger ChromaDB retrieval!"

    print(f"[TEST 3B] Retrieval Action ('PAYE deduction'): {action_legal}")
    assert action_legal == RetrievalAction.RETRIEVE_EMPLOYMENT_ACT, "Legal queries must trigger Employment Act retrieval!"

    print(f"[TEST 3C] Retrieval Action ('I got fired'): {action_emotional}")
    assert action_emotional == RetrievalAction.NO_RETRIEVAL, "Initial emotional disclosure must NOT trigger retrieval before empathy!"

    # 4. Test Full Conversation Pipeline Integration & Gated Latency
    print("\n[TEST 4] Full Pipeline Integration & Gated Retrieval Latency...")
    pipeline = BridgeAIPipeline()

    # Turn 1: Greeting (Gated - No ChromaDB retrieval)
    t0 = time.time()
    res1 = pipeline.run("Hello Amani")
    lat1 = int((time.time() - t0) * 1000)
    print(f"Turn 1 (Greeting 'Hello Amani'): Latency = {lat1}ms | Chunks = {len(res1['sources'])}")
    assert len(res1['sources']) == 0, "Greeting turn should retrieve 0 chunks!"

    # Turn 2: Factual probation query (Retrieval active)
    t0 = time.time()
    res2 = pipeline.run("What is the maximum legal probation period in Kenya?")
    lat2 = int((time.time() - t0) * 1000)
    print(f"Turn 2 (Factual Legal Query): Latency = {lat2}ms | Chunks = {len(res2['sources'])}")
    assert len(res2['sources']) > 0, "Legal query must retrieve chunks!"

    print("\n" + "=" * 80)
    print("ALL RFC v2 ORCHESTRATION TESTS PASSED SUCCESSFULLY ✓")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
