"""
memory.py — Session Memory & User Profile Builder (Phase 6)

Design principles from the design document:
  "Memory and knowledge are pulled at the same retrieval step but kept
  conceptually separate. The corpus is the ONLY thing the model is allowed
  to treat as a source of fact — memory shapes tone and relevance, never
  supplies new information the model didn't already have grounded elsewhere."

Two components:
  1. ConversationMemory: Sliding window of the last N turns (default 5).
     Formatted into a compact context string injected into the prompt.
  2. UserProfile: Lightweight key-value store of facts the user has
     explicitly stated in the conversation (career stage, employer type,
     location, stated concerns). Shapes relevance without adding new facts.
"""

from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Turn:
    """A single conversational exchange."""
    user_message: str
    assistant_response: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    guardrails_triggered: list[str] = field(default_factory=list)


@dataclass
class UserProfile:
    """
    Lightweight profile of facts the user has explicitly stated.
    Only populated from what the user directly says — never inferred.

    Design doc: "memory shapes tone and relevance, never supplies new
    information the model didn't already have grounded elsewhere."
    """
    career_stage: Optional[str] = None        # e.g. "fresh graduate", "6 months in"
    employer_type: Optional[str] = None       # e.g. "NGO", "bank", "startup", "government"
    current_concern: Optional[str] = None     # e.g. "probation ending", "scam worry"
    location: Optional[str] = None            # e.g. "Nairobi", "Mombasa"
    extra_context: list[str] = field(default_factory=list)  # Other stated facts

    def to_string(self) -> str:
        """Returns a compact string summary of the user profile for prompt injection."""
        parts = []
        if self.career_stage:
            parts.append(f"Career stage: {self.career_stage}")
        if self.employer_type:
            parts.append(f"Employer type: {self.employer_type}")
        if self.current_concern:
            parts.append(f"Current concern: {self.current_concern}")
        if self.location:
            parts.append(f"Location: {self.location}")
        for ctx in self.extra_context:
            parts.append(ctx)
        return " | ".join(parts) if parts else "No profile context captured yet."

    def is_empty(self) -> bool:
        return not any([
            self.career_stage, self.employer_type,
            self.current_concern, self.location,
            self.extra_context
        ])


# ─────────────────────────────────────────────────────────────────────────────
# Conversation Memory Manager
# ─────────────────────────────────────────────────────────────────────────────

class ConversationMemory:
    """
    Manages a sliding window of the last N conversation turns.

    The window is the only memory mechanism — there is no persistent storage
    between sessions in this PoC. Each session starts fresh.

    Design doc: "sliding window history handler" — keeps enough context for
    coherent multi-turn conversation without ballooning the prompt size.
    """

    def __init__(self, window_size: int = 5):
        """
        Args:
            window_size: Maximum number of past turns to retain.
                         Design doc specifies 5 as the starting parameter.
        """
        self.window_size = window_size
        self.turns: list[Turn] = []
        self.profile = UserProfile()

    def add_turn(
        self,
        user_message: str,
        assistant_response: str,
        guardrails_triggered: list[str] = None
    ) -> None:
        """
        Records a completed exchange and maintains the sliding window.
        Automatically extracts profile signals from the user message.
        """
        turn = Turn(
            user_message=user_message,
            assistant_response=assistant_response,
            guardrails_triggered=guardrails_triggered or []
        )
        self.turns.append(turn)

        # Trim to window size — oldest turns dropped first
        if len(self.turns) > self.window_size:
            self.turns = self.turns[-self.window_size:]

        # Update user profile from the message
        self._extract_profile_signals(user_message)

    def _extract_profile_signals(self, message: str) -> None:
        """
        Rule-based extraction of explicit profile signals from user messages.
        Only records what is clearly stated — no inference or assumption.

        Design doc: "memory shapes tone and relevance, never supplies
        new information the model didn't already have grounded elsewhere."
        """
        msg_lower = message.lower()

        # Career stage signals
        if any(kw in msg_lower for kw in ["just graduated", "fresh graduate", "just finished uni",
                                           "fresh from campus", "first job", "recently graduated"]):
            self.profile.career_stage = "fresh graduate"
        elif any(kw in msg_lower for kw in ["6 months", "six months", "been working for"]):
            self.profile.career_stage = "6+ months in first role"
        elif any(kw in msg_lower for kw in ["still in uni", "final year", "still studying",
                                              "fourth year", "3rd year"]):
            self.profile.career_stage = "still in university"

        # Employer type signals
        if any(kw in msg_lower for kw in ["ngo", "non-profit", "nonprofit", "charity"]):
            self.profile.employer_type = "NGO/non-profit"
        elif any(kw in msg_lower for kw in ["bank", "co-operative", "sacco", "microfinance"]):
            self.profile.employer_type = "banking/finance"
        elif any(kw in msg_lower for kw in ["startup", "tech company", "fintech"]):
            self.profile.employer_type = "startup/tech"
        elif any(kw in msg_lower for kw in ["government", "county", "civil service", "public service"]):
            self.profile.employer_type = "government/public sector"

        # Location signals
        for city in ["nairobi", "mombasa", "kisumu", "nakuru", "eldoret", "thika"]:
            if city in msg_lower:
                self.profile.location = city.capitalize()
                break

        # Concern signals
        if any(kw in msg_lower for kw in ["probation ending", "end of probation",
                                            "probation is almost", "probation period is"]):
            self.profile.current_concern = "probation period"
        elif any(kw in msg_lower for kw in ["pay me", "upfront", "deposit", "uniform fee",
                                              "registration fee", "seems like a scam"]):
            self.profile.current_concern = "potential job scam"

    def format_for_prompt(self) -> str:
        """
        Formats recent conversation history into a compact block for prompt injection.

        Returns an empty string if there are no prior turns (first message in session).
        Memory context is injected between the system prompt and the retrieved corpus
        chunks — it shapes relevance but is never treated as a source of fact.
        """
        if not self.turns:
            return ""

        lines = ["CONVERSATION HISTORY (for context only — not a source of facts):"]
        lines.append("-" * 50)

        for i, turn in enumerate(self.turns, 1):
            lines.append(f"[Turn {i}]")
            lines.append(f"User: {turn.user_message.strip()}")
            # Truncate long assistant responses to keep prompt size manageable
            response_preview = turn.assistant_response.strip()
            if len(response_preview) > 300:
                response_preview = response_preview[:297] + "..."
            lines.append(f"Bridge AI: {response_preview}")
            lines.append("")

        lines.append("-" * 50)
        return "\n".join(lines)

    def format_profile_for_prompt(self) -> str:
        """Returns the user profile summary string for prompt injection."""
        if self.profile.is_empty():
            return ""
        return f"USER CONTEXT (explicitly stated): {self.profile.to_string()}"

    def get_full_memory_block(self) -> str:
        """
        Returns the complete memory block to inject into the prompt.
        Combines profile summary + conversation history.
        Empty string if this is the first turn in a session.
        """
        parts = []
        profile_str = self.format_profile_for_prompt()
        history_str = self.format_for_prompt()

        if profile_str:
            parts.append(profile_str)
        if history_str:
            parts.append(history_str)

        return "\n\n".join(parts) if parts else ""

    @property
    def turn_count(self) -> int:
        return len(self.turns)

    def clear(self) -> None:
        """Resets the session — called when a new conversation starts."""
        self.turns = []
        self.profile = UserProfile()
