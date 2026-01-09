"""
AI-Powered Prompt Optimizer - Analyze and improve prompts using LLMs.
Feature #1: AI-Powered Prompt Optimizer
"""

from dataclasses import dataclass
from typing import Optional
from llm_client import LLMClient, LLMResponse


@dataclass
class OptimizationResult:
    original_prompt: str
    optimized_prompt: str
    suggestions: list[str]
    clarity_score: int  # 1-10
    specificity_score: int  # 1-10
    effectiveness_score: int  # 1-10
    explanation: str
    error: Optional[str] = None


OPTIMIZER_SYSTEM_PROMPT = """You are an expert prompt engineer. Your task is to analyze and optimize prompts for LLM interactions.

When given a prompt, you will:
1. Analyze its clarity, specificity, and potential effectiveness
2. Identify areas for improvement
3. Provide an optimized version
4. Give specific suggestions

Respond in this exact JSON format:
{
    "optimized_prompt": "The improved version of the prompt",
    "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"],
    "clarity_score": 7,
    "specificity_score": 8,
    "effectiveness_score": 7,
    "explanation": "Brief explanation of changes made and why"
}

Scores are 1-10 where 10 is best. Be constructive and specific in suggestions."""


class PromptOptimizer:
    """Analyze and optimize prompts using AI."""

    def __init__(self, llm_client: LLMClient = None):
        self.client = llm_client or LLMClient()

    async def optimize(
        self,
        prompt: str,
        context: str = None,
        provider: str = None,
        model: str = None
    ) -> OptimizationResult:
        """Analyze and optimize a prompt."""
        
        user_prompt = f"Analyze and optimize this prompt:\n\n{prompt}"
        if context:
            user_prompt += f"\n\nContext for the prompt: {context}"

        response = await self.client.complete(
            prompt=user_prompt,
            provider=provider,
            model=model,
            system_prompt=OPTIMIZER_SYSTEM_PROMPT,
            temperature=0.3
        )

        if response.error:
            return OptimizationResult(
                original_prompt=prompt,
                optimized_prompt=prompt,
                suggestions=[],
                clarity_score=0,
                specificity_score=0,
                effectiveness_score=0,
                explanation="",
                error=response.error
            )

        # Parse response
        try:
            import json
            # Try to extract JSON from response
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content.strip())
            
            return OptimizationResult(
                original_prompt=prompt,
                optimized_prompt=data.get("optimized_prompt", prompt),
                suggestions=data.get("suggestions", []),
                clarity_score=data.get("clarity_score", 5),
                specificity_score=data.get("specificity_score", 5),
                effectiveness_score=data.get("effectiveness_score", 5),
                explanation=data.get("explanation", "")
            )
        except Exception as e:
            # If parsing fails, return the raw response as explanation
            return OptimizationResult(
                original_prompt=prompt,
                optimized_prompt=prompt,
                suggestions=["Could not parse optimization suggestions"],
                clarity_score=5,
                specificity_score=5,
                effectiveness_score=5,
                explanation=response.content,
                error=f"Parse error: {str(e)}"
            )

    async def quick_suggestions(
        self,
        prompt: str,
        provider: str = None,
        model: str = None
    ) -> list[str]:
        """Get quick improvement suggestions without full optimization."""
        
        response = await self.client.complete(
            prompt=f"Give 3 brief suggestions to improve this prompt (one line each):\n\n{prompt}",
            provider=provider,
            model=model,
            system_prompt="You are a prompt engineering expert. Give concise, actionable suggestions.",
            max_tokens=500,
            temperature=0.3
        )

        if response.error:
            return [f"Error: {response.error}"]

        # Parse suggestions
        lines = [line.strip() for line in response.content.split("\n") if line.strip()]
        suggestions = []
        for line in lines:
            # Remove numbering
            if line[0].isdigit() and (line[1] == '.' or line[1] == ')'):
                line = line[2:].strip()
            if line.startswith('-'):
                line = line[1:].strip()
            if line:
                suggestions.append(line)
        
        return suggestions[:5]  # Max 5 suggestions
