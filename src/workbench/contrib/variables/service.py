"""
Variable Interpolation System - Dynamic placeholders for reusable prompts.
Feature #4: Variable Interpolation System
"""

import re
from dataclasses import dataclass, field
from typing import Any, Optional
import json

from src.platform.environment import get_config_dir


@dataclass
class Variable:
    name: str
    description: str = ""
    default: Optional[str] = None
    required: bool = True
    var_type: str = "string"  # string, number, list, json
    validation: Optional[str] = None  # regex pattern


@dataclass
class VariableTemplate:
    name: str
    template: str
    variables: list[Variable]
    description: str = ""
    tags: list[str] = field(default_factory=list)


class VariableInterpolator:
    """Handle variable interpolation in prompt templates."""

    # Pattern for {{variable}} or {{variable:default}}
    VAR_PATTERN = re.compile(r'\{\{(\w+)(?::([^}]*))?\}\}')

    def __init__(self):
        self.templates: dict[str, VariableTemplate] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load saved templates from config."""
        config_path = get_config_dir() / "variable_templates.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    data = json.load(f)
                for name, tpl in data.items():
                    variables = [Variable(**v) for v in tpl.get("variables", [])]
                    self.templates[name] = VariableTemplate(
                        name=name,
                        template=tpl["template"],
                        variables=variables,
                        description=tpl.get("description", ""),
                        tags=tpl.get("tags", [])
                    )
            except Exception:
                pass

    def save_templates(self):
        """Save templates to config."""
        config_path = get_config_dir() / "variable_templates.json"
        
        data = {}
        for name, tpl in self.templates.items():
            data[name] = {
                "template": tpl.template,
                "variables": [
                    {
                        "name": v.name,
                        "description": v.description,
                        "default": v.default,
                        "required": v.required,
                        "var_type": v.var_type,
                        "validation": v.validation
                    }
                    for v in tpl.variables
                ],
                "description": tpl.description,
                "tags": tpl.tags
            }
        
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)

    def extract_variables(self, template: str) -> list[Variable]:
        """Extract variable definitions from a template string."""
        variables = []
        seen = set()
        
        for match in self.VAR_PATTERN.finditer(template):
            name = match.group(1)
            default = match.group(2)
            
            if name not in seen:
                seen.add(name)
                variables.append(Variable(
                    name=name,
                    default=default,
                    required=default is None
                ))
        
        return variables

    def interpolate(
        self,
        template: str,
        variables: dict[str, Any],
        strict: bool = False
    ) -> str:
        """
        Interpolate variables into a template.
        
        Args:
            template: Template string with {{variable}} placeholders
            variables: Dict of variable name -> value
            strict: If True, raise error for missing required variables
        
        Returns:
            Interpolated string
        """
        def replace_var(match):
            name = match.group(1)
            default = match.group(2)
            
            if name in variables:
                value = variables[name]
                # Handle different types
                if isinstance(value, list):
                    return "\n".join(str(v) for v in value)
                elif isinstance(value, dict):
                    return json.dumps(value, indent=2)
                return str(value)
            elif default is not None:
                return default
            elif strict:
                raise ValueError(f"Missing required variable: {name}")
            else:
                return match.group(0)  # Keep original placeholder
        
        return self.VAR_PATTERN.sub(replace_var, template)

    def validate_variables(
        self,
        template: VariableTemplate,
        values: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """Validate variable values against template definitions."""
        errors = []
        
        for var in template.variables:
            if var.required and var.name not in values:
                errors.append(f"Missing required variable: {var.name}")
                continue
            
            if var.name in values:
                value = values[var.name]
                
                # Type validation
                if var.var_type == "number":
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        errors.append(f"{var.name} must be a number")
                
                elif var.var_type == "list":
                    if not isinstance(value, list):
                        errors.append(f"{var.name} must be a list")
                
                elif var.var_type == "json":
                    if isinstance(value, str):
                        try:
                            json.loads(value)
                        except json.JSONDecodeError:
                            errors.append(f"{var.name} must be valid JSON")
                
                # Regex validation
                if var.validation and isinstance(value, str):
                    if not re.match(var.validation, value):
                        errors.append(f"{var.name} does not match pattern: {var.validation}")
        
        return len(errors) == 0, errors

    def create_template(
        self,
        name: str,
        template: str,
        description: str = "",
        tags: list[str] = None
    ) -> VariableTemplate:
        """Create a new variable template."""
        variables = self.extract_variables(template)
        
        tpl = VariableTemplate(
            name=name,
            template=template,
            variables=variables,
            description=description,
            tags=tags or []
        )
        
        self.templates[name] = tpl
        self.save_templates()
        
        return tpl

    def get_template(self, name: str) -> Optional[VariableTemplate]:
        """Get a template by name."""
        return self.templates.get(name)

    def list_templates(self) -> list[VariableTemplate]:
        """List all saved templates."""
        return list(self.templates.values())

    def delete_template(self, name: str) -> bool:
        """Delete a template."""
        if name in self.templates:
            del self.templates[name]
            self.save_templates()
            return True
        return False

    def batch_interpolate(
        self,
        template: str,
        variable_sets: list[dict[str, Any]]
    ) -> list[str]:
        """Interpolate template with multiple variable sets for batch processing."""
        return [self.interpolate(template, vars) for vars in variable_sets]
