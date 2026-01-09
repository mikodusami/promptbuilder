"""
Configuration dataclasses for prompt building.
"""

from dataclasses import dataclass, field


@dataclass
class PromptConfig:
    """Configuration for building a prompt."""
    task: str
    context: str = ""
    examples: list[dict] = field(default_factory=list)
    role: str = ""
    output_format: str = ""
    constraints: list[str] = field(default_factory=list)
    temperature_hint: str = "balanced"
