"""
Natural Language Prompt Generation - Generate prompts from plain English descriptions.
Feature #9: Natural Language Prompt Generation
"""

from dataclasses import dataclass
from typing import Optional
from llm_client import LLMClient


@dataclass
class GeneratedPrompt:
    description: str
    technique: str
    prompt: str
    explanation: str
    confidence: float
    alternatives: list[str]
    error: Optional[str] = None


GENERATOR_SYSTEM_PROMPT = """You are an expert prompt engineer. Given a plain English description of what the user wants to accomplish, generate an optimal prompt using the best prompt engineering technique.

Available techniques:
1. Chain of Thought (cot) - For complex reasoning, math, logic problems
2. Few-Shot Learning (few_shot) - When examples would help clarify the pattern
3. Role-Based (role) - When domain expertise is needed
4. Structured Output (structured) - When specific format is required
5. ReAct (react) - For multi-step tasks requiring reasoning and actions
6. Tree of Thoughts (tot) - For problems with multiple solution paths
7. Self-Consistency (self_consistency) - When verification is important

Respond in this exact JSON format:
{
    "technique": "the_technique_key",
    "prompt": "The complete, ready-to-use prompt",
    "explanation": "Brief explanation of why this technique was chosen",
    "confidence": 0.85,
    "alternatives": ["Alternative prompt 1", "Alternative prompt 2"]
}

Generate prompts that are:
- Clear and specific
- Well-structured
- Appropriate for the task complexity
- Ready to use immediately"""


class NaturalLanguageGenerator:
    """Generate prompts from natural language descriptions."""

    def __init__(self, llm_client: LLMClient = None):
        self.client = llm_client or LLMClient()

    async def generate(
        self,
        description: str,
        context: str = None,
        preferred_technique: str = None,
        provider: str = None,
        model: str = None
    ) -> GeneratedPrompt:
        """Generate a prompt from a natural language description."""
        
        user_prompt = f"Generate an optimal prompt for this task:\n\n{description}"
        
        if context:
            user_prompt += f"\n\nAdditional context: {context}"
        
        if preferred_technique:
            user_prompt += f"\n\nPreferred technique: {preferred_technique}"

        response = await self.client.complete(
            prompt=user_prompt,
            provider=provider,
            model=model,
            system_prompt=GENERATOR_SYSTEM_PROMPT,
            temperature=0.5
        )

        if response.error:
            return GeneratedPrompt(
                description=description,
                technique="",
                prompt="",
                explanation="",
                confidence=0,
                alternatives=[],
                error=response.error
            )

        # Parse response
        try:
            import json
            content = response.content
            
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content.strip())
            
            return GeneratedPrompt(
                description=description,
                technique=data.get("technique", ""),
                prompt=data.get("prompt", ""),
                explanation=data.get("explanation", ""),
                confidence=data.get("confidence", 0.5),
                alternatives=data.get("alternatives", [])
            )
        except Exception as e:
            # If parsing fails, try to extract the prompt from raw response
            return GeneratedPrompt(
                description=description,
                technique="unknown",
                prompt=response.content,
                explanation="Could not parse structured response",
                confidence=0.3,
                alternatives=[],
                error=f"Parse error: {str(e)}"
            )

    async def suggest_technique(
        self,
        description: str,
        provider: str = None,
        model: str = None
    ) -> tuple[str, str]:
        """Suggest the best technique for a task description."""
        
        response = await self.client.complete(
            prompt=f"""For this task, which prompt engineering technique would be most effective?

Task: {description}

Respond with just the technique name and a one-sentence reason.
Options: Chain of Thought, Few-Shot Learning, Role-Based, Structured Output, ReAct, Tree of Thoughts, Self-Consistency""",
            provider=provider,
            model=model,
            max_tokens=200,
            temperature=0.3
        )

        if response.error:
            return "role", "Default to role-based for general tasks"

        # Parse simple response
        content = response.content.strip()
        
        technique_map = {
            "chain of thought": "cot",
            "few-shot": "few_shot",
            "few shot": "few_shot",
            "role-based": "role",
            "role based": "role",
            "structured": "structured",
            "react": "react",
            "tree of thoughts": "tot",
            "self-consistency": "self_consistency",
            "self consistency": "self_consistency"
        }
        
        for name, key in technique_map.items():
            if name in content.lower():
                return key, content
        
        return "role", content

    async def improve_description(
        self,
        description: str,
        provider: str = None,
        model: str = None
    ) -> str:
        """Improve a vague task description to be more specific."""
        
        response = await self.client.complete(
            prompt=f"""Make this task description more specific and actionable for prompt generation.
Keep it concise but add necessary details.

Original: {description}

Improved description:""",
            provider=provider,
            model=model,
            max_tokens=300,
            temperature=0.5
        )

        if response.error:
            return description

        return response.content.strip()

    async def batch_generate(
        self,
        descriptions: list[str],
        provider: str = None,
        model: str = None
    ) -> list[GeneratedPrompt]:
        """Generate prompts for multiple descriptions."""
        import asyncio
        
        tasks = [
            self.generate(desc, provider=provider, model=model)
            for desc in descriptions
        ]
        
        return await asyncio.gather(*tasks)
