"""
src/orchestration/conversation_manager.py — Central Conversation Orchestrator (RFC v2)

Central application layer coordinating:
1. Turn Manager (Endpointing & Silence Tolerance)
2. Emotional Context Detector (Register classification)
3. Retrieval Decision Engine (Gated vector lookup)
4. Conversation Policy Engine (Action directives)
5. Session Memory & User Profile Assembly

Decouples dialogue orchestration from open-ended LLM language generation.
"""

from typing import Dict, Any, Optional, List
try:
    from orchestration.turn_manager import TurnManager, TurnStatus
    from orchestration.emotional_detector import EmotionalContextDetector, EmotionalRegister
    from orchestration.retrieval_gating import RetrievalDecisionEngine, RetrievalAction
    from orchestration.conversation_policy import ConversationPolicyEngine, PolicyDirective
except ModuleNotFoundError:
    from src.orchestration.turn_manager import TurnManager, TurnStatus
    from src.orchestration.emotional_detector import EmotionalContextDetector, EmotionalRegister
    from src.orchestration.retrieval_gating import RetrievalDecisionEngine, RetrievalAction
    from src.orchestration.conversation_policy import ConversationPolicyEngine, PolicyDirective

class ConversationManager:
    def __init__(self):
        self.turn_manager = TurnManager()
        self.emotional_detector = EmotionalContextDetector()
        self.retrieval_engine = RetrievalDecisionEngine()
        self.policy_engine = ConversationPolicyEngine()

    def orchestrate_turn(
        self,
        transcript: str,
        silence_duration: float = 0.5,
        session_history: Optional[List[Dict[str, str]]] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Runs complete RFC v2 orchestration workflow.
        Returns a structured decision context object for prompt building.
        """
        # Step 1: Detect Emotional Register
        emotional_register = self.emotional_detector.detect(transcript)

        # Step 2: Evaluate Turn Endpointing
        turn_status = self.turn_manager.evaluate_turn(
            transcript=transcript,
            silence_duration=silence_duration,
            emotional_state=emotional_register.value
        )

        # Step 3: Retrieval Decision Gating
        has_active_context = bool(session_history and len(session_history) > 0)
        retrieval_action, retrieval_reason = self.retrieval_engine.decide(
            transcript=transcript,
            emotional_register=emotional_register,
            has_active_context=has_active_context
        )

        # Step 4: Determine Explicit Conversation Policy
        policy = self.policy_engine.determine_policy(
            transcript=transcript,
            emotional_register=emotional_register,
            retrieval_action=retrieval_action
        )

        return {
            "transcript": transcript,
            "turn_status": turn_status.value,
            "emotional_register": emotional_register.value,
            "retrieval_action": retrieval_action.value,
            "retrieval_reason": retrieval_reason,
            "policy_directive": policy.value,
            "should_retrieve": retrieval_action != RetrievalAction.NO_RETRIEVAL,
            "user_profile": user_profile or {}
        }
