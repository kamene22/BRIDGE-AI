"""
pipeline.py — Bridge AI Core Orchestration Pipeline (Phase 6 — Full)

This is the central entry point for answering a user query.
Implements the complete 8-step sequence from task.md §6.2, wiring together:
  - Session memory (ConversationMemory)
  - Input guardrails (out-of-scope check, scam detection)
  - Retrieval (ChromaDB corpus search)
  - Prompt construction (system prompt + memory + scam block + chunks)
  - Generation (Gemini via GeminiProvider)
  - Output guardrail (legal boundary check + corrective rewrite)

Design principles (from design document):
  - Hand-rolled pipeline — no framework. Linear with two conditional branches.
  - Corpus is the ONLY source of fact. Memory shapes tone only.
  - "Only the out-of-scope check is a hard branch — skips generation entirely."
  - All other guardrails correct/modify, never block outright.
  - Each guardrail is independently callable and separately testable.
"""

import os
import sys
import time
from typing import Any, Dict, List, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from llm_provider.provider import GeminiProvider
from retrieval.retrieval import RetrievalEngine
from generation.prompt_builder import build_full_prompt_for_plan
from guardrails.out_of_scope import is_out_of_scope
from guardrails.scam_detection import check_scam
from guardrails.legal_boundary import check_legal_boundary
from memory.memory import ConversationMemory
from intent.intent_classifier import IntentClassifier
from planning.response_planner import ResponsePlanner
from orchestration.conversation_manager import ConversationManager


# ─────────────────────────────────────────────────────────────────────────────
# Out-of-scope redirect response — verbatim from design document
# §System Prompt guardrail-specific instruction blocks
# ─────────────────────────────────────────────────────────────────────────────
_OOS_RESPONSE = (
    "That's outside what I'm built to help with. Bridge AI is specifically "
    "here for questions about landing your first job and navigating early "
    "employment in Kenya — from applications and interviews through probation, "
    "workplace norms, pay, and avoiding job scams. If you've got a question "
    "in that space, I'm glad to help."
)


