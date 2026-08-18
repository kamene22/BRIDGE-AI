"""
response_planner.py — Response Planner Engine for Hybrid Reasoning Architecture
Maps Classified Intents into structured Response Plans that define tone, reasoning parameters,
output templates, and guardrail constraints for Gemini 2.5 Flash generation.
"""

from typing import Dict, Any, List
try:
    from intent.intent_classifier import IntentCategory
except ModuleNotFoundError:
    from src.intent.intent_classifier import IntentCategory


class ResponsePlan:
    """Encapsulates the structured execution plan for a specific user intent."""

    def __init__(
        self,
        intent: IntentCategory,
        structure: List[str],
        reasoning_mode: str,
        empathy_level: str,
        requires_followup: bool,
        guardrail_rules: List[str],
        max_tokens: int = 600,
    ):
        self.intent = intent
        self.structure = structure
        self.reasoning_mode = reasoning_mode
        self.empathy_level = empathy_level
        self.requires_followup = requires_followup
        self.guardrail_rules = guardrail_rules
        self.max_tokens = max_tokens

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent.value,
            "structure": self.structure,
            "reasoning_mode": self.reasoning_mode,
            "empathy_level": self.empathy_level,
            "requires_followup": self.requires_followup,
            "guardrail_rules": self.guardrail_rules,
            "max_tokens": self.max_tokens,
        }


class ResponsePlanner:
    """Generates customized ResponsePlan instances tailored to classified user intents."""

    def extract_arguments(self, query: str) -> Dict[str, Any]:
        """
        REAPER Argument & Entity Extractor (CIKM '24)
        Extracts structured entities from informal situational queries to enable precise adaptation.
        """
        q_lower = query.lower().strip()

        # Core Scenario Detection
        scenario = "general_mentorship"
        if any(k in q_lower for k in ["probation", "trial period", "extend"]):
            scenario = "probation_rights"
        elif any(k in q_lower for k in ["email", "sent email", "wrong person", "mistake"]):
            scenario = "email_mistake_apology"
        elif any(k in q_lower for k in ["scam", "fee", "mpesa", "deposit", "uniform"]):
            scenario = "scam_prevention"
        elif any(k in q_lower for k in ["wear", "dress code", "clothes", "outfit", "in person"]):
            scenario = "first_day_prep"
        elif any(k in q_lower for k in ["manager", "boss", "talks to me", "ignores me"]):
            scenario = "manager_relationship"

        # Workplace Setting
        setting = "in_person"
        if "remote" in q_lower or "online" in q_lower:
            setting = "remote"
        elif "hybrid" in q_lower:
            setting = "hybrid"

        # Emotional Register
        emotion = "curious"
        if any(k in q_lower for k in ["😭", "scared", "terrified", "anxious", "worried", "mistake"]):
            emotion = "anxious"
        elif any(k in q_lower for k in ["excited", "got my first job", "landed"]):
            emotion = "enthusiastic"

        return {
            "core_scenario": scenario,
            "workplace_setting": setting,
            "emotional_register": emotion
        }

    def create_plan(self, intent: IntentCategory) -> ResponsePlan:
        if intent == IntentCategory.KNOWLEDGE:
            return ResponsePlan(
                intent=intent,
                structure=["Answer directly", "One practical tip"],
                reasoning_mode="strict_grounded",
                empathy_level="neutral_professional",
                requires_followup=False,
                guardrail_rules=[
                    "Stay 100% grounded in retrieved knowledge.",
                    "Do not speculate or add unverified assumptions.",
                    "Provide a direct answer immediately."
                ],
                max_tokens=1000
            )

        elif intent == IntentCategory.PROCEDURAL:
            return ResponsePlan(
                intent=intent,
                structure=["Brief explanation", "Step-by-step guidance", "Actionable recommendation"],
                reasoning_mode="workflow_extraction",
                empathy_level="encouraging_mentor",
                requires_followup=True,
                guardrail_rules=[
                    "Convert handbook principles into clear numbered or bulleted steps.",
                    "Keep steps concise and actionable for early career graduates.",
                    "Ensure steps match Kenyan workplace norms."
                ],
                max_tokens=800
            )

        elif intent == IntentCategory.SITUATIONAL:
            return ResponsePlan(
                intent=intent,
                structure=[
                    "Analyze conversation continuity (answering previous question vs new topic)",
                    "Acknowledge user context naturally",
                    "Reason through positive-intent perspectives (workloads, priorities)",
                    "Practical advice / next step",
                    "Contextual follow-up question (if natural)"
                ],
                reasoning_mode="mentorship_reasoning",
                empathy_level="calm_empathic",
                requires_followup=True,
                guardrail_rules=[
                    "Check if the user is answering a question previously asked by Amani. If so, do NOT restart—continue the topic thread.",
                    "NEVER assume negative intent, hostility, or malice from managers or colleagues.",
                    "Always frame explanations around busy schedules, competing priorities, or communication styles.",
                    "Do NOT introduce yourself unless greeted.",
                    "Do NOT force a follow-up question if the user is saying thank you or concluding.",
                    "NEVER invent company HR policies, legal advice, or disciplinary procedures."
                ],
                max_tokens=500
            )

        elif intent == IntentCategory.REFLECTIVE:
            return ResponsePlan(
                intent=intent,
                structure=[
                    "Acknowledge & validate feeling",
                    "Explore underlying experience",
                    "Reason through constructive reframing",
                    "Gentle practical guidance",
                    "One open-ended reflective question"
                ],
                reasoning_mode="reflective_coaching",
                empathy_level="warm_validating",
                requires_followup=True,
                guardrail_rules=[
                    "Do NOT introduce yourself unless greeted.",
                    "Do NOT assume career stage unless user explicitly stated it.",
                    "Do NOT jump immediately to fixing or solving—explore first.",
                    "Validate the user's feelings and experience naturally.",
                    "Ask one thoughtful, open-ended question to help the user unpack their thoughts."
                ],
                max_tokens=400
            )

        elif intent == IntentCategory.LEGAL:
            return ResponsePlan(
                intent=intent,
                structure=["Grounded explanation", "Clarify legal uncertainty", "Recommended next step"],
                reasoning_mode="strict_statutory",
                empathy_level="calm_reassuring",
                requires_followup=True,
                guardrail_rules=[
                    "Remain 100% grounded in the Employment Act corpus.",
                    "Do not speculate on legal outcomes or guarantee court decisions.",
                    "If corpus does not contain the answer, explicitly state legal uncertainty.",
                    "Recommend consulting official HR or Labour Office if appropriate."
                ],
                max_tokens=550
            )

        else: # SCAM / CONVERSATIONAL
            return ResponsePlan(
                intent=intent,
                structure=["Scam warning block", "Red flag checklist", "Safety action"],
                reasoning_mode="scam_alert",
                empathy_level="protective_alert",
                requires_followup=True,
                guardrail_rules=[
                    "Issue an immediate clear warning against paying any recruitment or medical fees.",
                    "State clearly that legitimate Kenyan employers do not charge job seekers.",
                    "Advise user not to send money via M-Pesa or unverified paybills."
                ],
                max_tokens=450
            )
