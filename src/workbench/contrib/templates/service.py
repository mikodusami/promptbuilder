"""
Templates feature - service for managing custom templates.
"""

from typing import Optional
from pathlib import Path

from ...platform.environment import get_config_dir
from .common import CustomTemplate

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


DEFAULT_TEMPLATES = """
templates:
  code_review:
    name: "Code Review"
    description: "Thorough code review with best practices"
    icon: "🔍"
    color: "cyan"
    template: |
      You are a senior software engineer conducting a code review.
      
      Review the following code for:
      1. Code quality and readability
      2. Potential bugs or edge cases
      3. Performance considerations
      4. Security vulnerabilities
      
      Code to review:
      {task}
    variables:
      - task

  debug_helper:
    name: "Debug Helper"
    description: "Systematic debugging assistance"
    icon: "🐛"
    color: "red"
    template: |
      Help me debug this issue systematically.
      
      Problem: {task}
      Context: {context}
      
      Please:
      1. Identify potential root causes
      2. Suggest diagnostic steps
      3. Propose solutions
    variables:
      - task
      - context
"""


class TemplateService:
    """Manage custom prompt templates."""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = str(get_config_dir() / "templates.yaml")
        self.config_path = config_path
        self._ensure_config_exists()
        self.templates = self._load_templates()

    def _ensure_config_exists(self) -> None:
        if not Path(self.config_path).exists():
            with open(self.config_path, 'w') as f:
                f.write(DEFAULT_TEMPLATES)

    def _load_templates(self) -> dict[str, CustomTemplate]:
        if not YAML_AVAILABLE:
            return {}
        
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            templates = {}
            for key, config in data.get('templates', {}).items():
                templates[key] = CustomTemplate(
                    name=config.get('name', key),
                    description=config.get('description', ''),
                    icon=config.get('icon', '📝'),
                    color=config.get('color', 'white'),
                    template=config.get('template', ''),
                    variables=config.get('variables', [])
                )
            return templates
        except Exception:
            return {}

    def list_templates(self) -> list[CustomTemplate]:
        return list(self.templates.values())

    def get_template(self, key: str) -> Optional[CustomTemplate]:
        return self.templates.get(key)

    def build_prompt(self, key: str, variables: dict[str, str]) -> str:
        template = self.templates.get(key)
        if not template:
            raise ValueError(f"Template '{key}' not found")
        
        prompt = template.template
        for var in template.variables:
            value = variables.get(var, '')
            prompt = prompt.replace(f"{{{var}}}", value)
        
        return prompt.strip()

    def get_config_path(self) -> str:
        return self.config_path
