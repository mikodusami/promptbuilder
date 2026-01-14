"""
Optimizer feature - AI-powered prompt optimization service.
"""

import json
from src.services.llm import LLMClient
from .common import OptimizationResult


OPTIMIZER_SYSTEM_PROMPT = """You are an expert prompt engineer. Analyze and optimize prompts for LLM interactions.

Respond in this exact JSON format:
{
    "optimized_prompt": "The improved version of the prompt",
    "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"],
    "clarity_score": 7,
    "specificity_score": 8,
    "effectiveness_score": 7,
    "explanation": "Brief explanation of changes made"
}

Scores are 1-10 where 10 is best."""


class OptimizerService:
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
            user_prompt += f"\n\nContext: {context}"

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

        try:
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
            return OptimizationResult(
                original_prompt=prompt,
                optimized_prompt=prompt,
                suggestions=[],
                clarity_score=5,
                specificity_score=5,
                effectiveness_score=5,
                explanation=response.content,
                error=f"Parse error: {str(e)}"
            )
