"""
Optimizer feature - common types.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class OptimizationResult:
    original_prompt: str
    optimized_prompt: str
    suggestions: list[str]
    clarity_score: int
    specificity_score: int
    effectiveness_score: int
    explanation: str
    error: Optional[str] = None
