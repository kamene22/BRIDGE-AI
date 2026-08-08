"""
src/orchestration/turn_manager.py — Endpoint & Turn Completion Manager (RFC v2)

Evaluates raw VAD speech/no-speech frames and transcript cues to decide
whether a user's turn has finished, applying widened silence tolerance
during emotional disclosures.
"""

import re
from enum import Enum
from typing import Dict, Any, Optional

class TurnStatus(str, Enum):
    LISTENING = "LISTENING"          # User is still speaking or pausing mid-thought
    TURN_COMPLETE = "TURN_COMPLETE"  # User has completed their turn
    INTERRUPTED = "INTERRUPTED"      # User barged in while assistant was speaking

class TurnManager:
    def __init__(self):
        # Base silence thresholds (in seconds)
        self.default_silence_threshold = 0.5
        self.emotional_silence_threshold = 2.5
        self.disfluency_silence_threshold = 1.2

        # Trailing conjunctions / disfluencies indicating incomplete thought
        self.disfluency_patterns = [
            r"\b(and|or|so|but|because|like|um|uh|you know|i mean)\s*$",
            r"\.\.\.\s*$",
            r",\s*$"
        ]

    def is_sentence_complete(self, transcript: str) -> bool:
        """Evaluates whether transcript looks grammatically complete."""
        text = transcript.strip()
        if not text:
            return False

        # Trailing disfluency check
        for pattern in self.disfluency_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False

        # Ends with sentence closing punctuation or natural clause completion
        if text[-1] in [".", "!", "?", "…"]:
            return True

        # Word count & clause heuristic
        words = text.split()
        if len(words) >= 3 and not text.lower().endswith(("and", "so", "but", "because", "or", "like")):
            return True

        return False

    def evaluate_turn(
        self,
        transcript: str,
        silence_duration: float,
        emotional_state: Optional[str] = None
    ) -> TurnStatus:
        """
        Determines whether the turn has ended given silence duration,
        sentence completeness, and emotional state.
        """
        text = transcript.strip()
        if not text:
            return TurnStatus.LISTENING

        # Determine active silence tolerance threshold
        threshold = self.default_silence_threshold
        if emotional_state in ["JOB_LOSS", "WORKPLACE_CONFLICT", "PRE_INTERVIEW_ANXIETY", "GENERAL_OVERWHELM"]:
            threshold = self.emotional_silence_threshold
        elif not self.is_sentence_complete(text):
            threshold = self.disfluency_silence_threshold

        if silence_duration >= threshold:
            return TurnStatus.TURN_COMPLETE
        else:
            return TurnStatus.LISTENING
