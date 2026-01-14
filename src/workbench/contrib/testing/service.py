"""
Testing feature - service for testing prompts across models.
"""

import json
import asyncio
from datetime import datetime

from ...services.llm import LLMClient
from .common import TestCase, TestResult


class TestingService:
    """Test prompts against multiple LLMs."""

    def __init__(self, llm_client: LLMClient = None):
        self.client = llm_client or LLMClient()

    async def run_test(
        self,
        prompt_template: str,
        test_case: TestCase,
        provider: str,
        model: str
    ) -> TestResult:
        """Run a single test case against a specific model."""
        
        prompt = prompt_template
        for key, value in test_case.input_vars.items():
            prompt = prompt.replace(f"{{{key}}}", value)

        start_time = datetime.now()
        response = await self.client.complete(prompt=prompt, provider=provider, model=model, temperature=0.3)
        latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        if response.error:
            return TestResult(
                test_case=test_case, provider=provider, model=model,
                response="", passed=False, score=0, checks={},
                latency_ms=latency_ms, tokens_used=0, error=response.error
            )

        checks = {}
        content = response.content

        for expected in test_case.expected_contains:
            checks[f"contains:{expected[:20]}"] = expected.lower() in content.lower()

        for not_expected in test_case.expected_not_contains:
            checks[f"not_contains:{not_expected[:20]}"] = not_expected.lower() not in content.lower()

        if test_case.expected_format == "json":
            try:
                json.loads(content)
                checks["format:json"] = True
            except:
                checks["format:json"] = False

        if checks:
            score = (sum(1 for v in checks.values() if v) / len(checks)) * 100
        else:
            score = 100 if content else 0

        passed = all(checks.values()) if checks else bool(content)

        return TestResult(
            test_case=test_case, provider=provider, model=model,
            response=content, passed=passed, score=score, checks=checks,
            latency_ms=latency_ms, tokens_used=response.input_tokens + response.output_tokens
        )

    async def run_across_models(
        self,
        prompt: str,
        models: list[tuple[str, str]] = None
    ) -> list[TestResult]:
        """Run a prompt across multiple models."""
        if not models:
            models = self.client.config.get_available_models()[:3]
        
        test_case = TestCase(name="quick_test", input_vars={})
        tasks = [self.run_test(prompt, test_case, p, m) for p, m in models]
        return await asyncio.gather(*tasks)
