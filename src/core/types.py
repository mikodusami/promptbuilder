"""
Core types and enumerations.
"""

from enum import Enum


class PromptType(Enum):
    """Available prompt engineering techniques."""
    CHAIN_OF_THOUGHT = "cot"
    FEW_SHOT = "few_shot"
    ROLE_BASED = "role"
    STRUCTURED = "structured"
    REACT = "react"
    TREE_OF_THOUGHTS = "tot"
    SELF_CONSISTENCY = "self_consistency"


# Technique metadata for UI display
TECHNIQUE_METADATA = {
    PromptType.CHAIN_OF_THOUGHT: {
        "name": "Chain of Thought",
        "icon": "🧠",
        "color": "cyan",
        "description": "Step-by-step reasoning for complex problems"
    },
    PromptType.FEW_SHOT: {
        "name": "Few-Shot Learning",
        "icon": "📚",
        "color": "green",
        "description": "Learn patterns from examples you provide"
    },
    PromptType.ROLE_BASED: {
        "name": "Role-Based",
        "icon": "🎭",
        "color": "magenta",
        "description": "Assign expert persona for domain-specific tasks"
    },
    PromptType.STRUCTURED: {
        "name": "Structured Output",
        "icon": "📋",
        "color": "yellow",
        "description": "Get responses in specific formats (JSON, etc.)"
    },
    PromptType.REACT: {
        "name": "ReAct",
        "icon": "⚡",
        "color": "red",
        "description": "Reasoning + Acting for multi-step problem solving"
    },
    PromptType.TREE_OF_THOUGHTS: {
        "name": "Tree of Thoughts",
        "icon": "🌳",
        "color": "blue",
        "description": "Explore multiple solution paths systematically"
    },
    PromptType.SELF_CONSISTENCY: {
        "name": "Self-Consistency",
        "icon": "🔄",
        "color": "white",
        "description": "Multiple solutions for verification & consensus"
    },
}
