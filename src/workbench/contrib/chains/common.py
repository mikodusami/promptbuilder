"""
Chains feature - common types.
"""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class ChainStep:
    name: str
    prompt_template: str
    provider: str = None
    model: str = None
    system_prompt: str = None
    output_key: str = None
    transform: str = None
    condition: str = None
    max_tokens: int = 4096
    temperature: float = 0.7


@dataclass
class PromptChain:
    name: str
    description: str
    steps: list[ChainStep]
    initial_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChainResult:
    success: bool
    steps_completed: int
    total_steps: int
    outputs: dict[str, str]
    final_output: str
    errors: list[str]
    total_tokens: int
    total_latency_ms: int
    timestamp: str
