"""
src/orchestration/emotional_detector.py — Emotional Register Detector (RFC v2)

Classifies user transcripts into explicit emotional registers to route policy
towards empathy-first responses before advice or legal retrieval.
"""

from enum import Enum
import re

class EmotionalRegister(str, Enum):
    PRE_INTERVIEW_ANXIETY = "PRE_INTERVIEW_ANXIETY"
    WORKPLACE_CONFLICT = "WORKPLACE_CONFLICT"
    JOB_LOSS = "JOB_LOSS"
    GENERAL_OVERWHELM = "GENERAL_OVERWHELM"
    NEUTRAL_FACTUAL = "NEUTRAL_FACTUAL"

class EmotionalContextDetector:
    def __init__(self):
        self.keywords = {
            EmotionalRegister.JOB_LOSS: [
                "got fired", "was fired", "terminated", "lost my job", "laid off",
                "let go", "sacked", "dismissed", "lost my seat"
            ],
            EmotionalRegister.WORKPLACE_CONFLICT: [
                "manager hates me", "boss hates me", "boss ignores me", "manager barely talks",
                "toxic environment", "screaming at me", "shouting", "unfair warning", "blaming me"
            ],
            EmotionalRegister.PRE_INTERVIEW_ANXIETY: [
                "terrified", "so nervous", "scared for interview", "anxious", "freaking out",
                "intimidated", "scared I will fail"
            ],
            EmotionalRegister.GENERAL_OVERWHELM: [
                "overwhelmed", "stressed out", "exhausted", "don't know what to do", "lost",
                "crying", "depressed about work"
            ]
        }

    def detect(self, transcript: str) -> EmotionalRegister:
        """Classifies transcript into an EmotionalRegister enum."""
        text = transcript.lower().strip()
        if not text:
            return EmotionalRegister.NEUTRAL_FACTUAL

        for register, phrase_list in self.keywords.items():
            for phrase in phrase_list:
                if phrase in text:
                    return register

        return EmotionalRegister.NEUTRAL_FACTUAL
