"""
Prompt Testing Suite - Test prompts against multiple LLMs and score results.
Feature #3: Prompt Testing Suite
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import asyncio
import json

from llm_client import LLMClient, LLMResponse


@dataclass
class TestCase:
    name: str
    input_vars: dict[str, str]
    expected_contains: list[str] = field(default_factory=list)
    expected_not_contains: list[str] = field(default_factory=list)
    expected_format: Optional[str] = None  # "json", "markdown", "code"
    min_length: int = 0
    max_length: int = 0


@dataclass
class TestResult:
    test_case: TestCase
    provider: str
    model: str
    response: str
    passed: bool
    score: float  # 0-100
    checks: dict[str, bool]
    latency_ms: int
    tokens_used: int
    error: Optional[str] = None


@dataclass
class TestSuiteResult:
    prompt_template: str
    results: list[TestResult]
    total_tests: int
    passed_tests: int
    average_score: float
    best_model: Optional[str]
    timestamp: str


class PromptTestSuite:
    """Test prompts against multiple LLMs with defined test cases."""

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
        
        # Fill in template variables
        prompt = prompt_template
        for key, value in test_case.input_vars.items():
            prompt = prompt.replace(f"{{{key}}}", value)
            prompt = prompt.replace(f"{{{{{key}}}}}", value)

        start_time = datetime.now()
        
        response = await self.client.complete(
            prompt=prompt,
            provider=provider,
            model=model,
            temperature=0.3
        )

        latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        if response.error:
            return TestResult(
                test_case=test_case,
                provider=provider,
                model=model,
                response="",
                passed=False,
                score=0,
                checks={},
                latency_ms=latency_ms,
                tokens_used=0,
                error=response.error
            )

        # Run checks
        checks = {}
        content = response.content

        # Check expected contains
        for expected in test_case.expected_contains:
            checks[f"contains:{expected[:20]}"] = expected.lower() in content.lower()

        # Check expected not contains
        for not_expected in test_case.expected_not_contains:
            checks[f"not_contains:{not_expected[:20]}"] = not_expected.lower() not in content.lower()

        # Check format
        if test_case.expected_format:
            if test_case.expected_format == "json":
                try:
                    json.loads(content)
                    checks["format:json"] = True
                except:
                    # Try to find JSON in response
                    try:
                        if "```json" in content:
                            json_str = content.split("```json")[1].split("```")[0]
                            json.loads(json_str)
                            checks["format:json"] = True
                        else:
                            checks["format:json"] = False
                    except:
                        checks["format:json"] = False
            elif test_case.expected_format == "markdown":
                checks["format:markdown"] = any(m in content for m in ["#", "**", "- ", "```"])
            elif test_case.expected_format == "code":
                checks["format:code"] = "```" in content or "def " in content or "function " in content

        # Check length
        if test_case.min_length > 0:
            checks["min_length"] = len(content) >= test_case.min_length
        if test_case.max_length > 0:
            checks["max_length"] = len(content) <= test_case.max_length

        # Calculate score
        if checks:
            score = (sum(1 for v in checks.values() if v) / len(checks)) * 100
        else:
            score = 100 if content else 0

        passed = all(checks.values()) if checks else bool(content)

        return TestResult(
            test_case=test_case,
            provider=provider,
            model=model,
            response=content,
            passed=passed,
            score=score,
            checks=checks,
            latency_ms=latency_ms,
            tokens_used=response.input_tokens + response.output_tokens
        )

    async def run_suite(
        self,
        prompt_template: str,
        test_cases: list[TestCase],
        models: list[tuple[str, str]] = None  # [(provider, model), ...]
    ) -> TestSuiteResult:
        """Run all test cases against specified models."""
        
        if not models:
            models = self.client.config.get_available_models()
            if not models:
                return TestSuiteResult(
                    prompt_template=prompt_template,
                    results=[],
                    total_tests=0,
                    passed_tests=0,
                    average_score=0,
                    best_model=None,
                    timestamp=datetime.now().isoformat()
                )

        # Run all tests concurrently
        tasks = []
        for test_case in test_cases:
            for provider, model in models:
                tasks.append(self.run_test(prompt_template, test_case, provider, model))

        results = await asyncio.gather(*tasks)

        # Calculate summary
        passed_tests = sum(1 for r in results if r.passed)
        average_score = sum(r.score for r in results) / len(results) if results else 0

        # Find best model
        model_scores = {}
        for r in results:
            key = f"{r.provider}:{r.model}"
            if key not in model_scores:
                model_scores[key] = []
            model_scores[key].append(r.score)

        best_model = None
        best_avg = 0
        for model, scores in model_scores.items():
            avg = sum(scores) / len(scores)
            if avg > best_avg:
                best_avg = avg
                best_model = model

        return TestSuiteResult(
            prompt_template=prompt_template,
            results=results,
            total_tests=len(results),
            passed_tests=passed_tests,
            average_score=average_score,
            best_model=best_model,
            timestamp=datetime.now().isoformat()
        )

    async def ab_test(
        self,
        prompt_a: str,
        prompt_b: str,
        test_input: str,
        provider: str = None,
        model: str = None,
        runs: int = 3
    ) -> dict:
        """A/B test two prompts."""
        
        results_a = []
        results_b = []

        for _ in range(runs):
            resp_a = await self.client.complete(prompt_a.replace("{input}", test_input), provider, model)
            resp_b = await self.client.complete(prompt_b.replace("{input}", test_input), provider, model)
            results_a.append(resp_a)
            results_b.append(resp_b)

        return {
            "prompt_a": {
                "prompt": prompt_a,
                "responses": [r.content for r in results_a],
                "avg_tokens": sum(r.output_tokens for r in results_a) / runs
            },
            "prompt_b": {
                "prompt": prompt_b,
                "responses": [r.content for r in results_b],
                "avg_tokens": sum(r.output_tokens for r in results_b) / runs
            }
        }
