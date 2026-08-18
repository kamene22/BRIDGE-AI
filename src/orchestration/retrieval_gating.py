"""
src/orchestration/retrieval_gating.py — Retrieval Decision Engine & Mandatory Grounding Router

Enforces Corpus Grounding Guarantees:
  - Factual employment law, contracts, probation, pay, statutory deductions, leave, working hours,
    termination, employment rights, and job scams MUST trigger vector retrieval (CORPUS_REQUIRED).
  - Parametric LLM generation without context is explicitly prohibited for factual queries.
  - Pure greetings, acknowledgments, and pure emotional disclosures gate retrieval off (NO_RETRIEVAL).

Routes:
  1. LEGAL           (top_k = 3, statutory RAG) -> RETRIEVE_EMPLOYMENT_ACT
  2. KNOWLEDGE       (top_k = 3, handbook RAG)  -> RETRIEVE_HANDBOOK
  3. SAFETY          (top_k = 3, scam/safety RAG)-> RETRIEVE_HANDBOOK
  4. FOLLOW_UP       (top_k = 2, contextual RAG)-> CONTINUE_CONTEXT / RETRIEVE_HANDBOOK
  5. CONVERSATIONAL  (top_k = 0, no RAG)        -> NO_RETRIEVAL
"""

from enum import Enum
from typing import Tuple, Optional
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
        # Comprehensive Statutory & Legal Terms (triggers Employment Act index)
        self.legal_keywords = [
            "employment act", "section", "notice period", "probation law", "probation period",
            "probation rules", "probation", "statutory deduction", "paye", "nssf", "sha", "nhif", "shif",
            "housing levy", "minimum wage", "leave days", "maternity", "paternity", "unfair termination",
            "wrongful dismissal", "employment contract", "signing my employment contract", "employment rights",
            "dock my pay", "dock pay", "working hours", "maximum hours", "overtime", "annual leave",
            "written contract", "terminated", "fire me", "fired", "sue", "legal", "court", "labour"
        ]

        # Knowledge, Scam & Handbook Topics (triggers Career Handbook index)
        self.knowledge_keywords = [
            "cv", "resume", "interview", "cover letter", "dress code", "wear", "attire", "ngo",
            "scam", "recruiter fee", "agencies", "salary negotiation", "paybill", "mpesa", "registration fee",
            "workplace culture in kenya", "ajira", "nea", "first salary", "net pay", "take home",
            "resignation", "resign", "handover", "1-on-1", "check-in", "first day", "onboarding"
        ]

        # Pure Conversational Greetings & Closures (NO_RETRIEVAL)
        self.greetings_acknowledgments = [
            "hello", "hi", "hey", "good morning", "good afternoon", "thank you", "thanks",
            "thanks, that helps", "thanks that helps", "asante", "asante sana", "okay", "got it", "cool", "bye",
            "maybe.", "exactly.", "yeah, that's what happened.", "i'm probably overthinking this.",
            "good day", "hujambo", "habari"
        ]

        # Pure Emotional Disclosures without factual claims (NO_RETRIEVAL)
        self.pure_emotional_phrases = [
            "terrified", "scared i won't fit in", "feel overwhelmed", "losing confidence",
            "imposter syndrome", "feeling anxious", "don't know if i belong"
        ]

    def decide(
        self,
        transcript: str,
        emotional_register: Optional[EmotionalRegister] = None,
        has_active_context: bool = False
    ) -> Tuple[RetrievalAction, str, int, str]:
        """
        Determines whether vector retrieval is required.
        Returns (RetrievalAction, reason_string, suggested_top_k, route_name).
        """
        text = transcript.lower().strip()
        words = text.split()

        # 1. Pure Greetings / Acknowledgments / Closures -> NO_RETRIEVAL (top_k = 0)
        if any(kw == text for kw in self.greetings_acknowledgments) or text in ["thanks!", "thank you!"]:
            return RetrievalAction.NO_RETRIEVAL, "Greeting, acknowledgment, or conversation closure.", 0, "conversational"

        # 2. Pure Emotional Disclosures without factual/legal query -> NO_RETRIEVAL (top_k = 0)
        if any(phrase in text for phrase in self.pure_emotional_phrases) and not any(k in text for k in self.legal_keywords + self.knowledge_keywords):
            return RetrievalAction.NO_RETRIEVAL, "Pure emotional disclosure requiring human empathy before retrieval.", 0, "emotional"

        # 3. Context inheritance follow-ups ("can they extend it?", "what if I refuse?")
        anaphoric_triggers = ["it", "its", "her", "she", "he", "him", "his", "they", "them", "that", "this", "there", "refuse", "extend"]
        if has_active_context and any(trig in words for trig in anaphoric_triggers) and len(words) <= 7:
            return RetrievalAction.CONTINUE_CONTEXT, "Follow-up turn inherits active session context for RAG.", 2, "conversational"

        # 4. Statutory Legal Queries -> RETRIEVE_EMPLOYMENT_ACT (top_k = 3)
        if any(kw in text for kw in self.legal_keywords):
            return RetrievalAction.RETRIEVE_EMPLOYMENT_ACT, "Knowledge query requiring Kenya Employment Act grounding.", 3, "legal"

        # 5. Handbook & Scam Queries -> RETRIEVE_HANDBOOK (top_k = 3)
        if any(kw in text for kw in self.knowledge_keywords):
            return RetrievalAction.RETRIEVE_HANDBOOK, "Knowledge query requiring career handbook / scam grounding.", 3, "knowledge"

        # 6. Default Grounding Guarantee Policy: Any informative query defaults to RAG (top_k = 2)
        # Avoid parametric LLM generation for unclassified user queries.
        return RetrievalAction.RETRIEVE_HANDBOOK, "General informational query defaulting to grounded retrieval.", 2, "knowledge"
