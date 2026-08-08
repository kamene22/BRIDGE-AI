"""
src/orchestration/conversation_policy.py — Conversation Policy Engine (RFC v2)

Emits explicit action directives for Gemini generation:
- EMPATHIZE
- RETRIEVE_THEN_ANSWER
- ASK_FOLLOW_UP
- GIVE_ADVICE
- ACKNOWLEDGE
- CLOSE_CONVERSATION
"""

from enum import Enum
try:
    from orchestration.emotional_detector import EmotionalRegister
    from orchestration.retrieval_gating import RetrievalAction
except ModuleNotFoundError:
    from src.orchestration.emotional_detector import EmotionalRegister
    from src.orchestration.retrieval_gating import RetrievalAction

class PolicyDirective(str, Enum):
    EMPATHIZE = "EMPATHIZE"
    RETRIEVE_THEN_ANSWER = "RETRIEVE_THEN_ANSWER"
    ASK_FOLLOW_UP = "ASK_FOLLOW_UP"
    GIVE_ADVICE = "GIVE_ADVICE"
    ACKNOWLEDGE = "ACKNOWLEDGE"
    CLOSE_CONVERSATION = "CLOSE_CONVERSATION"

class ConversationPolicyEngine:
    def determine_policy(
        self,
        transcript: str,
        emotional_register: EmotionalRegister,
        retrieval_action: RetrievalAction,
        is_closing: bool = False
    ) -> PolicyDirective:
        """Determines explicit policy directive to hand to PromptBuilder."""
        text = transcript.lower().strip()

        if is_closing or any(kw in text for kw in ["thank you", "thanks", "asante", "bye", "goodnight"]):
            return PolicyDirective.CLOSE_CONVERSATION

        if emotional_register in [EmotionalRegister.JOB_LOSS, EmotionalRegister.WORKPLACE_CONFLICT, EmotionalRegister.GENERAL_OVERWHELM]:
            if retrieval_action == RetrievalAction.NO_RETRIEVAL:
                return PolicyDirective.EMPATHIZE

        if retrieval_action in [RetrievalAction.RETRIEVE_EMPLOYMENT_ACT, RetrievalAction.RETRIEVE_HANDBOOK]:
            return PolicyDirective.RETRIEVE_THEN_ANSWER

        if len(text.split()) <= 4 and any(kw in text for kw in ["hello", "hi", "hey"]):
            return PolicyDirective.ACKNOWLEDGE

        return PolicyDirective.GIVE_ADVICE
