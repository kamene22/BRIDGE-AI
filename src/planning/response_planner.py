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
    ):
        self.intent = intent
        self.structure = structure
        self.reasoning_mode = reasoning_mode
        self.empathy_level = empathy_level
        self.requires_followup = requires_followup
        self.guardrail_rules = guardrail_rules

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent.value,
            "structure": self.structure,
            "reasoning_mode": self.reasoning_mode,
            "empathy_level": self.empathy_level,
            "requires_followup": self.requires_followup,
            "guardrail_rules": self.guardrail_rules,
        }


class ResponsePlanner:
    """Generates customized ResponsePlan instances tailored to classified user intents."""

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
                ]
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
                ]
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
                ]
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
                ]
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
                ]
            )

        else: # SCAM
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
                ]
            )
