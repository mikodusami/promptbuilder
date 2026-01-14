"""
Templates feature - common types.
"""

from dataclasses import dataclass

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class CustomTemplate:
    name: str
    description: str
    icon: str
    color: str
    template: str
    variables: list[str]