class BridgeAIPipeline:
    """
    Full Hybrid Reasoning RAG + guardrails + memory pipeline for Bridge AI.

    One instance per session — holds a ConversationMemory that accumulates
    turns across multiple `.run()` calls in the same session.
    """

    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        self.provider = GeminiProvider()
        self.retriever = RetrievalEngine()
        self.memory = ConversationMemory()
        self.intent_classifier = IntentClassifier()
        self.response_planner = ResponsePlanner()
        self.conversation_manager = ConversationManager()

    def run(self, query: str) -> Dict[str, Any]:
        """
        Runs the complete hybrid reasoning pipeline for a single user query.
        """
        start_time = time.time()
        
        # ── Step 0: Intent Classification & Response Planning ─────────────
        intent_result = self.intent_classifier.classify(query)
        intent_category = intent_result["intent"]
        response_plan = self.response_planner.create_plan(intent_category)

        trace = {
            "query": query,
            "turn_number": self.memory.turn_count + 1,
            "top_k": self.top_k,
            "intent": intent_result,
            "response_plan": response_plan.to_dict(),
            "guardrails": {
                "out_of_scope": False,
                "scam_detected": False,
                "legal_boundary_triggered": False,
            }
        }

        # ── Step 1: Load conversation memory ─────────────────────────────
        memory_block = self.memory.get_full_memory_block()
        trace["memory_turns_loaded"] = self.memory.turn_count

        # ── Step 2: Out-of-scope check (hard block) ───────────────────────
        if is_out_of_scope(query, self.provider):
            trace["guardrails"]["out_of_scope"] = True
            trace["latency_ms"] = int((time.time() - start_time) * 1000)

            self.memory.add_turn(
                user_message=query,
                assistant_response=_OOS_RESPONSE,
                guardrails_triggered=["out_of_scope"]
            )
            return {
                "answer": _OOS_RESPONSE,
                "sources": [],
                "chunks": [],
                "trace": trace,
                "redirected": True,
            }

        # ── Step 3: Scam detection (corrective, not blocking) ─────────────
        scam_instruction = check_scam(query, self.provider)
        if scam_instruction:
            trace["guardrails"]["scam_detected"] = True

        # ── Step 4: RFC v2 Orchestration & Gated Retrieval ────────────────
        orchestration_context = self.conversation_manager.orchestrate_turn(
            transcript=query,
            session_history=self.memory.turns
        )
        trace["orchestration"] = orchestration_context

        if orchestration_context["should_retrieve"]:
            chunks = self.retriever.retrieve(query, top_k=self.top_k)
        else:
            chunks = []

        trace["chunks_retrieved"] = len(chunks)

        # ── Step 5: Construct dynamic prompt via PromptBuilder ─────────────
        user_profile = memory_block if memory_block else None

        system_prompt, user_prompt = build_full_prompt_for_plan(
            query=query,
            chunks=chunks,
            plan=response_plan,
            user_profile=user_profile
        )

        # ── Step 6: Generate response via LLM provider ─────────────────────
        draft_response = self.provider.generate_response(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            max_output_tokens=1000
        )

        # ── Step 7: Legal boundary output check (corrective rewrite) ──────
        # Design doc: "corrects rather than blocks — assumes the underlying
        # answer is useful and simply needs confidence recalibrated."
        final_response, legal_triggered = check_legal_boundary(draft_response, self.provider)
        trace["guardrails"]["legal_boundary_triggered"] = legal_triggered

        # ── Step 8: Record turn + build source list ───────────────────────
        triggered_guardrails = []
        if trace["guardrails"]["scam_detected"]:
            triggered_guardrails.append("scam_detection")
        if legal_triggered:
            triggered_guardrails.append("legal_boundary")

        self.memory.add_turn(
            user_message=query,
            assistant_response=final_response,
            guardrails_triggered=triggered_guardrails
        )

        sources = []
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            title = meta.get("title", "Unknown Source")
            if "start_line" in meta:
                loc = f"Lines {meta['start_line']}–{meta['end_line']}"
            elif "page" in meta:
                loc = f"Page {meta['page']}"
            else:
                loc = f"Chunk {meta.get('chunk_index', '?')}"
            sources.append(f"{title} ({loc})")

        trace["latency_ms"] = int((time.time() - start_time) * 1000)

        return {
            "answer": final_response,
            "sources": sources,
            "chunks": chunks,
            "trace": trace,
            "redirected": False,
        }

    def reset_session(self) -> None:
        """Clears memory for a new conversation session."""
        self.memory.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Full 4-query smoke test — runs the complete pipeline including guardrails
# and multi-turn memory. Tests all 8 steps.
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pipeline = BridgeAIPipeline(top_k=5)

    print("\n" + "=" * 70)
    print("  BRIDGE AI — Career Mentor for Young Kenyan Professionals")
    print("=" * 70)
    print("  Ask me anything about job search, workplace norms, scams,")
    print("  probation, salary deductions, or your first job in Kenya.")
    print("  Type 'quit' or press Ctrl+C to exit.\n")

    while True:
        try:
            query = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nTake care — good luck out there! 👋")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q", "bye"):
            print("\nTake care — good luck out there! 👋")
            break

        print()
        result = pipeline.run(query)

        print(f"Bridge AI: {result['answer']}")

        if result["sources"]:
            print(f"\n  📄 Sources: {' | '.join(result['sources'][:3])}")

        g = result["trace"]["guardrails"]
        flags = []
        if g["scam_detected"]:
            flags.append("⚠ Scam signal detected")
        if g["out_of_scope"]:
            flags.append("↩ Out of scope")
        if g["legal_boundary_triggered"]:
            flags.append("⚖ Legal answer recalibrated")
        if flags:
            print(f"  {' | '.join(flags)}")

        print(f"  ⏱ {result['trace']['latency_ms']}ms\n")
        print("-" * 70)

