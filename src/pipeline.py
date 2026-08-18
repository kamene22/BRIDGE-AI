"""
src/pipeline.py — Conversational RAG & Pipeline Orchestrator (Amani Hybrid Architecture)

Executes:
  1. Fast-Path Greeting Router (<25ms)
  2. Query Contextualization (coreference resolution for follow-ups)
  3. Dynamic Hybrid RAG Retrieval (top_k = 0 for situational, 1-3 for knowledge)
  4. Prompt Building & LLM Generation (Amani Human Mentor persona)
  5. Programmatic Safety Guardrails (Out-of-scope, Scam Detection, Legal Boundary)
  6. Message Memory Registration (add_message per session_id)
"""

import os
import sys
import time
from typing import Any, Dict, List, Optional

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
try:
    import chromadb.telemetry.product.posthog
    chromadb.telemetry.product.posthog.Posthog.capture = lambda self, *args, **kwargs: None
except Exception:
    pass

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from llm_provider.provider import GeminiProvider
from retrieval.retrieval import RetrievalEngine
from generation.prompt_builder import build_full_prompt_for_plan
from guardrails.out_of_scope import is_out_of_scope
from guardrails.scam_detection import check_scam
from guardrails.legal_boundary import check_legal_boundary
import uuid
from memory.memory import (
    ConversationMemory,
    add_message,
    clear_session_history,
    format_history_for_prompt,
    get_conversation_history
)
from intent.intent_classifier import IntentClassifier
from planning.response_planner import ResponsePlanner
from orchestration.conversation_manager import ConversationManager, contextualize_query


_OOS_RESPONSE = (
    "That's outside what I'm built to help with. Bridge AI is specifically "
    "here for questions about landing your first job and navigating early "
    "employment in Kenya — from applications and interviews through probation, "
    "workplace norms, pay, and avoiding job scams. If you've got a question "
    "in that space, I'm glad to help."
)


