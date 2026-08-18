"""
src/orchestration/conversation_manager.py — Conversation Orchestrator & Query Contextualizer

Implements:
  1. contextualize_query: Converts ambiguous follow-up questions referencing chat history into standalone queries for RAG search.
  2. Orchestrates retrieval gating, policy determination, and conversation state tracking.
"""

from typing import Tuple, Dict, Any, List, Optional
try:
    from llm_provider.provider import GeminiProvider
    from orchestration.retrieval_gating import RetrievalDecisionEngine, RetrievalAction
    from orchestration.emotional_detector import EmotionalContextDetector, EmotionalRegister
    from orchestration.conversation_policy import ConversationPolicyEngine, PolicyDirective
    from memory.memory import format_history_for_prompt
except ModuleNotFoundError:
    from src.llm_provider.provider import GeminiProvider
    from src.orchestration.retrieval_gating import RetrievalDecisionEngine, RetrievalAction
    from src.orchestration.emotional_detector import EmotionalContextDetector, EmotionalRegister
    from src.orchestration.conversation_policy import ConversationPolicyEngine, PolicyDirective
    from src.memory.memory import format_history_for_prompt


CONTEXTUALIZE_PROMPT = """Given a chat history and the latest user question 
which might reference context in the chat history, formulate a standalone 
question which can be understood without the chat history. Do NOT answer 
the question, just reformulate it if needed and otherwise return it as is."""


def contextualize_query(query: str, conversation_history: str, provider: GeminiProvider) -> str:
    """
    Converts follow-up questions with ambiguous references ("it", "her", "that") into standalone vector search queries.
    """
    if not conversation_history or conversation_history.strip() == "None.":
        return query

    # Check for genuine anaphoric references requiring coreference resolution
    query_lower = query.lower().strip()
    anaphoric_triggers = [
        "it", "its", "her", "she", "he", "him", "his", "they", "them",
        "that", "this", "there", "those", "refuse", "the manager", "the company"
    ]
    words = query_lower.split()

    # Trigger LLM contextualization ONLY if query contains explicit ambiguous reference pronouns
    if any(trigger in words for trigger in anaphoric_triggers):
        user_prompt = f"Chat History:\n{conversation_history}\n\nLatest Question:\n{query}"
        try:
            standalone_q = provider.generate_response(
                prompt=user_prompt,
                system_prompt=CONTEXTUALIZE_PROMPT,
                temperature=0.0,
                max_output_tokens=100
            )
            clean_q = standalone_q.strip().replace('"', '')
            if clean_q:
                return clean_q
        except Exception as e:
            print(f"[Contextualize Warning] Reformulation fallback to original: {e}")

    return query


class ConversationManager:
    def __init__(self):
        self.emotional_detector = EmotionalContextDetector()
        self.retrieval_engine = RetrievalDecisionEngine()
        self.policy_engine = ConversationPolicyEngine()
        self.provider = GeminiProvider()

    def orchestrate_turn(
        self,
        transcript: str,
        session_history: Optional[List[Any]] = None,
        user_profile: Optional[Dict[str, Any]] = None,
        session_id: str = "default"
    ) -> Dict[str, Any]:
        # Step 1: Detect Emotional Register
        emotional_register = self.emotional_detector.detect(transcript)

        # Step 2: Turn Status & History Check
        has_active_context = bool(session_history and len(session_history) > 0)

        # Step 3: Retrieval Decision Gating
        retrieval_action, retrieval_reason, top_k_suggested, route_name = self.retrieval_engine.decide(
            transcript=transcript,
            emotional_register=emotional_register,
            has_active_context=has_active_context
        )

        # Step 4: Contextualize Query for RAG if retrieval is required
        history_str = format_history_for_prompt(session_id) if has_active_context else "None."
        contextualized_q = transcript
        if retrieval_action != RetrievalAction.NO_RETRIEVAL and top_k_suggested > 0:
            contextualized_q = contextualize_query(transcript, history_str, self.provider)

        # Step 5: Policy Determination
        policy = self.policy_engine.determine_policy(
            transcript=transcript,
            emotional_register=emotional_register,
            retrieval_action=retrieval_action
        )

        return {
            "transcript": transcript,
            "contextualized_query": contextualized_q,
            "emotional_register": emotional_register.value,
            "retrieval_action": retrieval_action.value,
            "retrieval_reason": retrieval_reason,
            "top_k_suggested": top_k_suggested,
            "route_name": route_name,
            "policy_directive": policy.value,
            "should_retrieve": retrieval_action != RetrievalAction.NO_RETRIEVAL and top_k_suggested > 0,
            "user_profile": user_profile or {}
        }
