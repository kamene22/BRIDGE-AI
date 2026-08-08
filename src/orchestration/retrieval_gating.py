"""
src/orchestration/retrieval_gating.py — Retrieval Decision Engine (RFC v2)

Gates ChromaDB vector retrieval so that greetings, follow-ups, acknowledgments,
and initial emotional disclosures bypass vector search, eliminating ~600ms of
unnecessary latency on 60%+ of turns.
"""

from enum import Enum
from typing import Tuple
try:
    from orchestration.emotional_detector import EmotionalRegister
except ModuleNotFoundError:
    from src.orchestration.emotional_detector import EmotionalRegister

class RetrievalAction(str, Enum):
    NO_RETRIEVAL = "NO_RETRIEVAL"
    RETRIEVE_EMPLOYMENT_ACT = "RETRIEVE_EMPLOYMENT_ACT"
    RETRIEVE_HANDBOOK = "RETRIEVE_HANDBOOK"
    CONTINUE_CONTEXT = "CONTINUE_CONTEXT"

class RetrievalDecisionEngine:
    def __init__(self):
        self.factual_legal_keywords = [
            "employment act", "section", "notice period", "probation law", "statutory deduction",
            "paye", "nssf", "sha", "nhif", "housing levy", "minimum wage", "leave days", "maternity"
        ]
        self.handbook_keywords = [
            "cv", "resume", "interview tips", "cover letter", "dress code", "first day",
            "scam", "recruiter fee", "agencies", "salary negotiation"
        ]
        self.greetings_acknowledgments = [
            "hello", "hi", "hey", "good morning", "good afternoon", "thank you", "thanks",
            "asante", "okay", "got it", "cool", "bye"
        ]

    def decide(
        self,
        transcript: str,
        emotional_register: EmotionalRegister,
        has_active_context: bool = False
    ) -> Tuple[RetrievalAction, str]:
        """
        Determines whether vector retrieval is required.
        Returns (RetrievalAction, reason_string).
        """
        text = transcript.lower().strip()
        words = text.split()

        # 1. Greetings / Acknowledgments -> NO_RETRIEVAL
        if any(kw == text for kw in self.greetings_acknowledgments) or (len(words) <= 3 and any(k in text for k in self.greetings_acknowledgments)):
            return RetrievalAction.NO_RETRIEVAL, "Greeting / acknowledgment query."

        # 2. Pure emotional disclosure without explicit question -> NO_RETRIEVAL (Empathy first)
        if emotional_register in [EmotionalRegister.JOB_LOSS, EmotionalRegister.WORKPLACE_CONFLICT, EmotionalRegister.GENERAL_OVERWHELM]:
            if not any(q_word in text for q_word in ["what", "how", "can i", "is it legal", "should i", "where"]):
                return RetrievalAction.NO_RETRIEVAL, f"Emotional disclosure ({emotional_register.value}) requires empathy before retrieval."

        # 3. Explicit legal lookup -> RETRIEVE_EMPLOYMENT_ACT
        if any(kw in text for kw in self.factual_legal_keywords):
            return RetrievalAction.RETRIEVE_EMPLOYMENT_ACT, "Explicit Kenya Employment Act statutory query."

        # 4. Handbook / career query -> RETRIEVE_HANDBOOK
        if any(kw in text for kw in self.handbook_keywords):
            return RetrievalAction.RETRIEVE_HANDBOOK, "Career handbook query."

        # 5. Short continuation / follow-up -> CONTINUE_CONTEXT or NO_RETRIEVAL
        if has_active_context and len(words) <= 7:
            return RetrievalAction.CONTINUE_CONTEXT, "Follow-up question reuses active session context."

        # Default fallback: Retrieve handbook for general career queries
        return RetrievalAction.RETRIEVE_HANDBOOK, "General career navigation query."