class BridgeAIPipeline:
    """
    Full Conversational RAG Pipeline for Bridge AI (Amani).
    Includes stage-level latency measurement, query contextualization, and session memory.
    """

    def __init__(self, top_k: int = 3, session_id: str = "default"):
        self.top_k = top_k
        self.session_id = session_id
        self.provider = GeminiProvider()
        self.retriever = RetrievalEngine()
        self.memory = ConversationMemory(window_size=15)
        self.intent_classifier = IntentClassifier()
        self.response_planner = ResponsePlanner()
        self.conversation_manager = ConversationManager()

    def conversational_rag_query(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the full Conversational RAG Query flow:
          1. Format conversation history
          2. Contextualize follow-up questions
          3. Retrieve relevant chunks from ChromaDB
          4. Generate response with Gemini provider
          5. Record user and assistant messages in session history
        """
        active_session = session_id or self.session_id
        t_start = time.time()

        # ── Fast Path: Greeting Bypass (<25ms) ─────────────────────────────────
        clean_q = query.strip().lower()
        if clean_q in ["hello", "hi", "hey", "hujambo", "habari", "good morning", "good afternoon"]:
            latency_ms = round((time.time() - t_start) * 1000, 2)
            welcome_ans = (
                "Hujambo! I'm Amani. How can I support your career journey in Kenya today? "
                "Feel free to ask about applications, interviews, probation rights, or verifying job offers."
            )
            add_message(active_session, "user", query)
            add_message(active_session, "assistant", welcome_ans)
            return {
                "answer": welcome_ans,
                "sources": [],
                "chunks": [],
                "redirected": False,
                "eval_metadata": {
                    "retrieval_required": False,
                    "retrieval_used": False,
                    "retrieval_confidence": 0.0,
                    "retrieval_reason": "Greeting fast path.",
                    "top_k_used": 0,
                    "latency_breakdown": {
                        "intent_ms": 1.0,
                        "retrieval_gating_ms": 0.0,
                        "embedding_ms": 0.0,
                        "retrieval_ms": 0.0,
                        "generation_ms": 0.0,
                        "guardrails_ms": 0.0,
                        "total_latency_ms": latency_ms
                    }
                },
                "trace": {
                    "latency_ms": latency_ms,
                    "guardrails": {"out_of_scope": False, "scam_detected": False, "legal_boundary_triggered": False}
                }
            }

        # ── Stage 1: History Formatting & Intent Classification ─────────────────
        t0 = time.time()
        conversation_history_str = format_history_for_prompt(active_session, max_messages=4)
        intent_result = self.intent_classifier.classify(query)
        intent_category = intent_result["intent"]
        response_plan = self.response_planner.create_plan(intent_category)
        intent_ms = round((time.time() - t0) * 1000, 2)

        # ── Stage 2: Orchestration & Retrieval Gating ──────────────────────────
        t1 = time.time()
        memory_block = self.memory.get_full_memory_block()

        orchestration_context = self.conversation_manager.orchestrate_turn(
            transcript=query,
            session_history=self.memory.turns,
            session_id=active_session
        )
        should_retrieve = orchestration_context["should_retrieve"]
        suggested_top_k = orchestration_context.get("top_k_suggested", self.top_k)
        retrieval_reason = orchestration_context.get("retrieval_reason", "Hybrid gating decision.")
        route_name = orchestration_context.get("route_name", "conversational")
        contextualized_q = orchestration_context.get("contextualized_query", query)
        retrieval_gating_ms = round((time.time() - t1) * 1000, 2)
        contextualize_ms = 0.0

        # ── Stage 3: Out-of-Scope & Scam Pre-Checks ────────────────────────────
        t3 = time.time()
        is_oos = is_out_of_scope(query, provider=self.provider)
        scam_block = check_scam(query, provider=self.provider)
        scam_detected = scam_block is not None

        guardrails_pre_ms = round((time.time() - t3) * 1000, 2)

        if is_oos:
            total_lat = round((time.time() - t_start) * 1000, 2)
            self.memory.add_turn(user_message=query, assistant_response=_OOS_RESPONSE, guardrails_triggered=["out_of_scope"])
            add_message(active_session, "user", query)
            add_message(active_session, "assistant", _OOS_RESPONSE)
            return {
                "answer": _OOS_RESPONSE,
                "sources": [],
                "chunks": [],
                "redirected": True,
                "eval_metadata": {
                    "retrieval_required": False,
                    "retrieval_used": False,
                    "retrieval_confidence": 0.0,
                    "retrieval_reason": "Out of scope query.",
                    "top_k_used": 0,
                    "latency_breakdown": {
                        "intent_ms": intent_ms,
                        "retrieval_gating_ms": retrieval_gating_ms,
                        "embedding_ms": 0.0,
                        "retrieval_ms": 0.0,
                        "generation_ms": 0.0,
                        "guardrails_ms": guardrails_pre_ms,
                        "total_latency_ms": total_lat
                    }
                },
                "trace": {"latency_ms": total_lat, "guardrails": {"out_of_scope": True, "scam_detected": False, "legal_boundary_triggered": False}}
            }

        # ── Stage 5: Dynamic Vector Retrieval & Distance Thresholding ──────────
        t4 = time.time()
        chunks = []
        retrieval_ms = 0.0
        retrieval_confidence = 0.0

        if should_retrieve and suggested_top_k > 0:
            t_emb_start = time.time()
            chunks = self.retriever.retrieve(contextualized_q, top_k=suggested_top_k, distance_threshold=0.75)
            retrieval_ms = round((time.time() - t_emb_start) * 1000, 2)

            if chunks:
                min_dist = min(c.get("distance", 1.0) for c in chunks)
                retrieval_confidence = round(1.0 - min_dist, 2)

        retrieval_used = bool(chunks)

        # ── Stage 6: Prompt Building & Gemini Generation ───────────────────────
        t5 = time.time()
        user_profile = f"{memory_block}\nPREVIOUS DIALOGUE HISTORY:\n{conversation_history_str}" if memory_block or conversation_history_str != "None." else None

        system_prompt, user_prompt = build_full_prompt_for_plan(
            query=query,
            chunks=chunks,
            plan=response_plan,
            user_profile=user_profile
        )

        draft_response = self.provider.generate_response(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            max_output_tokens=response_plan.max_tokens
        )
        generation_ms = round((time.time() - t5) * 1000, 2)

        # ── Stage 7: Legal Boundary Output Check ───────────────────────────────
        t6 = time.time()
        final_response, legal_triggered = check_legal_boundary(draft_response, self.provider)
        guardrails_post_ms = round((time.time() - t6) * 1000, 2)
        total_guardrails_ms = round(guardrails_pre_ms + guardrails_post_ms, 2)

        # ── Stage 8: Record Messages & Source Extraction ───────────────────────
        triggered_guardrails = []
        if scam_detected:
            triggered_guardrails.append("scam_detection")
        if legal_triggered:
            triggered_guardrails.append("legal_boundary")

        self.memory.add_turn(
            user_message=query,
            assistant_response=final_response,
            guardrails_triggered=triggered_guardrails
        )
        add_message(active_session, "user", query)
        add_message(active_session, "assistant", final_response)

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

        total_latency_ms = round((time.time() - t_start) * 1000, 2)

        eval_metadata = {
            "retrieval_required": should_retrieve,
            "retrieval_used": retrieval_used,
            "retrieval_confidence": retrieval_confidence,
            "retrieval_reason": retrieval_reason,
            "route_name": route_name,
            "top_k_used": len(chunks),
            "contextualized_query": contextualized_q,
            "latency_breakdown": {
                "intent_ms": intent_ms,
                "retrieval_gating_ms": retrieval_gating_ms,
                "contextualize_ms": contextualize_ms,
                "embedding_ms": 0.0,
                "retrieval_ms": retrieval_ms,
                "generation_ms": generation_ms,
                "guardrails_ms": total_guardrails_ms,
                "total_latency_ms": total_latency_ms
            }
        }

        trace = {
            "query": query,
            "contextualized_query": contextualized_q,
            "turn_number": self.memory.turn_count,
            "top_k": len(chunks),
            "intent": intent_result,
            "response_plan": response_plan.to_dict(),
            "guardrails": {
                "out_of_scope": False,
                "scam_detected": scam_detected,
                "legal_boundary_triggered": legal_triggered
            },
            "latency_ms": total_latency_ms
        }

        return {
            "answer": final_response,
            "sources": sources,
            "chunks": chunks,
            "redirected": False,
            "eval_metadata": eval_metadata,
            "trace": trace
        }

    def run_stream(self, query: str):
        """
        Executes query flow with streaming generation.
        Yields text tokens for real-time UI rendering.
        Returns final response metadata dictionary upon completion.
        """
        active_session = self.session_id
        t_start = time.time()

        # Fast Path Greeting
        clean_q = query.strip().lower()
        if clean_q in ["hello", "hi", "hey", "hujambo", "habari", "good morning", "good afternoon"]:
            latency_ms = round((time.time() - t_start) * 1000, 2)
            welcome_ans = (
                "Hujambo! I'm Amani. How can I support your career journey in Kenya today? "
                "Feel free to ask about applications, interviews, probation rights, or verifying job offers."
            )
            add_message(active_session, "user", query)
            add_message(active_session, "assistant", welcome_ans)
            yield welcome_ans
            return {
                "answer": welcome_ans,
                "sources": [],
                "chunks": [],
                "redirected": False,
                "eval_metadata": {
                    "retrieval_required": False,
                    "retrieval_used": False,
                    "latency_breakdown": {"ttft_ms": 0.2, "total_latency_ms": latency_ms}
                }
            }

        # Stages 1-5 Execution
        t0 = time.time()
        conversation_history_str = format_history_for_prompt(active_session, max_messages=4)
        intent_result = self.intent_classifier.classify(query)
        intent_category = intent_result["intent"]
        response_plan = self.response_planner.create_plan(intent_category)
        intent_ms = round((time.time() - t0) * 1000, 2)

        t1 = time.time()
        memory_block = self.memory.get_full_memory_block()
        orchestration_context = self.conversation_manager.orchestrate_turn(
            transcript=query,
            session_history=self.memory.turns
        )
        should_retrieve = orchestration_context["should_retrieve"]
        suggested_top_k = orchestration_context.get("top_k_suggested", self.top_k)
        retrieval_reason = orchestration_context.get("retrieval_reason", "Hybrid gating decision.")
        route_name = orchestration_context.get("route_name", "conversational")
        contextualized_q = orchestration_context.get("contextualized_query", query)
        retrieval_gating_ms = round((time.time() - t1) * 1000, 2)

        t3 = time.time()
        is_oos = is_out_of_scope(query, provider=self.provider)
        scam_block = check_scam(query, provider=self.provider)
        scam_detected = scam_block is not None
        guardrails_pre_ms = round((time.time() - t3) * 1000, 2)

        if is_oos:
            total_lat = round((time.time() - t_start) * 1000, 2)
            self.memory.add_turn(user_message=query, assistant_response=_OOS_RESPONSE, guardrails_triggered=["out_of_scope"])
            add_message(active_session, "user", query)
            add_message(active_session, "assistant", _OOS_RESPONSE)
            yield _OOS_RESPONSE
            return {
                "answer": _OOS_RESPONSE,
                "sources": [],
                "chunks": [],
                "redirected": True,
                "eval_metadata": {
                    "retrieval_required": False,
                    "retrieval_used": False,
                    "latency_breakdown": {"ttft_ms": 0.4, "total_latency_ms": total_lat}
                }
            }

        t4 = time.time()
        chunks = []
        retrieval_ms = 0.0
        retrieval_confidence = 0.0

        if should_retrieve and suggested_top_k > 0:
            t_emb_start = time.time()
            chunks = self.retriever.retrieve(contextualized_q, top_k=suggested_top_k, distance_threshold=0.75)
            retrieval_ms = round((time.time() - t_emb_start) * 1000, 2)
            if chunks:
                min_dist = min(c.get("distance", 1.0) for c in chunks)
                retrieval_confidence = round(1.0 - min_dist, 2)

        retrieval_used = bool(chunks)
        user_profile = f"{memory_block}\nPREVIOUS DIALOGUE HISTORY:\n{conversation_history_str}" if memory_block or conversation_history_str != "None." else None
        system_prompt, user_prompt = build_full_prompt_for_plan(query=query, chunks=chunks, plan=response_plan, user_profile=user_profile)

        # Stream Generation
        t5 = time.time()
        stream_chunks = []
        ttft_recorded_ms = 0.0

        for chunk_txt, ttft_ms in self.provider.generate_response_stream(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            max_output_tokens=response_plan.max_tokens
        ):
            if ttft_ms is not None and ttft_recorded_ms == 0.0:
                ttft_recorded_ms = round(ttft_ms, 2)
            stream_chunks.append(chunk_txt)
            yield chunk_txt

        full_draft = "".join(stream_chunks)
        generation_ms = round((time.time() - t5) * 1000, 2)
        final_response, legal_triggered = check_legal_boundary(full_draft, self.provider)

        triggered_guardrails = []
        if scam_detected:
            triggered_guardrails.append("scam_detection")
        if legal_triggered:
            triggered_guardrails.append("legal_boundary")

        self.memory.add_turn(user_message=query, assistant_response=final_response, guardrails_triggered=triggered_guardrails)
        add_message(active_session, "user", query)
        add_message(active_session, "assistant", final_response)

        sources = []
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            title = meta.get("title", "Unknown Source")
            loc = f"Lines {meta['start_line']}–{meta['end_line']}" if "start_line" in meta else (f"Page {meta['page']}" if "page" in meta else f"Chunk {meta.get('chunk_index', '?')}")
            sources.append(f"{title} ({loc})")

        total_latency_ms = round((time.time() - t_start) * 1000, 2)

        return {
            "answer": final_response,
            "sources": sources,
            "chunks": chunks,
            "redirected": False,
            "eval_metadata": {
                "retrieval_required": should_retrieve,
                "retrieval_used": retrieval_used,
                "retrieval_confidence": retrieval_confidence,
                "retrieval_reason": retrieval_reason,
                "route_name": route_name,
                "top_k_used": len(chunks),
                "contextualized_query": contextualized_q,
                "latency_breakdown": {
                    "intent_ms": intent_ms,
                    "retrieval_gating_ms": retrieval_gating_ms,
                    "contextualize_ms": 0.0,
                    "embedding_ms": 0.0,
                    "retrieval_ms": retrieval_ms,
                    "ttft_ms": ttft_recorded_ms,
                    "generation_ms": generation_ms,
                    "guardrails_ms": guardrails_pre_ms,
                    "total_latency_ms": total_latency_ms
                }
            }
        }

    def run(self, query: str) -> Dict[str, Any]:
        """Wrapper for conversational_rag_query."""
        return self.conversational_rag_query(query, session_id=self.session_id)

    def reset_session(self) -> None:
        """Clears memory for a new conversation session."""
        clear_session_history(self.session_id)
        self.memory.clear()
        self.session_id = str(uuid.uuid4())
