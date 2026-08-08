"""
__init__.py for src/guardrails/

Exposes the three guardrail functions as clean imports for pipeline.py.
"""

from .out_of_scope import is_out_of_scope
from .scam_detection import check_scam, SCAM_INSTRUCTION_BLOCK
from .legal_boundary import check_legal_boundary

__all__ = [
    "is_out_of_scope",
    "check_scam",
    "check_legal_boundary",
    "SCAM_INSTRUCTION_BLOCK",
]
