"""
Testing feature - common types.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TestCase:
    name: str
    input_vars: dict[str, str]
    expected_contains: list[str] = field(default_factory=list)
    expected_not_contains: list[str] = field(default_factory=list)
    expected_format: Optional[str] = None
    min_length: int = 0
    max_length: int = 0


@dataclass
class TestResult:
    test_case: TestCase
    provider: str
    model: str
    response: str
    passed: bool
    score: float
    checks: dict[str, bool]
    latency_ms: int
    tokens_used: int
    error: Optional[str] = None
