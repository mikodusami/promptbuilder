"""
Chains feature - service for executing prompt chains.
"""

import json
import re
from datetime import datetime
from typing import Any, Callable, Optional
from pathlib import Path

from src.platform.environment import get_config_dir
from src.services.llm import LLMClient
from .common import ChainStep, PromptChain, ChainResult


class ChainService:
    """Execute multi-step prompt chains."""

    def __init__(self, llm_client: LLMClient = None):
        self.client = llm_client or LLMClient()
        self.chains: dict[str, PromptChain] = {}
        self._load_chains()

    def _load_chains(self) -> None:
        config_path = get_config_dir() / "chains.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    data = json.load(f)
                for name, chain_data in data.items():
                    steps = [ChainStep(**s) for s in chain_data.get("steps", [])]
                    self.chains[name] = PromptChain(
                        name=name,
                        description=chain_data.get("description", ""),
                        steps=steps,
                        initial_context=chain_data.get("initial_context", {})
                    )
            except Exception:
                pass

    def save_chains(self):
        config_path = get_config_dir() / "chains.json"
        data = {}
        for name, chain in self.chains.items():
            data[name] = {
                "description": chain.description,
                "steps": [
                    {
                        "name": s.name,
                        "prompt_template": s.prompt_template,
                        "output_key": s.output_key,
                        "transform": s.transform,
                    }
                    for s in chain.steps
                ]
            }
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _interpolate(self, template: str, context: dict[str, Any]) -> str:
        result = template
        for key, value in context.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    async def execute(
        self,
        chain: PromptChain,
        input_context: dict[str, Any] = None,
    ) -> ChainResult:
        """Execute a prompt chain."""
        
        context = {**chain.initial_context, **(input_context or {})}
        outputs = {}
        errors = []
        total_tokens = 0
        total_latency = 0
        steps_completed = 0

        for i, step in enumerate(chain.steps):
            try:
                prompt = self._interpolate(step.prompt_template, context)
                system = self._interpolate(step.system_prompt, context) if step.system_prompt else None

                start = datetime.now()
                response = await self.client.complete(
                    prompt=prompt, provider=step.provider, model=step.model,
                    system_prompt=system, max_tokens=step.max_tokens, temperature=step.temperature
                )
                latency = int((datetime.now() - start).total_seconds() * 1000)
                total_latency += latency

                if response.error:
                    errors.append(f"Step {step.name}: {response.error}")
                    break

                total_tokens += response.input_tokens + response.output_tokens
                output_key = step.output_key or f"step_{i}_output"
                context[output_key] = response.content
                outputs[step.name] = response.content
                steps_completed += 1

            except Exception as e:
                errors.append(f"Step {step.name}: {str(e)}")
                break

        return ChainResult(
            success=len(errors) == 0 and steps_completed == len(chain.steps),
            steps_completed=steps_completed,
            total_steps=len(chain.steps),
            outputs=outputs,
            final_output=list(outputs.values())[-1] if outputs else "",
            errors=errors,
            total_tokens=total_tokens,
            total_latency_ms=total_latency,
            timestamp=datetime.now().isoformat()
        )

    def create_chain(self, name: str, description: str, steps: list[ChainStep]) -> PromptChain:
        chain = PromptChain(name=name, description=description, steps=steps)
        self.chains[name] = chain
        self.save_chains()
        return chain

    def get_chain(self, name: str) -> Optional[PromptChain]:
        return self.chains.get(name)

    def list_chains(self) -> list[PromptChain]:
        return list(self.chains.values())
