"""
Prompt Chains & Workflows - Multi-step prompt pipelines.
Feature #5: Prompt Chains & Workflows
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Callable
from datetime import datetime
import asyncio
import json
from pathlib import Path

from llm_client import LLMClient, LLMResponse


@dataclass
class ChainStep:
    name: str
    prompt_template: str
    provider: str = None  # None = use default
    model: str = None
    system_prompt: str = None
    output_key: str = None  # Key to store output in context
    transform: str = None  # "json", "lines", "first_line", None
    condition: str = None  # Simple condition like "len(output) > 100"
    max_tokens: int = 4096
    temperature: float = 0.7


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


@dataclass
class PromptChain:
    name: str
    description: str
    steps: list[ChainStep]
    initial_context: dict[str, Any] = field(default_factory=dict)


class ChainExecutor:
    """Execute multi-step prompt chains."""

    def __init__(self, llm_client: LLMClient = None):
        self.client = llm_client or LLMClient()
        self.chains: dict[str, PromptChain] = {}
        self._load_chains()

    def _load_chains(self):
        """Load saved chains from config."""
        config_path = Path.home() / ".promptbuilder" / "chains.json"
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
        """Save chains to config."""
        config_path = Path.home() / ".promptbuilder" / "chains.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {}
        for name, chain in self.chains.items():
            data[name] = {
                "description": chain.description,
                "steps": [
                    {
                        "name": s.name,
                        "prompt_template": s.prompt_template,
                        "provider": s.provider,
                        "model": s.model,
                        "system_prompt": s.system_prompt,
                        "output_key": s.output_key,
                        "transform": s.transform,
                        "condition": s.condition,
                        "max_tokens": s.max_tokens,
                        "temperature": s.temperature
                    }
                    for s in chain.steps
                ],
                "initial_context": chain.initial_context
            }
        
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _interpolate(self, template: str, context: dict[str, Any]) -> str:
        """Simple variable interpolation."""
        result = template
        for key, value in context.items():
            result = result.replace(f"{{{key}}}", str(value))
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result

    def _transform_output(self, output: str, transform: str) -> Any:
        """Transform output based on specified method."""
        if not transform:
            return output
        
        if transform == "json":
            try:
                # Try to extract JSON from response
                if "```json" in output:
                    output = output.split("```json")[1].split("```")[0]
                elif "```" in output:
                    output = output.split("```")[1].split("```")[0]
                return json.loads(output.strip())
            except:
                return output
        
        elif transform == "lines":
            return [line.strip() for line in output.split("\n") if line.strip()]
        
        elif transform == "first_line":
            lines = output.strip().split("\n")
            return lines[0] if lines else ""
        
        return output

    def _check_condition(self, condition: str, output: Any, context: dict) -> bool:
        """Check if condition is met."""
        if not condition:
            return True
        
        try:
            # Safe evaluation with limited scope
            local_vars = {"output": output, "context": context, "len": len}
            return eval(condition, {"__builtins__": {}}, local_vars)
        except:
            return True

    async def execute(
        self,
        chain: PromptChain,
        input_context: dict[str, Any] = None,
        on_step_complete: Callable[[str, str], None] = None
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
                # Interpolate prompt
                prompt = self._interpolate(step.prompt_template, context)
                system = self._interpolate(step.system_prompt, context) if step.system_prompt else None

                # Execute
                start = datetime.now()
                response = await self.client.complete(
                    prompt=prompt,
                    provider=step.provider,
                    model=step.model,
                    system_prompt=system,
                    max_tokens=step.max_tokens,
                    temperature=step.temperature
                )
                latency = int((datetime.now() - start).total_seconds() * 1000)
                total_latency += latency

                if response.error:
                    errors.append(f"Step {step.name}: {response.error}")
                    break

                total_tokens += response.input_tokens + response.output_tokens

                # Transform output
                output = self._transform_output(response.content, step.transform)

                # Check condition
                if not self._check_condition(step.condition, output, context):
                    errors.append(f"Step {step.name}: Condition not met")
                    break

                # Store output
                output_key = step.output_key or f"step_{i}_output"
                context[output_key] = output
                outputs[step.name] = response.content

                # Callback
                if on_step_complete:
                    on_step_complete(step.name, response.content)

                steps_completed += 1

            except Exception as e:
                errors.append(f"Step {step.name}: {str(e)}")
                break

        # Get final output
        final_output = ""
        if outputs:
            final_output = list(outputs.values())[-1]

        return ChainResult(
            success=len(errors) == 0 and steps_completed == len(chain.steps),
            steps_completed=steps_completed,
            total_steps=len(chain.steps),
            outputs=outputs,
            final_output=final_output,
            errors=errors,
            total_tokens=total_tokens,
            total_latency_ms=total_latency,
            timestamp=datetime.now().isoformat()
        )

    def create_chain(
        self,
        name: str,
        description: str,
        steps: list[ChainStep],
        initial_context: dict = None
    ) -> PromptChain:
        """Create and save a new chain."""
        chain = PromptChain(
            name=name,
            description=description,
            steps=steps,
            initial_context=initial_context or {}
        )
        self.chains[name] = chain
        self.save_chains()
        return chain

    def get_chain(self, name: str) -> Optional[PromptChain]:
        """Get a chain by name."""
        return self.chains.get(name)

    def list_chains(self) -> list[PromptChain]:
        """List all saved chains."""
        return list(self.chains.values())

    def delete_chain(self, name: str) -> bool:
        """Delete a chain."""
        if name in self.chains:
            del self.chains[name]
            self.save_chains()
            return True
        return False


# Pre-built chain templates
BUILTIN_CHAINS = {
    "research_and_summarize": PromptChain(
        name="research_and_summarize",
        description="Research a topic and create a summary",
        steps=[
            ChainStep(
                name="research",
                prompt_template="Research and list 5 key points about: {topic}",
                output_key="research_points"
            ),
            ChainStep(
                name="expand",
                prompt_template="Expand on these points with details:\n{research_points}",
                output_key="expanded"
            ),
            ChainStep(
                name="summarize",
                prompt_template="Create a concise summary from:\n{expanded}",
                output_key="summary"
            )
        ]
    ),
    "code_review_chain": PromptChain(
        name="code_review_chain",
        description="Multi-step code review",
        steps=[
            ChainStep(
                name="analyze",
                prompt_template="Analyze this code for potential issues:\n```\n{code}\n```",
                output_key="analysis"
            ),
            ChainStep(
                name="suggest",
                prompt_template="Based on this analysis:\n{analysis}\n\nSuggest specific improvements.",
                output_key="suggestions"
            ),
            ChainStep(
                name="refactor",
                prompt_template="Refactor the original code applying these suggestions:\n{suggestions}\n\nOriginal code:\n```\n{code}\n```",
                output_key="refactored"
            )
        ]
    )
}
