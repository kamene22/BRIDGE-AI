#!/usr/bin/env python3
"""
Phase 5+6 structural dry-run test.
Verifies guardrail logic, memory management, and full prompt construction
WITHOUT calling the generation API (quota may be exhausted).
"""
import sys, os
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from memory.memory import ConversationMemory
from generation.prompt_builder import build_full_prompt
from guardrails.scam_detection import SCAM_INSTRUCTION_BLOCK

PASS = "✓"
FAIL = "✗"

print("=" * 70)
print("PHASE 5+6 STRUCTURAL DRY-RUN TEST")
print("=" * 70)

# ── Test 1: Memory sliding window ─────────────────────────────────────────
print("\n[TEST 1] ConversationMemory — sliding window (window_size=3)")
mem = ConversationMemory(window_size=3)
for i in range(5):
    mem.add_turn(f"User question {i+1}", f"AI answer {i+1}")
assert mem.turn_count == 3, f"Expected 3 turns, got {mem.turn_count}"
assert "question 3" in mem.turns[0].user_message
assert "question 5" in mem.turns[2].user_message
print(f"  {PASS} Window correctly holds last 3 of 5 turns")
print(f"  {PASS} Oldest turn: '{mem.turns[0].user_message}'")
print(f"  {PASS} Newest turn: '{mem.turns[2].user_message}'")

# ── Test 2: User profile extraction ──────────────────────────────────────
print("\n[TEST 2] UserProfile — signal extraction from messages")
mem2 = ConversationMemory()
mem2.add_turn(
    "I'm a fresh graduate who just started at an NGO in Nairobi",
    "Great, welcome to the workforce!"
)
assert mem2.profile.career_stage == "fresh graduate", f"Got: {mem2.profile.career_stage}"
assert mem2.profile.employer_type == "NGO/non-profit", f"Got: {mem2.profile.employer_type}"
assert mem2.profile.location == "Nairobi", f"Got: {mem2.profile.location}"
print(f"  {PASS} Career stage: '{mem2.profile.career_stage}'")
print(f"  {PASS} Employer type: '{mem2.profile.employer_type}'")
print(f"  {PASS} Location: '{mem2.profile.location}'")

# ── Test 3: Memory block formatting ───────────────────────────────────────
print("\n[TEST 3] Memory block — prompt formatting")
block = mem2.get_full_memory_block()
assert "USER CONTEXT" in block, "Missing USER CONTEXT header"
assert "NGO/non-profit" in block, "Profile not in block"
assert "CONVERSATION HISTORY" in block, "Missing history header"
print(f"  {PASS} Block length: {len(block)} chars")
print(f"  {PASS} Contains profile context")
print(f"  {PASS} Contains conversation history")
print(f"\n  Preview:\n{block[:350]}...")

# ── Test 4: Scam instruction block exists and is non-empty ────────────────
print("\n[TEST 4] Scam instruction block")
assert len(SCAM_INSTRUCTION_BLOCK) > 100, "Scam block too short"
assert "upfront payment" in SCAM_INSTRUCTION_BLOCK.lower()
assert "verification steps" in SCAM_INSTRUCTION_BLOCK.lower()
print(f"  {PASS} Block length: {len(SCAM_INSTRUCTION_BLOCK)} chars")
print(f"  {PASS} Contains 'upfront payment' reference")
print(f"  {PASS} Contains 'verification steps' reference")

# ── Test 5: Full prompt construction with memory + scam block ─────────────
print("\n[TEST 5] Full prompt with memory + scam instruction block")
mock_chunks = [
    {
        "document": "No employer shall request upfront fees from a job applicant before employment begins.",
        "metadata": {"title": "Job Scam Red Flags", "source": "corpus/job_scam_red_flags.md",
                     "start_line": 10, "end_line": 20, "chunk_index": 0}
    }
]
memory_block = mem2.get_full_memory_block()
extra = SCAM_INSTRUCTION_BLOCK + "\n\n" + memory_block

sys_p, user_p = build_full_prompt(
    query="They asked me to pay KES 2,500 before I start",
    chunks=mock_chunks,
    extra_system_instructions=extra
)

assert "Bridge AI" in sys_p
assert SCAM_INSTRUCTION_BLOCK[:50] in sys_p
assert "USER CONTEXT" in sys_p
assert "Job Scam Red Flags" in user_p
assert "[1]" in user_p
print(f"  {PASS} System prompt: {len(sys_p)} chars (base + scam block + memory)")
print(f"  {PASS} Scam instruction block present in system prompt")
print(f"  {PASS} Memory context present in system prompt")
print(f"  {PASS} Corpus chunk [1] present in user prompt")
print(f"  {PASS} User prompt total: {len(user_p)} chars")

# ── Test 6: Memory reset ───────────────────────────────────────────────────
print("\n[TEST 6] Memory session reset")
mem2.clear()
assert mem2.turn_count == 0
assert mem2.profile.is_empty()
assert mem2.get_full_memory_block() == ""
print(f"  {PASS} Turn count reset to 0")
print(f"  {PASS} Profile cleared")
print(f"  {PASS} Memory block is empty string after reset")

print("\n" + "=" * 70)
print("ALL PHASE 5+6 STRUCTURAL TESTS PASSED ✓")
print("Components verified:")
print("  • ConversationMemory (sliding window, signal extraction, formatting)")
print("  • UserProfile (career stage, employer type, location)")
print("  • Guardrail instruction blocks (scam: content verified)")
print("  • Full prompt builder (system + scam block + memory + chunks)")
print("  • Session reset")
print("\nGeneration API tests deferred — quota check live when available.")
print("=" * 70)
