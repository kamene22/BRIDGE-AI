"""
intent_classifier.py — Intent Classification Engine for Hybrid Reasoning Architecture
Categorizes incoming user queries into 6 distinct intent categories:
1. KNOWLEDGE (Factual objective lookup)
2. PROCEDURAL (Step-by-step guidance)
3. SITUATIONAL (Interpersonal workplace scenarios & conflict)
4. REFLECTIVE (Emotional state, identity, confidence)
5. LEGAL (Employment rights & statutory laws)
6. SCAM (Recruiter fees & job scams)
"""

from enum import Enum
from typing import Dict, Any


class IntentCategory(str, Enum):
    KNOWLEDGE = "knowledge"
    PROCEDURAL = "procedural"
    SITUATIONAL = "situational"
    REFLECTIVE = "reflective"
    LEGAL = "legal"
    SCAM = "scam"


class IntentClassifier:
    """Classifies user queries into discrete intent categories to drive response planning."""

    SCAM_KEYWORDS = [
        "paybill", "mpesa", "registration fee", "interview fee", "medical fee",
        "uniform fee", "pay money", "fake job", "scam"
    ]

    LEGAL_KEYWORDS = [
        "can they fire me", "fire me", "can i sue", "is this legal", "employment act",
        "wrongful dismissal", "unfair termination", "notice period", "severance",
        "statutory leave", "maternity leave", "paternity leave", "public holiday pay", "terminated"
    ]

    SITUATIONAL_KEYWORDS = [
        "manager hates me", "boss hates me", "manager dislikes me", "boss shouted",
        "sent an email to the wrong person", "sent email to wrong", "missed a deadline",
        "coworkers ignore me", "coworkers dislike me", "conflict with colleague",
        "my manager ignored", "boss ignored", "disagree with manager"
    ]

    REFLECTIVE_KEYWORDS = [
        "feel stuck", "feel overwhelmed", "don't know if i belong", "losing confidence",
        "imposter syndrome", "feeling anxious", "should i quit", "don't think i'm doing a good job",
        "scared i'll fail", "fear of failing", "overwhelmed"
    ]

    PROCEDURAL_KEYWORDS = [
        "how do i resign", "how to resign", "how to ask for feedback",
        "how do i prepare for", "how to prepare for my first day", "how to write a cover letter",
        "how to structure my cv", "how do i request leave"
    ]

    def classify(self, text: str) -> Dict[str, Any]:
        """Classify user text into an IntentCategory with confidence scoring and matching cues."""
        p_lower = text.lower().strip()

        # 1. SCAM SIGNAL CHECK
        if any(k in p_lower for k in self.SCAM_KEYWORDS):
            return {
                "intent": IntentCategory.SCAM,
                "confidence": 0.95,
                "reason": "Detected job scam fee or paybill keywords."
            }

        # 2. LEGAL CHECK
        if any(k in p_lower for k in self.LEGAL_KEYWORDS):
            return {
                "intent": IntentCategory.LEGAL,
                "confidence": 0.90,
                "reason": "Detected statutory employment rights or legal termination query."
            }

        # 3. SITUATIONAL CHECK
        if any(k in p_lower for k in self.SITUATIONAL_KEYWORDS):
            return {
                "intent": IntentCategory.SITUATIONAL,
                "confidence": 0.88,
                "reason": "Detected interpersonal workplace scenario or manager dynamics."
            }

        # 4. REFLECTIVE CHECK
        if any(k in p_lower for k in self.REFLECTIVE_KEYWORDS):
            return {
                "intent": IntentCategory.REFLECTIVE,
                "confidence": 0.85,
                "reason": "Detected emotional state, self-doubt, or confidence reflection."
            }

        # 5. PROCEDURAL CHECK
        if any(k in p_lower for k in self.PROCEDURAL_KEYWORDS) or p_lower.startswith("how do i") or p_lower.startswith("how to"):
            return {
                "intent": IntentCategory.PROCEDURAL,
                "confidence": 0.82,
                "reason": "Detected procedural step-by-step guidance request."
            }

        # 6. DEFAULT TO KNOWLEDGE
        return {
            "intent": IntentCategory.KNOWLEDGE,
            "confidence": 0.75,
            "reason": "Default factual knowledge query."
        }
