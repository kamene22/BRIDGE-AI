"""
src/memory/memory.py — Session Memory, Conversation Store & Profile Builder

Implements:
  1. UUID Session Management & In-Memory Store (`create_session`, `add_message`, `get_conversation_history`)
  2. History Formatting for Prompts (`format_history_for_prompt`)
  3. Sliding Window & Profile Extractor (`ConversationMemory`, `UserProfile`)
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


# ── Global In-Memory Conversation Store ───────────────────────────────────────
conversations: Dict[str, List[Dict[str, Any]]] = {}


def create_session() -> str:
    """Creates a new unique conversation session ID."""
    session_id = str(uuid.uuid4())
    conversations[session_id] = []
    return session_id


def clear_session_history(session_id: str) -> None:
    """Clears conversation history for a session."""
    conversations[session_id] = []


def add_message(session_id: str, role: str, content: str) -> None:
    """Adds a message to the conversation history for a session."""
    if session_id not in conversations:
        conversations[session_id] = []

    conversations[session_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    })


def get_conversation_history(session_id: str, max_messages: Optional[int] = 15) -> List[Dict[str, Any]]:
    """Gets recent conversation history for a session."""
    if session_id not in conversations:
        return []

    history = conversations[session_id]
    if max_messages:
        history = history[-max_messages:]

    return history


def format_history_for_prompt(session_id: str, max_messages: int = 4) -> str:
    """Formats recent conversation history (sliding window of last 4 messages) as a clean string for prompt context."""
    history = get_conversation_history(session_id, max_messages)
    if not history:
        return "None."

    formatted_history = []
    for msg in history:
        role_label = "Human" if msg["role"] == "user" else "Assistant"
        formatted_history.append(f"{role_label}: {msg['content']}")

    return "\n\n".join(formatted_history)


# ── Structured Memory Data Structures ─────────────────────────────────────────

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
    """
    career_stage: Optional[str] = None
    employer_type: Optional[str] = None
    current_concern: Optional[str] = None
    location: Optional[str] = None
    extra_context: list[str] = field(default_factory=list)

    def to_string(self) -> str:
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


class ConversationMemory:
    """
    Manages sliding window of turns and profile signals for a session.
    """
    def __init__(self, window_size: int = 15):
        self.window_size = window_size
        self.turns: list[Turn] = []
        self.profile = UserProfile()

    @property
    def turn_count(self) -> int:
        return len(self.turns)

    def add_turn(
        self,
        user_message: str,
        assistant_response: str,
        guardrails_triggered: list[str] = None
    ) -> None:
        turn = Turn(
            user_message=user_message,
            assistant_response=assistant_response,
            guardrails_triggered=guardrails_triggered or []
        )
        self.turns.append(turn)

        if len(self.turns) > self.window_size:
            self.turns = self.turns[-self.window_size:]

        self._extract_profile_signals(user_message)

    def clear(self) -> None:
        self.turns = []
        self.profile = UserProfile()

    def get_full_memory_block(self) -> str:
        if not self.turns and self.profile.is_empty():
            return ""

        blocks = []
        if not self.profile.is_empty():
            blocks.append(f"USER PROFILE (Established Facts):\n{self.profile.to_string()}")

        if self.turns:
            history_lines = []
            for idx, turn in enumerate(self.turns, 1):
                history_lines.append(f"Turn {idx}:")
                history_lines.append(f"  User: {turn.user_message}")
                history_lines.append(f"  Amani: {turn.assistant_response}")
            blocks.append("RECENT CONVERSATION HISTORY:\n" + "\n".join(history_lines))

        return "\n\n".join(blocks)

    def _extract_profile_signals(self, message: str) -> None:
        msg_lower = message.lower()
        if any(kw in msg_lower for kw in ["just graduated", "fresh graduate", "just finished uni", "fresh from campus", "first job"]):
            self.profile.career_stage = "fresh graduate"
        elif any(kw in msg_lower for kw in ["6 months", "six months", "been working for"]):
            self.profile.career_stage = "6+ months in first role"

        if any(kw in msg_lower for kw in ["ngo", "non-profit", "non profit"]):
            self.profile.employer_type = "NGO"
        elif any(kw in msg_lower for kw in ["bank", "banking", "finance"]):
            self.profile.employer_type = "Bank/Finance"
        elif any(kw in msg_lower for kw in ["tech company", "startup", "software firm"]):
            self.profile.employer_type = "Tech Startup"

        if any(kw in msg_lower for kw in ["nairobi", "mombasa", "kisumu", "nakuru", "eldoret"]):
            for loc in ["nairobi", "mombasa", "kisumu", "nakuru", "eldoret"]:
                if loc in msg_lower:
                    self.profile.location = loc.capitalize()
